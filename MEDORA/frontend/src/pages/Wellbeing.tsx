import { useState, useCallback, useEffect, useRef } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Heart, Mic } from "lucide-react";
import { useChatSession } from "@/hooks/useChatSession";
import { useAuth } from "@/contexts/AuthContext";
import { getMyChat } from "@/api/client";
import { ChatLayout } from "@/components/layout/ChatLayout";
import { ChatView } from "@/components/chat/ChatView";
import { Footer } from "@/components/Footer";
import { postWellbeingChatStream } from "@/api/client";

const WELCOME_TAGLINE = "I can help with emotional support and mental wellness. Share what's on your mind — no judgment.";
const QUICK_REPLIES = [
  "I've been feeling anxious",
  "How can I sleep better?",
  "Tips for a rough day",
  "I need to vent",
];

export function Wellbeing() {
  const [searchParams] = useSearchParams();
  const sessionParam = searchParams.get("session");
  const { user } = useAuth();
  const {
    sessionId,
    messages,
    contextForApi,
    addUserMessage,
    addAssistantMessage,
    updateLastAssistantMessage,
    loadSession,
  } = useChatSession();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const loadedSessionRef = useRef<string | null>(null);

  useEffect(() => {
    if (!sessionParam || !user || sessionParam === loadedSessionRef.current) return;
    getMyChat(sessionParam)
      .then((data) => {
        loadedSessionRef.current = data.client_session_id;
        loadSession(
          data.client_session_id,
          data.messages.map((m) => ({
            role: m.role as "user" | "assistant",
            content: m.content,
            agent_name: m.agent_name ?? undefined,
          }))
        );
      })
      .catch(() => { });
  }, [sessionParam, user, loadSession]);

  const handleSend = useCallback(
    async (query: string) => {
      addUserMessage(query);
      setIsLoading(true);
      setError(null);
      addAssistantMessage("", "Personal Wellbeing Counsellor");
      let fullText = "";
      try {
        await postWellbeingChatStream(
          { session_id: sessionId, query, context: contextForApi },
          (event) => {
            if (event.type === "text" && event.content) {
              fullText += event.content;
              updateLastAssistantMessage(fullText);
            } else if (event.type === "done" && event.content) {
              fullText = event.content;
              updateLastAssistantMessage(fullText);
            }
          }
        );
      } catch (e) {
        setError(e instanceof Error ? e.message : "Something went wrong.");
        updateLastAssistantMessage(
          fullText ||
          "I'm having a small technical moment. Please try again or reach out to someone you trust."
        );
      } finally {
        setIsLoading(false);
      }
    },
    [
      sessionId,
      contextForApi,
      addUserMessage,
      addAssistantMessage,
      updateLastAssistantMessage,
    ]
  );

  return (
    <ChatLayout
      agentLabel="Wellbeing"
      status={isLoading ? "thinking" : "online"}
    >
      <div className="flex flex-col flex-1 min-h-0">
        <ChatView
          messages={messages}
          onSend={handleSend}
          isLoading={isLoading}
          error={error}
          clearError={() => setError(null)}
          quickReplies={QUICK_REPLIES}
          placeholder="Share what's on your mind…"
          welcomeTagline={WELCOME_TAGLINE}
          welcomeIcon={Heart}
        />
        {/* Voice Mode entry */}
        <div className="flex justify-center py-2">
          <Link
            to="/wellbeing/voice"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-[var(--primary)] to-teal-500 text-white text-sm font-medium shadow-lg shadow-teal-500/20 hover:shadow-teal-500/40 hover:scale-105 active:scale-95 transition-all"
          >
            <Mic className="h-4 w-4" />
            Try Voice Mode
          </Link>
        </div>
        <Footer />
      </div>
    </ChatLayout>
  );
}

