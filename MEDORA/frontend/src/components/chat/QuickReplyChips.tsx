import { motion } from "framer-motion";

interface QuickReplyChipsProps {
  replies: string[];
  onSelect: (text: string) => void;
  disabled?: boolean;
}

export function QuickReplyChips({ replies, onSelect, disabled }: QuickReplyChipsProps) {
  return (
    <div className="flex flex-wrap gap-2 pl-12">
      {replies.map((text) => (
        <motion.button
          key={text}
          type="button"
          onClick={() => !disabled && onSelect(text)}
          disabled={disabled}
          className="rounded-full border border-[var(--border)] bg-transparent px-4 py-2 text-[13px] font-medium text-[var(--foreground)] transition-all duration-200 hover:border-[#14B8A6] hover:bg-[#14B8A6]/10 hover:text-[#14B8A6] focus:outline-none focus:ring-2 focus:ring-[#14B8A6]/30 disabled:opacity-50"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {text}
        </motion.button>
      ))}
    </div>
  );
}
