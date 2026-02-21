import { useState, useCallback, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { Stethoscope } from "lucide-react";
import { useChatSession } from "@/hooks/useChatSession";
import { useAuth } from "@/contexts/AuthContext";
import { getMyChat } from "@/api/client";
import { ChatLayout } from "@/components/layout/ChatLayout";
import { ChatView } from "@/components/chat/ChatView";
import { Footer } from "@/components/Footer";
import { postVirtualDoctorChat } from "@/api/client";

const WELCOME_TAGLINE = "I can help with symptoms, triage, and image-based questions. Describe your concern or attach an image.";
const QUICK_REPLIES = [
  "What could this rash be?",
  "I have a headache, what should I do?",
  "Analyse this image",
  "When should I see a doctor?",
];

export function VirtualDoctor() {
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
    async (query: string, imageBase64?: string, imageMimeType?: string) => {
      addUserMessage(query + (imageBase64 ? " [Image attached]" : ""));
      setIsLoading(true);
      setError(null);
      try {
        const res = await postVirtualDoctorChat({
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
      agentLabel="Virtual Doctor"
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
          placeholder="Describe your concern or attach an image…"
          allowImage
          welcomeTagline={WELCOME_TAGLINE}
          welcomeIcon={Stethoscope}
        />
        <Footer />
      </div>
    </ChatLayout>
  );
}
