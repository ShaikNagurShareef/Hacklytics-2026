import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { MessageCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const DEFAULT_HEADLINE = "How can I help with your health today?";

interface WelcomeStateProps {
  onSuggestion: (text: string) => void;
  headline?: string;
  tagline: string;
  icon?: LucideIcon;
  suggestions: string[];
}

export function WelcomeState({
  onSuggestion,
  headline = DEFAULT_HEADLINE,
  tagline,
  icon: Icon = MessageCircle,
  suggestions,
}: WelcomeStateProps) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 py-16 px-4">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.15 }}
        className="flex flex-col items-center text-center max-w-md"
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--hover)] text-[var(--muted-foreground)] mb-6">
          <Icon className="h-6 w-6" strokeWidth={1.5} />
        </div>
        <h2 className="text-[18px] font-semibold text-[var(--foreground)] mb-2">
          {headline}
        </h2>
        <p className="text-[15px] text-[var(--muted-foreground)] leading-relaxed mb-8">
          {tagline}
        </p>

        <div className="grid grid-cols-2 gap-2 w-full max-w-sm">
          {suggestions.map((text, i) => (
            <motion.button
              key={text}
              type="button"
              onClick={() => onSuggestion(text)}
              className={cn(
                "rounded-xl border border-[var(--border)] bg-transparent px-4 py-3 text-[14px] font-medium text-[var(--foreground)] text-left",
                "hover:bg-[var(--hover)] transition-colors duration-100",
                "focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20"
              )}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * i, duration: 0.15 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {text}
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
