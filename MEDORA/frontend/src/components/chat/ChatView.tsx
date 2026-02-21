import { useState, useRef, useEffect } from "react";
import { ArrowDown, Mic, Square } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import { WelcomeState } from "./WelcomeState";
import { InputBar } from "./InputBar";
import { agents } from "@/components/layout/Sidebar";
import type { ChatMessage } from "@/api/types";
import { cn } from "@/lib/utils";

function agentForName(agentName: string | undefined) {
  if (!agentName) return undefined;
  const lower = agentName.toLowerCase();
  if (lower.includes("orchestrator")) return agents[0]; // Ask MEDORA
  if (lower.includes("virtual") || lower.includes("doctor")) return agents[1];
  if (lower.includes("dietary")) return agents[2];
  if (lower.includes("wellbeing") || lower.includes("wellness") || lower.includes("counsellor"))
    return agents[3];
  if (lower.includes("diagnostic")) return agents[4];
  return undefined;
}

/** Voice (speech-to-text) state passed from parent when allowVoice is true */
export interface VoiceState {
  isListening: boolean;
  isSupported: boolean;
  transcript: string;
}

interface ChatViewProps {
  messages: ChatMessage[];
  onSend: (query: string, imageBase64?: string, imageMimeType?: string) => Promise<void>;
  isLoading?: boolean;
  error: string | null;
  clearError: () => void;
  quickReplies?: string[];
  placeholder?: string;
  allowImage?: boolean;
  /** Enable mic for speech-to-text and optional text-to-speech for replies */
  allowVoice?: boolean;
  voiceState?: VoiceState;
  onStartVoice?: () => void;
  onStopVoice?: () => void;
  /** When set, assistant messages show "Read aloud" and call this on click */
  onSpeakReply?: (text: string) => void;
  welcomeHeadline?: string;
  welcomeTagline: string;
  welcomeIcon?: LucideIcon;
}

export function ChatView({
  messages,
  onSend,
  isLoading,
  error,
  clearError,
  quickReplies = [],
  placeholder = "Message MEDORA...",
  allowImage = false,
  allowVoice = false,
  voiceState,
  onStartVoice,
  onStopVoice,
  onSpeakReply,
  welcomeHeadline,
  welcomeTagline,
  welcomeIcon,
}: ChatViewProps) {
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [imagePreview, setImagePreview] = useState<{ base64: string; mime: string } | null>(null);
  const [showScrollBottom, setShowScrollBottom] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  const isListening = voiceState?.isListening ?? false;
  const voiceTranscript = voiceState?.transcript ?? "";
  const isVoiceSupported = voiceState?.isSupported ?? false;
  const showVoice = allowVoice && isVoiceSupported;
  const inputDisplayValue = showVoice && isListening ? voiceTranscript : input;

  useEffect(() => {
    // Only auto-scroll if we are already near bottom or if it's a new message
    if (listRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = listRef.current;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      
      if (isNearBottom || messages[messages.length - 1]?.role === "user") {
        listRef.current.scrollTo({ top: scrollHeight, behavior: "smooth" });
      }
    }
  }, [messages, isLoading]);

  const handleScroll = () => {
    if (listRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = listRef.current;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      setShowScrollBottom(!isNearBottom);
    }
  };

  const scrollToBottom = () => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  };

  const handleSend = async () => {
    const q = inputDisplayValue.trim();
    if ((!q && !imagePreview) || isLoading) return;
    setInput("");
    clearError();
    setSending(true);
    try {
      await onSend(q || "What do you see?", imagePreview?.base64, imagePreview?.mime ?? "image/jpeg");
      setImagePreview(null);
    } finally {
      setSending(false);
    }
  };

  const handleImageSelect = (file: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      const data = reader.result as string;
      setImagePreview({ base64: data.split(",")[1] ?? "", mime: file.type });
    };
    reader.readAsDataURL(file);
  };

  const handleQuickReply = (text: string) => {
    setSending(true);
    clearError();
    onSend(text).finally(() => setSending(false));
  };

  const handleSuggestion = (text: string) => {
    setSending(true);
    clearError();
    onSend(text).finally(() => setSending(false));
  };

  const lastAssistant = messages.length > 0 && messages[messages.length - 1].role === "assistant";
  const showChips = quickReplies.length > 0 && lastAssistant && !isLoading;
  const isEmpty = messages.length === 0 && !isLoading;
  const handleVoiceToggle = () => {
    if (isListening) onStopVoice?.();
    else onStartVoice?.();
  };

  return (
    <div className="grid grid-rows-1 grid-cols-1 flex-1 min-h-0 relative">
      <div
        ref={listRef}
        onScroll={handleScroll}
        className="row-start-1 col-start-1 overflow-y-auto scrollbar-thin pb-32"
        role="log"
        aria-live="polite"
      >
        {isEmpty ? (
          <div className="min-h-full flex flex-col">
            <WelcomeState
              onSuggestion={handleSuggestion}
              headline={welcomeHeadline}
              tagline={welcomeTagline}
              icon={welcomeIcon}
              suggestions={quickReplies}
            />
          </div>
        ) : (
          <div className="space-y-6 pt-4">
            {messages.map((m, i) => {
              const agent = agentForName(m.agent_name);
              const isLastAssistant = m.role === "assistant" && i === messages.length - 1;
              return (
                <div key={i} className="space-y-1">
                  <MessageBubble
                    role={m.role}
                    content={m.content}
                    agentName={m.role === "assistant" ? (agent?.label ?? m.agent_name) : undefined}
                    agentIcon={m.role === "assistant" ? agent?.icon : undefined}
                    quickReplies={isLastAssistant && showChips ? quickReplies : undefined}
                    onQuickReply={isLastAssistant && showChips ? handleQuickReply : undefined}
                    onRegenerate={m.role === "assistant" ? undefined : undefined}
                    onSpeak={m.role === "assistant" ? onSpeakReply : undefined}
                    pdfData={m.pdf_data}
                  />
                </div>
              );
            })}
            {isLoading && <TypingIndicator />}
          </div>
        )}
      </div>

      <div className="row-start-1 col-start-1 pointer-events-none z-10 flex flex-col justify-end">
        <AnimatePresence>
          {showScrollBottom && (
            <div className="pointer-events-auto flex justify-end px-6 pb-2">
              <motion.button
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                onClick={scrollToBottom}
                className="flex h-10 w-10 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--background)] shadow-lg hover:bg-[var(--hover)] transition-colors"
                aria-label="Scroll to bottom"
              >
                <ArrowDown className="h-5 w-5 text-[var(--muted-foreground)]" />
              </motion.button>
            </div>
          )}
        </AnimatePresence>

        <div className="pointer-events-auto bg-gradient-to-t from-[var(--background)] via-[var(--background)]/80 to-transparent pt-10 pb-2 px-4">
          {error && (
            <div
              className="mb-2 rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/20 px-3 py-2 text-[13px] text-red-700 dark:text-red-400"
              role="alert"
            >
              {error}
            </div>
          )}

          {imagePreview && (
            <div className="relative mb-2 inline-flex items-center gap-3 rounded-xl border border-[var(--border)] bg-[var(--hover)] p-2 pr-4">
              <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--background)]">
                <img
                  src={`data:${imagePreview.mime};base64,${imagePreview.base64}`}
                  alt="Preview"
                  className="h-full w-full object-cover"
                />
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-[12px] font-medium text-[var(--foreground)]">Image attached</span>
                <button
                  type="button"
                  onClick={() => setImagePreview(null)}
                  className="text-left text-[11px] font-medium text-red-500 hover:underline"
                >
                  Remove
                </button>
              </div>
            </div>
          )}

          <div className="flex items-end gap-2 w-full">
            {showVoice && (
              <motion.button
                type="button"
                onClick={handleVoiceToggle}
                className={cn(
                  "flex-shrink-0 flex items-center justify-center w-11 h-11 rounded-xl transition-colors",
                  isListening
                    ? "bg-red-500/20 text-red-600 dark:text-red-400 animate-pulse"
                    : "bg-[var(--hover)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--primary)]/10"
                )}
                aria-label={isListening ? "Stop listening and send" : "Speak"}
                title={isListening ? "Stop and send" : "Speak"}
              >
                {isListening ? (
                  <Square className="h-5 w-5" strokeWidth={2} fill="currentColor" />
                ) : (
                  <Mic className="h-5 w-5" strokeWidth={1.5} />
                )}
              </motion.button>
            )}
            <div className="flex-1 min-w-0 flex flex-col">
              <InputBar
                value={showVoice && isListening ? voiceTranscript : input}
                onChange={setInput}
                onSubmit={handleSend}
                onImageSelect={allowImage ? handleImageSelect : undefined}
                disabled={isLoading || sending}
                placeholder={isListening ? "Listening…" : placeholder}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
