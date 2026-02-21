import { useRef, useState, useEffect } from "react";
import { Send, Paperclip } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface InputBarProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  onImageSelect?: (file: File) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function InputBar({
  value,
  onChange,
  onSubmit,
  onImageSelect,
  disabled,
  placeholder = "Message MEDORA...",
}: InputBarProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!value.trim() || disabled) return;
    onSubmit();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file?.type.startsWith("image/") && onImageSelect) onImageSelect(file);
    e.target.value = "";
  };

  const canSend = value.trim().length > 0 && !disabled;

  return (
    <motion.div
      layout
      className={cn(
        "relative flex items-end gap-2 w-full min-w-0 rounded-[24px] border bg-[var(--background)]/80 backdrop-blur-xl p-2 shadow-lg transition-all duration-200",
        "border-[var(--border)]",
        focused ? "border-[var(--primary)] ring-1 ring-[var(--primary)] shadow-xl shadow-[var(--primary)]/5" : "hover:border-[var(--border)]/80 hover:shadow-xl"
      )}
    >
        {onImageSelect && (
          <div className="flex-shrink-0 mb-0.5">
            <motion.button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="flex items-center justify-center w-9 h-9 rounded-xl text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--hover)] transition-colors"
              aria-label="Attach image"
              title="Attach image"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Paperclip className="h-5 w-5" strokeWidth={1.5} />
            </motion.button>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={handleFile}
              className="hidden"
            />
          </div>
        )}
        
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 min-w-0 py-3 bg-transparent text-[16px] leading-relaxed text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none resize-none max-h-[200px]"
          aria-label="Message"
        />

        <div className="flex-shrink-0 mb-0.5">
          <motion.button
            layout
            type="button"
            onClick={() => handleSubmit()}
            disabled={!canSend}
            className={cn(
              "flex items-center justify-center w-9 h-9 rounded-xl transition-all duration-200",
              canSend
                ? "bg-[var(--primary)] text-[var(--primary-foreground)] shadow-md hover:brightness-110"
                : "bg-[var(--hover)] text-[var(--muted-foreground)]"
            )}
            whileHover={canSend ? { scale: 1.05 } : {}}
            whileTap={canSend ? { scale: 0.95 } : {}}
            initial={false}
            animate={{
              scale: canSend ? 1 : 1,
              opacity: canSend ? 1 : 0.5,
              rotate: canSend ? 0 : 0
            }}
            aria-label="Send message"
          >
            <Send className="h-4 w-4" strokeWidth={2} />
          </motion.button>
        </div>
    </motion.div>
  );
}
