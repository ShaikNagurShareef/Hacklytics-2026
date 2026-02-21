import { useState, useCallback, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { UtensilsCrossed } from "lucide-react";
import { useChatSession } from "@/hooks/useChatSession";
import { useAuth } from "@/contexts/AuthContext";
import { getMyChat } from "@/api/client";
import { ChatLayout } from "@/components/layout/ChatLayout";
import { ChatView } from "@/components/chat/ChatView";
import { Footer } from "@/components/Footer";
import { postDietaryChat } from "@/api/client";

const WELCOME_TAGLINE = "I can help with meals, nutrition, and diet plans. Ask about calories, macros, or weekly meal ideas.";
const QUICK_REPLIES = [
  "Calculate my BMR",
  "Meal plan for the week",
  "What's a balanced breakfast?",
  "Help me hit my protein goal",
];

export function Dietary() {
  const [searchParams] = useSearchParams();
  const sessionParam = searchParams.get("session");
  const { user } = useAuth();
  const {
    sessionId,
    messages,
    contextForApi,
    addUserMessage,
    addAssistantMessage,
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
      .catch(() => {});
  }, [sessionParam, user, loadSession]);

  const handleSend = useCallback(
    async (query: string, _imageBase64?: string, _imageMimeType?: string) => {
      addUserMessage(query);
      setIsLoading(true);
      setError(null);
      try {
        const res = await postDietaryChat({
          session_id: sessionId,
          query,
          context: contextForApi,
        });
        addAssistantMessage(res.content, res.agent_name);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Something went wrong.");
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, contextForApi, addUserMessage, addAssistantMessage]
  );

  return (
    <ChatLayout
      agentLabel="Dietary"
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
          placeholder="Ask about meals, calories, or nutrition…"
          welcomeTagline={WELCOME_TAGLINE}
          welcomeIcon={UtensilsCrossed}
        />
        <Footer />
      </div>
    </ChatLayout>
  );
}
