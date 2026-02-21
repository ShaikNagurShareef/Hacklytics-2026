import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { Send, Loader2, Paperclip, ImagePlus, Mic } from "lucide-react";
import type { ChatMessage } from "@/api/types";

interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (query: string) => Promise<void>;
  isLoading?: boolean;
  error: string | null;
  clearError: () => void;
  placeholder?: string;
  className?: string;
  emptyMessage?: string;
  thinkingLabel?: string;
  /** Quick reply chips shown below the last AI message */
  quickReplies?: string[];
}

function TypingDots() {
  return (
    <span className="flex gap-1">
      <span className="h-2 w-2 rounded-full bg-muted-foreground animate-typing-dot" style={{ animationDelay: "0ms" }} />
      <span className="h-2 w-2 rounded-full bg-muted-foreground animate-typing-dot" style={{ animationDelay: "150ms" }} />
      <span className="h-2 w-2 rounded-full bg-muted-foreground animate-typing-dot" style={{ animationDelay: "300ms" }} />
    </span>
  );
}

export function ChatPanel({
  messages,
  onSend,
  isLoading,
  error,
  clearError,
  placeholder = "Type your message…",
  className,
  emptyMessage = "Send a message to start.",
  thinkingLabel = "Thinking…",
  quickReplies = [],
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || isLoading) return;
    setInput("");
    clearError();
    setSending(true);
    try {
      await onSend(q);
    } finally {
      setSending(false);
    }
  };

  const handleQuickReply = (text: string) => {
    setSending(true);
    clearError();
    onSend(text).finally(() => setSending(false));
  };

  const isDisabled = isLoading || sending || !input.trim();
  const lastAssistant = messages.length > 0 && messages[messages.length - 1].role === "assistant";
  const showQuickReplies = quickReplies.length > 0 && lastAssistant && !isLoading;

  return (
    <div className={cn("flex flex-col h-[calc(100vh-8rem)] md:h-[calc(100vh-6rem)] min-h-[280px]", className)}>
      <div
        ref={listRef}
        className="scrollbar-thin flex-1 overflow-y-auto px-1 py-4 space-y-4"
        role="log"
        aria-live="polite"
      >
        {messages.length === 0 && !isLoading && (
          <p className="text-muted-foreground text-sm text-center py-12 animate-fade-in">
            {emptyMessage}
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className="flex flex-col gap-2">
            <div
              className={cn(
                "max-w-[85%] rounded-bubble px-4 py-3 text-sm leading-relaxed transition-all duration-200 animate-fade-in-up",
                m.role === "user"
                  ? "ml-auto bg-primary text-primary-foreground shadow-card"
                  : "mr-auto bg-card text-foreground border border-border shadow-card"
              )}
            >
              {m.role === "assistant" && m.agent_name && (
                <p className="text-xs text-muted-foreground mb-1.5 font-medium">
                  {m.agent_name}
                </p>
              )}
              <p className="whitespace-pre-wrap">{m.content}</p>
            </div>
            {m.role === "assistant" && i === messages.length - 1 && showQuickReplies && (
              <div className="flex flex-wrap gap-2 mr-auto animate-fade-in-up">
                {quickReplies.map((reply) => (
                  <button
                    key={reply}
                    type="button"
                    onClick={() => handleQuickReply(reply)}
                    disabled={isLoading || sending}
                    className="rounded-full border border-border bg-card px-4 py-2 text-xs font-medium text-foreground shadow-card transition-all duration-200 hover:bg-accent hover:border-primary/30 active:scale-[0.98] disabled:opacity-50"
                  >
                    {reply}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="mr-auto max-w-[85%] rounded-bubble px-4 py-3 bg-card border border-border shadow-card animate-fade-in-up flex items-center gap-2">
            <TypingDots />
            <span className="text-muted-foreground text-sm">{thinkingLabel}</span>
          </div>
        )}
      </div>
      {error && (
        <div
          className="mb-3 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive animate-fade-in"
          role="alert"
        >
          {error}
        </div>
      )}
      <form onSubmit={handleSubmit} className="flex gap-2 items-end">
        <div className="flex-1 flex items-center gap-2 rounded-2xl border border-border bg-card px-3 py-2 shadow-card min-h-12">
          <button
            type="button"
            className="p-1.5 rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
            title="Attach file"
          >
            <Paperclip className="h-5 w-5" />
          </button>
          <button
            type="button"
            className="p-1.5 rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
            title="Attach image"
          >
            <ImagePlus className="h-5 w-5" />
          </button>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={placeholder}
            disabled={isLoading}
            className="flex-1 border-0 bg-transparent shadow-none focus-visible:ring-0 min-h-9 py-2"
            aria-label="Message"
          />
          <button
            type="button"
            className="p-1.5 rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
            title="Voice message"
          >
            <Mic className="h-5 w-5" />
          </button>
        </div>
        <button
          type="submit"
          disabled={isDisabled}
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-card transition-all duration-200 hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
          aria-label="Send"
        >
          {sending || isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </button>
      </form>
    </div>
  );
}
