/**
 * Text-to-speech via Web Speech API (speechSynthesis).
 * Queues utterances so sentence-by-sentence streaming works without interruption.
 * Browsers (e.g. Chrome M71+) require a user gesture before speak() works.
 * Call unlock() once from a click handler (e.g. when user sends a message).
 */
import { useCallback, useRef, useState } from "react";

export function useTextToSpeech(options?: { lang?: string; rate?: number }) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const queueRef = useRef<SpeechSynthesisUtterance[]>([]);
  const activeRef = useRef(false);

  const processQueue = useCallback(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    if (activeRef.current) return; // already playing one
    const next = queueRef.current.shift();
    if (!next) {
      setIsSpeaking(false);
      return;
    }
    activeRef.current = true;
    setIsSpeaking(true);
    next.onend = () => {
      activeRef.current = false;
      processQueue();
    };
    next.onerror = () => {
      activeRef.current = false;
      processQueue();
    };
    window.speechSynthesis.speak(next);
  }, []);

  const speak = useCallback(
    (text: string) => {
      const t = typeof text === "string" ? text.trim() : "";
      if (!t) return;
      if (typeof window === "undefined" || !window.speechSynthesis) return;
      const u = new SpeechSynthesisUtterance(t);
      u.lang = options?.lang ?? "en-US";
      u.rate = options?.rate ?? 1;
      queueRef.current.push(u);
      processQueue();
    },
    [options?.lang, options?.rate, processQueue]
  );

  /** Call from a user gesture (click) so async speak() works in Chrome. Speaks a silent utterance to unlock. */
  const unlock = useCallback(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    // Chrome requires an actual speak() call during a user gesture to unlock
    const silent = new SpeechSynthesisUtterance("");
    silent.volume = 0;
    window.speechSynthesis.speak(silent);
  }, []);

  const stop = useCallback(() => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      queueRef.current = [];
      activeRef.current = false;
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, []);

  const isSupported = typeof window !== "undefined" && !!window.speechSynthesis;

  return { speak, stop, unlock, isSpeaking, isSupported };
}

