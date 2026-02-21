/**
 * MoodGlobe – animated orb that reacts to conversation state and mood.
 *
 * States: idle | listening | thinking | speaking
 * Mood colors derived from backend wellbeing metadata (stress / anxiety / depression).
 */
import { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export type GlobeState = "idle" | "listening" | "thinking" | "speaking";

export interface MoodMeta {
    stress?: string;   // low | moderate | high
    anxiety?: string;  // none | mild | moderate | severe
    depression?: string; // none | mild | moderate | moderately_severe | severe
}

/** Derive a gradient palette from mood metadata. */
function moodToColors(mood: MoodMeta): { from: string; via: string; to: string; glow: string } {
    const s = mood.stress ?? "low";
    const a = mood.anxiety ?? "none";
    const d = mood.depression ?? "none";

    // Severe / high → rose-red
    if (s === "high" || a === "severe" || d === "severe" || d === "moderately_severe") {
        return { from: "#f43f5e", via: "#e11d48", to: "#9f1239", glow: "rgba(244,63,94,0.35)" };
    }
    // Moderate → warm amber-gold
    if (s === "moderate" || a === "moderate" || d === "moderate") {
        return { from: "#f59e0b", via: "#d97706", to: "#b45309", glow: "rgba(245,158,11,0.35)" };
    }
    // Mild → soft lavender-blue
    if (a === "mild" || d === "mild") {
        return { from: "#818cf8", via: "#6366f1", to: "#4f46e5", glow: "rgba(129,140,248,0.3)" };
    }
    // Default calm → teal-green
    return { from: "#2dd4bf", via: "#14b8a6", to: "#0d9488", glow: "rgba(45,212,191,0.3)" };
}

/** Framer-motion variants for each state. */
const orbVariants = {
    idle: {
        scale: [1, 1.04, 1],
        transition: { repeat: Infinity, duration: 4, ease: "easeInOut" },
    },
    listening: {
        scale: [1, 1.08, 1, 1.06, 1],
        transition: { repeat: Infinity, duration: 1.2, ease: "easeInOut" },
    },
    thinking: {
        scale: [1, 1.05, 1],
        rotate: [0, 3, -3, 0],
        transition: { repeat: Infinity, duration: 2, ease: "easeInOut" },
    },
    speaking: {
        scale: [1, 1.06, 1.02, 1.07, 1],
        transition: { repeat: Infinity, duration: 1.6, ease: "easeInOut" },
    },
};

interface MoodGlobeProps {
    state: GlobeState;
    mood: MoodMeta;
    onClick?: () => void;
    size?: number; // px, default 220
    className?: string;
}

export function MoodGlobe({ state, mood, onClick, size = 220, className }: MoodGlobeProps) {
    const colors = useMemo(() => moodToColors(mood), [mood]);
    const half = size / 2;

    return (
        <div
            className={cn("relative flex items-center justify-center select-none", className)}
            style={{ width: size, height: size }}
        >
            {/* Outer glow ring – expands on speaking / listening */}
            <AnimatePresence>
                {(state === "speaking" || state === "listening") && (
                    <motion.div
                        key="ring"
                        className="absolute inset-0 rounded-full pointer-events-none"
                        style={{
                            background: `radial-gradient(circle, ${colors.glow} 0%, transparent 70%)`,
                        }}
                        initial={{ scale: 1, opacity: 0 }}
                        animate={{
                            scale: [1, 1.45, 1.2],
                            opacity: [0.6, 0.15, 0.6],
                        }}
                        exit={{ opacity: 0, scale: 1 }}
                        transition={{ repeat: Infinity, duration: state === "listening" ? 1.2 : 2, ease: "easeInOut" }}
                    />
                )}
            </AnimatePresence>

            {/* Thinking shimmer ring */}
            <AnimatePresence>
                {state === "thinking" && (
                    <motion.div
                        key="shimmer"
                        className="absolute rounded-full pointer-events-none"
                        style={{
                            width: size + 24,
                            height: size + 24,
                            border: `2px solid`,
                            borderColor: colors.from,
                            borderTopColor: "transparent",
                            borderRightColor: "transparent",
                        }}
                        initial={{ rotate: 0, opacity: 0 }}
                        animate={{ rotate: 360, opacity: 0.7 }}
                        exit={{ opacity: 0 }}
                        transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                    />
                )}
            </AnimatePresence>

            {/* Main orb */}
            <motion.button
                type="button"
                onClick={onClick}
                className="relative rounded-full cursor-pointer focus:outline-none active:scale-95 transition-[filter] duration-500"
                style={{
                    width: size,
                    height: size,
                    background: `radial-gradient(circle at 35% 30%, ${colors.from}, ${colors.via} 55%, ${colors.to} 100%)`,
                    boxShadow: `
            inset 0 -${half * 0.2}px ${half * 0.6}px rgba(0,0,0,0.25),
            inset 0 ${half * 0.15}px ${half * 0.35}px rgba(255,255,255,0.15),
            0 0 ${half * 0.8}px ${colors.glow},
            0 0 ${half * 0.3}px ${colors.glow}
          `,
                }}
                variants={orbVariants}
                animate={state}
                aria-label={state === "idle" ? "Tap to speak" : state}
            >
                {/* Glass highlight top-left */}
                <div
                    className="absolute rounded-full pointer-events-none"
                    style={{
                        top: "10%",
                        left: "15%",
                        width: "40%",
                        height: "35%",
                        background: "radial-gradient(ellipse at 40% 40%, rgba(255,255,255,0.35), transparent 70%)",
                    }}
                />
                {/* Subtle inner glow center */}
                <div
                    className="absolute rounded-full pointer-events-none"
                    style={{
                        top: "25%",
                        left: "25%",
                        width: "50%",
                        height: "50%",
                        background: `radial-gradient(circle, rgba(255,255,255,0.08), transparent 70%)`,
                    }}
                />
            </motion.button>

            {/* State label below */}
            <motion.span
                className="absolute -bottom-8 left-1/2 -translate-x-1/2 text-xs font-medium tracking-wider uppercase whitespace-nowrap"
                style={{ color: colors.from }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.8 }}
                key={state}
            >
                {state === "idle" ? "Tap to speak" : state === "listening" ? "Listening…" : state === "thinking" ? "Thinking…" : "Speaking…"}
            </motion.span>
        </div>
    );
}
