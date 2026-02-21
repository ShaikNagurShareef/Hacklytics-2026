/**
 * Speech-to-text via Web Speech API (SpeechRecognition).
 * Chrome, Edge, Safari (iOS 14.5+); not in Firefox.
 */
import { useCallback, useEffect, useRef, useState } from "react";

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionInstance;
    webkitSpeechRecognition?: new () => SpeechRecognitionInstance;
  }
}

interface SpeechRecognitionInstance extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((e: SpeechRecognitionEvent) => void) | null;
  onend: (() => void) | null;
  onerror: ((e: SpeechRecognitionErrorEvent) => void) | null;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message?: string;
}

export function useSpeechToText(options?: { lang?: string; onResult?: (transcript: string, isFinal: boolean) => void }) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [isSupported, setIsSupported] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const finalSoFarRef = useRef("");

  // Store callback in a ref so it doesn't cause the SpeechRecognition to be recreated on every render
  const onResultRef = useRef(options?.onResult);
  onResultRef.current = options?.onResult;

  const lang = options?.lang ?? "en-US";

  useEffect(() => {
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    setIsSupported(!!Recognition);
    if (!Recognition) return;
    const rec = new Recognition() as SpeechRecognitionInstance;
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = lang;
    rec.onresult = (e: SpeechRecognitionEvent) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const result = e.results[i];
        const t = result[0].transcript;
        if (result.isFinal) {
          finalSoFarRef.current += t;
          if (t.trim()) onResultRef.current?.(finalSoFarRef.current.trim(), true);
        } else {
          interim = t;
        }
      }
      setTranscript(finalSoFarRef.current + interim);
    };
    rec.onend = () => setIsListening(false);
    rec.onerror = (e: SpeechRecognitionErrorEvent) => {
      if (e.error !== "aborted") setError(e.error);
    };
    recognitionRef.current = rec;
    return () => {
      try { rec.abort(); } catch { /* ignore */ }
      recognitionRef.current = null;
    };
  }, [lang]);

  const startListening = useCallback(() => {
    setError(null);
    setTranscript("");
    finalSoFarRef.current = "";
    const rec = recognitionRef.current;
    if (!rec) return;
    try {
      rec.start();
      setIsListening(true);
    } catch {
      setError("Could not start microphone");
    }
  }, []);

  const stopListening = useCallback(() => {
    const rec = recognitionRef.current;
    if (rec) try { rec.stop(); } catch { /* ignore */ }
    setIsListening(false);
  }, []);

  const resetTranscript = useCallback(() => setTranscript(""), []);

  return {
    isListening,
    transcript,
    isSupported,
    error,
    startListening,
    stopListening,
    resetTranscript,
  };
}

