import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { ImagePlus, X, Send, Loader2, Paperclip, Mic } from "lucide-react";
import type { ChatMessage } from "@/api/types";

interface ChatPanelWithImageProps {
  messages: ChatMessage[];
  onSend: (query: string, imageBase64?: string, imageMimeType?: string) => Promise<void>;
  isLoading?: boolean;
  error: string | null;
  clearError: () => void;
  placeholder?: string;
  className?: string;
  emptyMessage?: string;
  thinkingLabel?: string;
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

export function ChatPanelWithImage({
  messages,
  onSend,
  isLoading,
  error,
  clearError,
  placeholder = "Describe your concern or attach an image…",
  className,
  emptyMessage = "Describe your concern or attach an image.",
  thinkingLabel = "Thinking…",
  quickReplies = [],
}: ChatPanelWithImageProps) {
  const [input, setInput] = useState("");
  const [preview, setPreview] = useState<{ base64: string; mime: string; dataUrl: string } | null>(null);
  const [sending, setSending] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isLoading]);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = () => {
      const data = reader.result as string;
      setPreview({
        base64: data.split(",")[1] ?? "",
        mime: file.type,
        dataUrl: data,
      });
    };
    reader.readAsDataURL(file);
  };

  const clearPreview = () => {
    setPreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if ((!q && !preview) || isLoading) return;
    clearError();
    setSending(true);
    try {
      await onSend(q || "What do you see?", preview?.base64, preview?.mime);
      setInput("");
      clearPreview();
    } finally {
      setSending(false);
    }
  };

  const handleQuickReply = (text: string) => {
    setSending(true);
    clearError();
    onSend(text).finally(() => setSending(false));
  };

  const isDisabled = isLoading || sending || (!input.trim() && !preview);
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
      {preview && (
        <div className="mb-3 flex items-center gap-3 rounded-xl border border-border bg-card p-3 shadow-card animate-scale-in">
          <img
            src={preview.dataUrl}
            alt="Attached"
            className="h-14 w-14 rounded-lg object-cover border border-border"
          />
          <span className="text-sm text-muted-foreground flex-1">Image attached</span>
          <button
            type="button"
            onClick={clearPreview}
            className="rounded-lg p-2 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
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
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFile}
            className="hidden"
            aria-label="Attach image"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
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
