import { useState, useCallback, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { MessageCircle } from "lucide-react";
import { useChatSession } from "@/hooks/useChatSession";
import { useAuth } from "@/contexts/AuthContext";
import { getMyChat } from "@/api/client";
import { ChatLayout } from "@/components/layout/ChatLayout";
import { ChatView } from "@/components/chat/ChatView";
import { Footer } from "@/components/Footer";
import { postOrchestratorChat } from "@/api/client";

const WELCOME_TAGLINE = "Ask anything — I'll route you to the right agent for symptoms, diet, or wellbeing.";
const QUICK_REPLIES = [
  "I have a headache",
  "Plan my meals",
  "I feel anxious",
  "What should I eat today?",
];

export function Ask() {
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
      .catch(() => {})
      .finally(() => {});
  }, [sessionParam, user, loadSession]);

  const handleSend = useCallback(
    async (query: string, imageBase64?: string, imageMimeType?: string) => {
      addUserMessage(query + (imageBase64 ? " [Image attached]" : ""));
      setIsLoading(true);
      setError(null);
      try {
        const res = await postOrchestratorChat({
          session_id: sessionId,
          query,
          context: contextForApi,
          image_base64: imageBase64 ?? null,
          image_mime_type: imageMimeType ?? "image/jpeg",
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
      agentLabel="Ask MEDORA"
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
          placeholder="Ask anything about your health…"
          welcomeTagline={WELCOME_TAGLINE}
          welcomeIcon={MessageCircle}
          allowImage
        />
        <Footer />
      </div>
    </ChatLayout>
  );
}
