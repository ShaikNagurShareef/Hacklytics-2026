import { motion } from "framer-motion";

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3 md:gap-4 pr-4"
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--hover)] mt-0.5 border border-[var(--border)] shadow-sm">
        <span className="text-[12px] font-semibold text-[var(--primary)]">M</span>
      </div>
      <div className="flex items-center gap-2 py-2">
        <span className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="h-2 w-2 rounded-full bg-[var(--muted-foreground)]"
              animate={{ y: [0, -4, 0] }}
              transition={{
                duration: 0.4,
                repeat: Infinity,
                delay: i * 0.15,
                ease: "easeInOut",
              }}
            />
          ))}
        </span>
        <span className="text-[13px] text-[var(--muted-foreground)]">MEDORA is thinking…</span>
      </div>
    </motion.div>
  );
}
