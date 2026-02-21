import { useCallback, useMemo, useState } from "react";
import type { ChatMessage } from "@/api/types";

const SESSION_KEY = "medora_session_id";

function getOrCreateSessionId(): string {
  if (typeof window === "undefined") return "default";
  let id = sessionStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID?.() ?? `session-${Date.now()}`;
    sessionStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

export function useChatSession() {
  const [sessionId, setSessionId] = useState(getOrCreateSessionId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const contextForApi = useMemo(
    () =>
      messages.map((m) => ({
        role: m.role,
        content: m.content,
      })),
    [messages]
  );

  const addUserMessage = useCallback((content: string) => {
    setMessages((prev) => [...prev, { role: "user", content }]);
  }, []);

  const addAssistantMessage = useCallback(
    (content: string, agent_name?: string, pdf_data?: string) => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content, agent_name, pdf_data },
      ]);
    },
    []
  );

  /** Append to the last assistant message's content (e.g. for streaming). */
  const updateLastAssistantMessage = useCallback((content: string) => {
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (last?.role === "assistant")
        next[next.length - 1] = { ...last, content };
      return next;
    });
  }, []);

  const clearMessages = useCallback(() => {
    const newId = typeof window !== "undefined" ? (crypto.randomUUID?.() ?? `session-${Date.now()}`) : "default";
    setSessionId(newId);
    setMessages([]);
    if (typeof window !== "undefined") sessionStorage.setItem(SESSION_KEY, newId);
  }, []);

  /** Load a saved chat session (e.g. from profile history). Replaces current session id and messages. */
  const loadSession = useCallback((newSessionId: string, newMessages: ChatMessage[]) => {
    setSessionId(newSessionId);
    setMessages(newMessages);
    if (typeof window !== "undefined") sessionStorage.setItem(SESSION_KEY, newSessionId);
  }, []);

  return {
    sessionId,
    messages,
    contextForApi,
    addUserMessage,
    addAssistantMessage,
    updateLastAssistantMessage,
    clearMessages,
    loadSession,
  };
}
