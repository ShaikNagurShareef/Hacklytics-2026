import { useState, useRef, useEffect, useCallback } from "react";
import { Mic, Zap, Loader2, Bot, Volume2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { postVoiceIntent, VoiceIntentResult } from "../api/client";
import { motion, AnimatePresence } from "framer-motion";

// ─── Helpers ────────────────────────────────────────────────────────
function determineAgentRoute(transcript: string): string | null {
    const q = transcript.toLowerCase();
    if (q.includes("diet") || q.includes("meal") || q.includes("food") || q.includes("nutrition")) return "/dietary";
    if (q.includes("wellbeing") || q.includes("stress") || q.includes("anxiety") || q.includes("therapist")) return "/wellbeing";
    if (q.includes("doctor") || q.includes("symptoms") || q.includes("headache") || q.includes("pain")) return "/virtual-doctor";
    if (q.includes("diagnostic") || q.includes("xray") || q.includes("report")) return "/diagnostic";
    // fallback or global agent
    return "/ask";
}

function agentColor(agentName?: string): string {
    if (!agentName) return "#14b8a6";
    const n = agentName.toLowerCase();
    if (n.includes("dietary")) return "#f59e0b";
    if (n.includes("wellbeing")) return "#ec4899";
    if (n.includes("doctor")) return "#3b82f6";
    if (n.includes("diagnostic")) return "#8b5cf6";
    return "#14b8a6"; // teal default
}

// ─── Types ──────────────────────────────────────────────────────────

type Phase = "idle" | "listening" | "processing" | "speaking" | "done";

interface ActionToast {
    text: string;
    icon: "navigate" | "query" | "theme" | "greet" | "action";
    color: string;
}

// ─── Component ──────────────────────────────────────────────────────

export function VoiceCommandBar() {
    const navigate = useNavigate();

    const [phaseState, setPhaseState] = useState<Phase>("idle");
    const phaseRef = useRef<Phase>("idle");
    const setPhase = useCallback((p: Phase) => {
        phaseRef.current = p;
        setPhaseState(p);
    }, []);
    const phase = phaseState;

    const [transcript, setTranscript] = useState("");
    const [toast, setToast] = useState<ActionToast | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [expanded, setExpanded] = useState(false);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recRef = useRef<any>(null);
    const transcriptRef = useRef("");
    const busyRef = useRef(false);
    const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const processTranscriptRef = useRef<(text: string) => void>();

    // ─── Show toast with auto-dismiss ──────────────────────────────
    const showToast = useCallback((t: ActionToast) => {
        setToast(t);
        if (toastTimer.current) clearTimeout(toastTimer.current);
        toastTimer.current = setTimeout(() => setToast(null), 4000);
    }, []);

    // ─── Action executor ──────────────────────────────────────────
    const executeAction = useCallback(
        (result: VoiceIntentResult) => {
            switch (result.action) {
                case "navigate":
                    if (result.target) {
                        showToast({
                            text: result.speech || `Navigating to ${result.target}`,
                            icon: "navigate",
                            color: "#14b8a6",
                        });
                        navigate(result.target);
                    }
                    break;

                case "send_query":
                    showToast({
                        text: `${result.agent_name || "Agent"} is responding…`,
                        icon: "query",
                        color: agentColor(result.agent_name),
                    });
                    // Navigate to the agent's page if specified
                    if (result.navigate_to) {
                        navigate(result.navigate_to);
                    }
                    else if (result.agent_name && result.agent_name !== "orchestrator") {
                        navigate(determineAgentRoute(transcriptRef.current) || "/ask");
                    } else {
                        navigate("/ask");
                    }
                    break;

                case "toggle_theme": {
                    const html = document.documentElement;
                    const isDark = html.classList.contains("dark");
                    html.classList.toggle("dark", !isDark);
                    localStorage.setItem("medora-theme", isDark ? "light" : "dark");
                    showToast({
                        text: result.speech || (isDark ? "Switched to light mode" : "Switched to dark mode"),
                        icon: "theme",
                        color: "#f59e0b",
                    });
                    break;
                }

                case "greeting":
                    showToast({
                        text: result.speech || "Hello!",
                        icon: "greet",
                        color: "#14b8a6",
                    });
                    break;

                case "logout":
                    showToast({
                        text: result.speech || "Signing you out",
                        icon: "action",
                        color: "#ef4444",
                    });
                    // Trigger logout via localStorage event (AuthContext listens for this)
                    localStorage.removeItem("medora_token");
                    window.location.href = "/login";
                    break;

                case "new_chat":
                    showToast({
                        text: result.speech || "Starting a new chat",
                        icon: "action",
                        color: "#14b8a6",
                    });
                    // Navigate to /ask to start fresh
                    navigate("/ask");
                    // Force page reload to clear session
                    window.location.reload();
                    break;
            }
        },
        [navigate, showToast]
    );

    // ─── Process transcript → classify → execute ──────────────────
    const processTranscript = useCallback(
        async (text: string) => {
            busyRef.current = true;
            setPhase("processing");
            setError(null);

            try {
                const result = await postVoiceIntent(text);

                // Execute the action
                executeAction(result);

                // Speak the response or confirmation
                const textToSpeak = result.response || result.speech;
                if (textToSpeak) {
                    setPhase("speaking");
                    speakText(textToSpeak, () => {
                        setPhase("done");
                        setTimeout(() => {
                            setPhase("idle");
                            setExpanded(false);
                            busyRef.current = false;
                        }, 1500);
                    });
                } else {
                    setPhase("done");
                    setTimeout(() => {
                        setPhase("idle");
                        setExpanded(false);
                        busyRef.current = false;
                    }, 1500);
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : "Something went wrong");
                setPhase("idle");
                setExpanded(false);
                busyRef.current = false;
            }
        },
        [executeAction, setPhase]
    );

    useEffect(() => {
        processTranscriptRef.current = processTranscript;
    }, [processTranscript]);

    // ─── Stop speech synthesis ────────────────────────────────────
    const stopAllSpeech = () => {
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
    };

    // ─── Text-to-Speech (Fallback implementation) ─────────────────
    const speakText = (text: string, onEnd?: () => void) => {
        if (!window.speechSynthesis) {
            if (onEnd) onEnd();
            return;
        }

        stopAllSpeech();
        const utterance = new SpeechSynthesisUtterance(text);

        // Find a good voice
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(
            (v) =>
                v.lang.startsWith("en") &&
                (v.name.includes("Female") || v.name.includes("Samantha") || v.name.includes("Google US English"))
        );
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }

        utterance.rate = 1.05;
        utterance.pitch = 1.05;

        utterance.onend = () => {
            if (onEnd) onEnd();
        };
        utterance.onerror = () => {
            if (onEnd) onEnd();
        };

        window.speechSynthesis.speak(utterance);
    };

    // ─── Start listening ──────────────────────────────────────────
    const startListening = useCallback(() => {
        if (busyRef.current) return;
        stopAllSpeech();
        setError(null);
        setTranscript("");
        transcriptRef.current = "";
        setExpanded(true);

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const Ctor = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
        if (!Ctor) {
            setError("Speech not supported in this browser");
            return;
        }

        try {
            // Unlock speechSynthesis on iOS/Safari
            if (window.speechSynthesis) {
                const s = new SpeechSynthesisUtterance("");
                s.volume = 0;
                window.speechSynthesis.speak(s);
            }

            // Cleanup old instance if it exists
            if (recRef.current) {
                try { recRef.current.abort(); } catch { /* ignore */ }
            }

            // Create a fresh instance for every listen attempt
            const rec = new Ctor();
            rec.continuous = false;
            rec.interimResults = true;
            rec.lang = "en-US";

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            rec.onresult = (e: any) => {
                let final = "";
                let interim = "";
                for (let i = 0; i < e.results.length; i++) {
                    const result = e.results[i];
                    if (result.isFinal) final += result[0].transcript;
                    else interim += result[0].transcript;
                }
                const full = (final + interim).trim();
                transcriptRef.current = full;
                setTranscript(full);
            };

            rec.onend = () => {
                const q = transcriptRef.current.trim();
                if (q && !busyRef.current) {
                    if (phaseRef.current === "listening") {
                        processTranscriptRef.current?.(q);
                    }
                } else if (!busyRef.current && phaseRef.current === "listening") {
                    setPhase("idle");
                    setExpanded(false);
                    setError("I didn't catch that. Try again.");
                }
            };

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            rec.onerror = (e: any) => {
                if (e.error !== "aborted" && e.error !== "no-speech") {
                    setError(`Mic error: ${e.error}`);
                    setPhase("idle");
                    setExpanded(false);
                }
            };

            recRef.current = rec;
            rec.start();
            setPhase("listening");
        } catch {
            setError("Could not start microphone");
        }
    }, [setPhase]);

    // ─── Stop listening ───────────────────────────────────────────
    const stopListening = useCallback(() => {
        const rec = recRef.current;
        if (rec) try { rec.stop(); } catch { /* ignore */ }
    }, []);

    // ─── Handle orb click ─────────────────────────────────────────
    const handleClick = useCallback(() => {
        if (phaseRef.current === "idle") {
            startListening();
        } else if (phaseRef.current === "listening") {
            stopListening();
        } else if (phaseRef.current === "speaking") {
            stopAllSpeech();
            setPhase("idle");
            setExpanded(false);
            busyRef.current = false;
        }
    }, [startListening, stopListening, setPhase]);

    // ─── Handle close ─────────────────────────────────────────────
    const handleClose = useCallback(() => {
        const rec = recRef.current;
        if (rec) try { rec.abort(); } catch { /* ignore */ }
        stopAllSpeech();
        setPhase("idle");
        setExpanded(false);
        setTranscript("");
        setError(null);
        busyRef.current = false;
    }, [setPhase]);

    // ─── Orb color based on phase ─────────────────────────────────
    const orbGradient =
        phase === "listening"
            ? "from-teal-500 to-emerald-500"
            : phase === "processing"
                ? "from-amber-500 to-orange-500"
                : phase === "speaking"
                    ? "from-blue-500 to-indigo-500"
                    : phase === "done"
                        ? "from-green-500 to-emerald-500"
                        : "from-teal-600 to-cyan-600";

    return (
        <>
            {/* Toast notification */}
            <AnimatePresence>
                {toast && (
                    <motion.div
                        initial={{ opacity: 0, y: 20, x: 20 }}
                        animate={{ opacity: 1, y: 0, x: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        className="fixed bottom-28 right-6 z-[60] max-w-xs"
                    >
                        <div
                            className="flex items-center gap-3 rounded-2xl px-4 py-3 shadow-xl border backdrop-blur-xl"
                            style={{
                                background: `linear-gradient(135deg, ${toast.color}15, ${toast.color}08)`,
                                borderColor: `${toast.color}30`,
                            }}
                        >
                            <div
                                className="h-8 w-8 rounded-full flex items-center justify-center shrink-0"
                                style={{ background: `${toast.color}20` }}
                            >
                                <Zap className="h-4 w-4" style={{ color: toast.color }} />
                            </div>
                            <p className="text-sm font-medium text-[var(--foreground)]">{toast.text}</p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Main voice orb */}
            <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
                {/* Expanded panel */}
                <AnimatePresence>
                    {expanded && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 20, transformOrigin: "bottom right" }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 20 }}
                            className="bg-background border border-[var(--border)] shadow-2xl rounded-2xl w-72 overflow-hidden flex flex-col"
                        >
                            <div className="p-4 flex flex-col gap-3">
                                {/* Header / Status */}
                                <div className="flex items-center gap-2">
                                    {phase === "listening" && <span className="relative flex h-3 w-3"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span><span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span></span>}
                                    {phase === "processing" && <Loader2 className="h-4 w-4 animate-spin text-amber-500" />}
                                    {phase === "speaking" && <Volume2 className="h-4 w-4 text-blue-500 animate-pulse" />}

                                    <span className="text-sm font-semibold capitalize text-[var(--foreground)]">
                                        {phase === "idle" ? "Voice Assistant" : phase}
                                    </span>

                                    <button onClick={handleClose} className="ml-auto text-xs opacity-50 hover:opacity-100 transition-opacity">
                                        Close
                                    </button>
                                </div>

                                {/* Transcript area */}
                                <div className="min-h-[60px] max-h-[120px] overflow-y-auto w-full break-words">
                                    {error ? (
                                        <p className="text-sm text-red-500">{error}</p>
                                    ) : transcript ? (
                                        <p className="text-sm text-[var(--foreground)] leading-relaxed italic">
                                            "{transcript}"
                                        </p>
                                    ) : (
                                        <p className="text-sm text-gray-500 italic">
                                            {phase === "listening" ? "Listening..." : "Tap the orb to start"}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Orb Button */}
                <motion.button
                    onClick={handleClick}
                    className={`relative w-16 h-16 rounded-full flex items-center justify-center text-white shadow-lg focus:outline-none focus:ring-4 focus:ring-teal-500/30 overflow-hidden group`}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    {/* Gradient background */}
                    <div className={`absolute inset-0 bg-gradient-to-tr ${orbGradient} transition-colors duration-500`} />

                    {/* Speaking animation waves */}
                    {phase === "speaking" && (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-full h-full border-2 border-white/50 rounded-full animate-ping opacity-75" style={{ animationDuration: '1.5s' }} />
                        </div>
                    )}

                    {/* Inside Icon */}
                    <div className="relative z-10">
                        {phase === "processing" ? (
                            <Loader2 className="w-8 h-8 animate-spin" strokeWidth={2.5} />
                        ) : phase === "listening" ? (
                            <Mic className="w-8 h-8 opacity-90 animate-pulse" strokeWidth={2.5} />
                        ) : phase === "speaking" ? (
                            <Volume2 className="w-8 h-8" strokeWidth={2.5} />
                        ) : (
                            <Bot className="w-8 h-8 opacity-90 transition-transform group-hover:-rotate-12" strokeWidth={2.5} />
                        )}
                    </div>
                </motion.button>
            </div>
        </>
    );
}
