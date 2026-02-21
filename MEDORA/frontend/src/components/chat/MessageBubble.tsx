import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { RotateCcw, Copy, ThumbsUp, ThumbsDown, FileText, Volume2 } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  agentName?: string;
  agentIcon?: LucideIcon;
  quickReplies?: string[];
  onQuickReply?: (text: string) => void;
  onRegenerate?: () => void;
  onSpeak?: (text: string) => void;
  pdfData?: string;
}

export function MessageBubble({
  role,
  content,
  agentName,
  agentIcon: AgentIcon,
  quickReplies = [],
  onQuickReply,
  onRegenerate,
  onSpeak,
  pdfData,
}: MessageBubbleProps) {
  const [, setShowTime] = useState(false);
  const [copied, setCopied] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  useEffect(() => {
    if (pdfData) {
      try {
        const byteCharacters = atob(pdfData);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        setPdfUrl(url);
        return () => URL.revokeObjectURL(url);
      } catch (e) {
        console.error("Failed to decode PDF data", e);
      }
    }
  }, [pdfData]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (role === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ type: "spring", stiffness: 400, damping: 25 }}
        className="flex justify-end pl-12"
      >
        <div
          onMouseEnter={() => setShowTime(true)}
          onMouseLeave={() => setShowTime(false)}
          className="max-w-full rounded-2xl bg-[var(--user-bubble)] px-5 py-3.5 text-[var(--foreground)] shadow-sm hover:shadow-md transition-shadow duration-200"
        >
          <p className="text-[15px] sm:text-[16px] leading-relaxed whitespace-pre-wrap">
            {content}
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className="flex gap-3 md:gap-4 pr-4 group"
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--hover)] mt-0.5 border border-[var(--border)] shadow-sm group-hover:scale-105 transition-transform duration-200">
        {AgentIcon ? (
          <AgentIcon className="h-4 w-4 text-[var(--primary)]" strokeWidth={1.5} />
        ) : (
          <span className="text-[12px] font-semibold text-[var(--primary)]">M</span>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="mb-1.5 flex items-center gap-2 text-[13px] text-[var(--muted-foreground)]">
          <span className="font-semibold text-[var(--foreground)]">MEDORA</span>
          {agentName && (
            <>
              <span className="opacity-40">/</span>
              <span className="font-medium text-[var(--primary)]">{agentName}</span>
            </>
          )}
        </div>
        
        <div className="prose prose-neutral dark:prose-invert max-w-none">
          <p className="text-[15px] sm:text-[16px] leading-relaxed whitespace-pre-wrap text-[var(--foreground)]">
            {content}
          </p>
        </div>

        {pdfUrl && (
          <div className="mt-4">
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors mb-2"
            >
              <FileText className="w-4 h-4" />
              Open PDF Report
            </a>
            <div className="border rounded-lg overflow-hidden h-96 bg-gray-100">
               <iframe src={pdfUrl} className="w-full h-full" title="Diagnostic Report PDF" />
            </div>
          </div>
        )}

        {quickReplies.length > 0 && onQuickReply && (
          <div className="flex flex-wrap gap-2 mt-4">
            {quickReplies.map((text) => (
              <button
                key={text}
                type="button"
                onClick={() => onQuickReply(text)}
                className="rounded-xl border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-[13px] sm:text-[14px] font-medium text-[var(--foreground)] hover:bg-[var(--hover)] hover:border-[var(--primary)]/30 transition-all duration-200 shadow-sm active:scale-95"
              >
                {text}
              </button>
            ))}
          </div>
        )}
        
        <div className="flex items-center gap-3 mt-3 text-[13px] text-[var(--muted-foreground)]">
          {onRegenerate && (
            <button
              type="button"
              onClick={onRegenerate}
              className="inline-flex items-center gap-1.5 py-1 px-1.5 -ml-1.5 rounded-md hover:bg-[var(--hover)] hover:text-[var(--foreground)] transition-colors"
              aria-label="Regenerate response"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Regenerate</span>
            </button>
          )}
          {onSpeak && content.trim() && (
            <button
              type="button"
              onClick={() => onSpeak(content)}
              className="inline-flex items-center gap-1.5 py-1 px-1.5 rounded-md hover:bg-[var(--hover)] hover:text-[var(--foreground)] transition-colors"
              aria-label="Read aloud"
            >
              <Volume2 className="h-3.5 w-3.5" />
              <span>Read aloud</span>
            </button>
          )}
          <button
            type="button"
            onClick={handleCopy}
            className="inline-flex items-center gap-1.5 py-1 px-1.5 rounded-md hover:bg-[var(--hover)] hover:text-[var(--foreground)] transition-colors"
            aria-label="Copy message"
          >
            <Copy className="h-3.5 w-3.5" />
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
          <div className="flex items-center border-l border-[var(--border)] pl-2 ml-1 space-x-1">
            <button
              type="button"
              className="p-1.5 rounded-md hover:bg-[var(--hover)] hover:text-green-600 transition-colors"
              aria-label="Good response"
            >
              <ThumbsUp className="h-3.5 w-3.5" />
            </button>
            <button
              type="button"
              className="p-1.5 rounded-md hover:bg-[var(--hover)] hover:text-red-600 transition-colors"
              aria-label="Bad response"
            >
              <ThumbsDown className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
