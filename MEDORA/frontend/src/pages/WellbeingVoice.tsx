/**
 * WellbeingVoice – full-screen speech-to-speech experience.
 * Simplified flow: tap mic → speak → tap mic → sends to API → speaks response.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Mic, Phone, MessageSquare, Square } from "lucide-react";
import { MoodGlobe, type GlobeState, type MoodMeta } from "@/components/wellbeing/MoodGlobe";
import { useChatSession } from "@/hooks/useChatSession";
import { postWellbeingChatStream } from "@/api/client";
import { cn } from "@/lib/utils";

// ─── Inline speech helpers (no hooks, direct control) ───────────────────────

function speakText(text: string, onEnd?: () => void): void {
    if (!window.speechSynthesis || !text.trim()) {
        onEnd?.();
        return;
    }
    let done = false;
    const finish = () => {
        if (done) return;
        done = true;
        clearInterval(watchdog);
        onEnd?.();
    };

    const u = new SpeechSynthesisUtterance(text.trim());
    u.lang = "en-US";
    u.rate = 0.95;
    u.onend = finish;
    u.onerror = finish;
    window.speechSynthesis.speak(u);

    // Watchdog: Chrome sometimes doesn't fire onend.
    // Poll speechSynthesis.speaking and also call resume() to avoid Chrome's 15s pause bug.
    const watchdog = setInterval(() => {
        window.speechSynthesis.resume();  // Chrome pauses after ~15s; this keeps it going
        if (!window.speechSynthesis.speaking) {
            finish();
        }
    }, 200);
}

function stopAllSpeech(): void {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
}

// ─── Voice Activity Detection (VAD) for barge-in ────────────────────────────
// Uses Web Audio API to detect when the user speaks while TTS is playing.
// When mic volume exceeds threshold, triggers a callback.
interface VADHandle {
    stop: () => void;
}

async function startVAD(
    onVoiceDetected: () => void,
    threshold = 0.015,   // RMS threshold — tune if needed
    debounceMs = 300,    // must sustain above threshold for this long
): Promise<VADHandle | null> {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const audioCtx = new AudioContext();
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 512;
        source.connect(analyser);

        const data = new Float32Array(analyser.fftSize);
        let aboveStart = 0;
        let stopped = false;

        const check = () => {
            if (stopped) return;
            analyser.getFloatTimeDomainData(data);
            // Compute RMS (volume level)
            let sum = 0;
            for (let i = 0; i < data.length; i++) sum += data[i] * data[i];
            const rms = Math.sqrt(sum / data.length);

            if (rms > threshold) {
                if (aboveStart === 0) aboveStart = Date.now();
                if (Date.now() - aboveStart > debounceMs) {
                    // Sustained voice detected — trigger barge-in
                    onVoiceDetected();
                    return; // stop polling
                }
            } else {
                aboveStart = 0;
            }
            requestAnimationFrame(check);
        };
        requestAnimationFrame(check);

        return {
            stop: () => {
                stopped = true;
                stream.getTracks().forEach(t => t.stop());
                audioCtx.close().catch(() => { });
            },
        };
    } catch {
        // Mic access denied or not available
        return null;
    }
}

// ─── Component ──────────────────────────────────────────────────────────────

export function WellbeingVoice() {
    const {
        sessionId,
        contextForApi,
        addUserMessage,
        addAssistantMessage,
        updateLastAssistantMessage,
    } = useChatSession();

    const [phase, setPhase] = useState<"idle" | "listening" | "thinking" | "speaking">("idle");
    const [mood, setMood] = useState<MoodMeta>({});
    const [liveTranscript, setLiveTranscript] = useState("");
    const [userText, setUserText] = useState("");
    const [assistantText, setAssistantText] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [micStatus, setMicStatus] = useState("Ready");  // visible debug status

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recRef = useRef<any>(null);
    const transcriptRef = useRef("");  // always-fresh transcript
    const busyRef = useRef(false);
    const phaseRef = useRef(phase);  // keep phase current for callbacks
    const vadRef = useRef<VADHandle | null>(null);
    const [textInput, setTextInput] = useState("");  // fallback text input

    // Keep phaseRef in sync
    useEffect(() => { phaseRef.current = phase; }, [phase]);

    // ─── VAD barge-in: monitor mic while speaking ────
    useEffect(() => {
        if (phase !== "speaking") {
            // Stop VAD when not speaking
            if (vadRef.current) {
                vadRef.current.stop();
                vadRef.current = null;
            }
            return;
        }
        // Start VAD when speaking
        let cancelled = false;
        startVAD(() => {
            if (cancelled) return;
            // Voice detected — barge-in!
            setMicStatus("Voice detected — interrupting!");
            stopAllSpeech();
            busyRef.current = false;
            setPhase("idle");
            // Start listening after a brief pause
            setTimeout(() => {
                if (!cancelled) {
                    const rec = recRef.current;
                    if (rec) {
                        try {
                            setMicStatus("Starting mic…");
                            transcriptRef.current = "";
                            setLiveTranscript("");
                            setError(null);
                            rec.start();
                            setPhase("listening");
                        } catch { /* ignore */ }
                    }
                }
            }, 150);
        }).then(handle => {
            if (cancelled) {
                handle?.stop();
            } else {
                vadRef.current = handle;
            }
        });
        return () => {
            cancelled = true;
            if (vadRef.current) {
                vadRef.current.stop();
                vadRef.current = null;
            }
        };
    }, [phase]);

    // sendQueryRef — we need access to sendQuery inside the rec callbacks,
    // but sendQuery is defined later. Use a ref to break the circular dep.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const sendQueryRef = useRef<(q: string) => void>(() => { });

    // Create SpeechRecognition once on mount — inline, no helper
    useEffect(() => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const Ctor = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
        if (!Ctor) {
            setMicStatus("Not supported in this browser");
            return;
        }
        const rec = new Ctor();
        rec.continuous = false;      // stop after one phrase
        rec.interimResults = true;   // get partial results as user speaks
        rec.lang = "en-US";

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        rec.onresult = (e: any) => {
            let final = "";
            let interim = "";
            for (let i = 0; i < e.results.length; i++) {
                const result = e.results[i];
                if (result.isFinal) {
                    final += result[0].transcript;
                } else {
                    interim += result[0].transcript;
                }
            }
            const full = (final + interim).trim();
            transcriptRef.current = full;
            setLiveTranscript(full);
            setMicStatus(`Got: "${full.slice(0, 40)}${full.length > 40 ? "…" : ""}"`);
        };

        rec.onaudiostart = () => setMicStatus("Mic active — speak now!");
        rec.onsoundstart = () => setMicStatus("Hearing sound…");
        rec.onspeechstart = () => setMicStatus("Detecting speech…");
        rec.onspeechend = () => setMicStatus("Speech ended, processing…");

        rec.onend = () => {
            if (phaseRef.current === "listening") {
                const q = transcriptRef.current.trim();
                if (q) {
                    setMicStatus("Sending…");
                    sendQueryRef.current(q);
                } else {
                    setMicStatus("No speech detected");
                    setPhase("idle");
                    setError("I didn't catch that. Try speaking louder or type below.");
                }
            }
        };

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        rec.onerror = (e: any) => {
            setMicStatus(`Error: ${e.error}`);
            if (e.error !== "aborted" && e.error !== "no-speech") {
                console.warn("SpeechRecognition error:", e.error);
                setError(`Mic error: ${e.error}. Try again or type below.`);
                setPhase("idle");
            }
        };

        recRef.current = rec;
        setMicStatus("Ready");

        return () => {
            try { rec.abort(); } catch { /* ignore */ }
            recRef.current = null;
        };
    }, []);

    // ─── Start listening ────
    const startListening = useCallback(() => {
        if (busyRef.current) return;
        stopAllSpeech();
        setError(null);
        setLiveTranscript("");
        setUserText("");
        setAssistantText("");
        transcriptRef.current = "";

        const rec = recRef.current;
        if (!rec) {
            setError("Speech recognition not supported. Use the text input below.");
            return;
        }
        try {
            setMicStatus("Starting mic…");
            rec.start();
            setPhase("listening");
        } catch (err) {
            setMicStatus(`Start failed: ${err}`);
            setError("Could not start microphone. Check browser permissions.");
        }
    }, []);

    // ─── Send a text query (fallback or from stopAndSend) ────
    const sendQuery = useCallback(async (query: string) => {
        if (!query.trim() || busyRef.current) return;
        busyRef.current = true;
        setUserText(query.trim());
        setLiveTranscript("");
        setAssistantText("");
        setError(null);
        setPhase("thinking");

        // Unlock speechSynthesis
        if (window.speechSynthesis) {
            const silent = new SpeechSynthesisUtterance("");
            silent.volume = 0;
            window.speechSynthesis.speak(silent);
        }

        addUserMessage(query.trim());
        addAssistantMessage("", "Personal Wellbeing Counsellor");

        let fullText = "";
        const sentencesToSpeak: string[] = [];
        let spokenLength = 0;
        const sentenceEnd = /^([^.!?]*[.!?]\s*)/;

        try {
            await postWellbeingChatStream(
                { session_id: sessionId, query: query.trim(), context: contextForApi },
                (event) => {
                    if (event.type === "meta" && event.metadata) {
                        const m = event.metadata as Record<string, string>;
                        setMood({ stress: m.stress, anxiety: m.anxiety, depression: m.depression });
                    } else if (event.type === "text" && event.content) {
                        fullText += event.content;
                        setAssistantText(fullText);
                        updateLastAssistantMessage(fullText);
                        let tail = fullText.slice(spokenLength);
                        let match: RegExpExecArray | null;
                        while ((match = sentenceEnd.exec(tail))) {
                            const sentence = match[1].trim();
                            if (sentence) sentencesToSpeak.push(sentence);
                            spokenLength += match[0].length;
                            tail = fullText.slice(spokenLength);
                        }
                    } else if (event.type === "done" && event.content) {
                        fullText = event.content;
                        setAssistantText(fullText);
                        updateLastAssistantMessage(fullText);
                        const remainder = fullText.slice(spokenLength).trim();
                        if (remainder) sentencesToSpeak.push(remainder);
                    }
                }
            );
        } catch (e) {
            setError(e instanceof Error ? e.message : "Something went wrong.");
            setPhase("idle");
            busyRef.current = false;
            return;
        }

        if (sentencesToSpeak.length === 0) {
            setPhase("idle");
            busyRef.current = false;
            return;
        }

        setPhase("speaking");
        let idx = 0;
        const speakNext = () => {
            if (idx >= sentencesToSpeak.length) {
                setPhase("idle");
                busyRef.current = false;
                return;
            }
            speakText(sentencesToSpeak[idx], () => {
                idx++;
                speakNext();
            });
        };
        speakNext();
    }, [sessionId, contextForApi, addUserMessage, addAssistantMessage, updateLastAssistantMessage]);

    // Keep sendQueryRef in sync so the rec.onend callback can call it
    useEffect(() => { sendQueryRef.current = sendQuery; }, [sendQuery]);

    // ─── Stop listening and send (manual tap) ────
    const stopAndSend = useCallback(() => {
        const rec = recRef.current;
        // Stopping the rec will trigger onend, which auto-sends if there's a transcript
        if (rec) try { rec.stop(); } catch { /* ignore */ }
    }, []);

    // ─── Toggle mic ────
    const handleMicToggle = useCallback(() => {
        if (phase === "listening") {
            stopAndSend();
        } else if (phase === "speaking") {
            // Barge-in: interrupt TTS and start listening
            stopAllSpeech();
            busyRef.current = false;
            setPhase("idle");
            // Small delay to let speech cancel, then start listening
            setTimeout(() => startListening(), 100);
        } else if (phase === "idle") {
            startListening();
        }
        // If thinking, ignore mic taps (waiting for API response)
    }, [phase, stopAndSend, startListening]);

    // ─── Send text fallback ────
    const handleTextSubmit = useCallback(() => {
        if (!textInput.trim() || busyRef.current) return;
        const q = textInput.trim();
        setTextInput("");
        sendQuery(q);
    }, [textInput, sendQuery]);

    // ─── End session ────
    const handleEndCall = useCallback(() => {
        const rec = recRef.current;
        if (rec) try { rec.abort(); } catch { /* ignore */ }
        stopAllSpeech();
        setPhase("idle");
        busyRef.current = false;
    }, []);

    // Map phase to GlobeState
    const globeState: GlobeState = phase;

    return (
        <div className="fixed inset-0 z-50 flex flex-col bg-[#0A0A0F] text-white overflow-hidden select-none">
            {/* Ambient background gradients */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
                <div
                    className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] rounded-full blur-[120px] opacity-20 transition-colors duration-1000"
                    style={{ background: `radial-gradient(circle, ${mood.stress === "high" ? "#f43f5e" : mood.anxiety === "moderate" ? "#f59e0b" : "#14b8a6"}, transparent)` }}
                />
                <div
                    className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] rounded-full blur-[120px] opacity-15 transition-colors duration-1000"
                    style={{ background: `radial-gradient(circle, ${mood.depression === "moderate" ? "#818cf8" : "#0d9488"}, transparent)` }}
                />
            </div>

            {/* Top bar */}
            <div className="relative z-10 flex items-center justify-between p-4 sm:p-6">
                <Link to="/wellbeing" className="flex items-center gap-2 text-sm text-white/60 hover:text-white transition-colors">
                    <ArrowLeft className="h-4 w-4" />
                    <span className="hidden sm:inline">Back to chat</span>
                </Link>
                <div className="text-center">
                    <p className="text-xs uppercase tracking-[0.2em] text-white/40 font-medium">Wellbeing Counsellor</p>
                    <p className="text-[11px] text-white/30 mt-0.5">Voice Mode</p>
                </div>
                <Link to="/wellbeing" className="flex items-center gap-1.5 text-sm text-white/60 hover:text-white transition-colors">
                    <MessageSquare className="h-4 w-4" />
                    <span className="hidden sm:inline">Text</span>
                </Link>
            </div>

            {/* Globe area */}
            <div className="relative z-10 flex-1 flex flex-col items-center justify-center gap-6 px-4">
                <MoodGlobe
                    state={globeState}
                    mood={mood}
                    onClick={handleMicToggle}
                    size={240}
                />

                {/* Transcript / reply area */}
                <div className="w-full max-w-md min-h-[120px] flex flex-col items-center justify-start gap-3 mt-6">
                    <AnimatePresence mode="popLayout">
                        {/* Live transcript while listening */}
                        {phase === "listening" && liveTranscript && (
                            <motion.p
                                key="transcript"
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0 }}
                                className="text-center text-lg font-light text-white/90 leading-relaxed"
                            >
                                {liveTranscript}
                            </motion.p>
                        )}

                        {/* Show what the user said while thinking */}
                        {phase === "thinking" && userText && (
                            <motion.p
                                key="user-sent"
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 0.5, y: 0 }}
                                exit={{ opacity: 0 }}
                                className="text-center text-sm text-white/40 italic"
                            >
                                "{userText}"
                            </motion.p>
                        )}

                        {/* Assistant reply while speaking or after */}
                        {assistantText && (phase === "speaking" || phase === "idle") && (
                            <motion.div
                                key="reply"
                                initial={{ opacity: 0, y: 12 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="text-center max-h-[200px] overflow-y-auto scrollbar-thin px-2"
                            >
                                <p className="text-base font-light text-white/80 leading-relaxed">{assistantText}</p>
                            </motion.div>
                        )}

                        {/* Error message */}
                        {error && (
                            <motion.p
                                key="error"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="text-sm text-red-400 text-center"
                            >
                                {error}
                            </motion.p>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            {/* Bottom controls */}
            <div className="relative z-10 flex flex-col items-center gap-4 pb-6 sm:pb-10 px-4">
                <div className="flex items-center justify-center gap-6">
                    {/* Mic button */}
                    <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={handleMicToggle}
                        disabled={phase === "thinking"}
                        className={cn(
                            "h-16 w-16 rounded-full flex items-center justify-center transition-all shadow-lg relative",
                            phase === "listening"
                                ? "bg-teal-500 text-white shadow-teal-500/30"
                                : phase === "thinking"
                                    ? "bg-white/5 text-white/30 cursor-not-allowed"
                                    : phase === "speaking"
                                        ? "bg-white/10 backdrop-blur-md border border-white/20 text-white hover:bg-white/20 animate-pulse"
                                        : "bg-white/10 backdrop-blur-md border border-white/20 text-white hover:bg-white/20"
                        )}
                        aria-label={phase === "listening" ? "Stop and send" : phase === "speaking" ? "Interrupt and speak" : "Start listening"}
                    >
                        {phase === "listening" ? (
                            <>
                                {/* Pulsing ring to show mic is ACTIVE */}
                                <span className="absolute inset-0 rounded-full bg-teal-500 animate-ping opacity-30" />
                                <Square className="h-5 w-5 fill-white" />
                            </>
                        ) : (
                            <Mic className="h-6 w-6" />
                        )}
                    </motion.button>

                    {/* End / hang up */}
                    <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={handleEndCall}
                        className="h-14 w-14 rounded-full bg-red-600/80 backdrop-blur-md text-white flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg shadow-red-600/20"
                        aria-label="End voice session"
                    >
                        <Phone className="h-5 w-5 rotate-[135deg]" />
                    </motion.button>
                </div>
                {/* Label + debug status below controls */}
                <p className="text-xs text-white/40 text-center">
                    {phase === "listening" ? "Listening… tap ■ to send" : phase === "idle" ? "Tap mic to speak" : ""}
                </p>
                <p className="text-[10px] text-white/25 text-center font-mono">
                    mic: {micStatus}
                </p>

                {/* Text input fallback */}
                <form
                    onSubmit={(e) => { e.preventDefault(); handleTextSubmit(); }}
                    className="w-full max-w-md flex items-center gap-2"
                >
                    <input
                        type="text"
                        value={textInput}
                        onChange={(e) => setTextInput(e.target.value)}
                        placeholder="Or type here…"
                        disabled={phase === "thinking" || phase === "speaking"}
                        className="flex-1 bg-white/10 backdrop-blur-md border border-white/20 rounded-full px-4 py-2.5 text-sm text-white placeholder:text-white/40 focus:outline-none focus:border-teal-400/50 transition-colors"
                    />
                    <button
                        type="submit"
                        disabled={!textInput.trim() || phase === "thinking" || phase === "speaking"}
                        className="h-10 w-10 rounded-full bg-teal-500 text-white flex items-center justify-center hover:bg-teal-400 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                    >
                        <ArrowLeft className="h-4 w-4 rotate-180" />
                    </button>
                </form>
            </div>
        </div>
    );
}
