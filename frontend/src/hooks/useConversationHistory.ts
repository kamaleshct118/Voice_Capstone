import { useState, useEffect } from "react";
import type { ChatMessage } from "@/types/clinical";

const API = "http://localhost:8000/api";

interface ConversationHistoryData {
  messages: Array<{ role: string; content: string }>;
  session_id: string;
  has_history: boolean;
}

export const useConversationHistory = (sessionId: string) => {
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setIsLoading(true);
        const res = await fetch(`${API}/conversation-history/${sessionId}`);

        if (!res.ok) {
          throw new Error("Failed to fetch conversation history");
        }

        const data: ConversationHistoryData = await res.json();

        if (data.has_history && data.messages.length > 0) {
          // Convert stored messages to ChatMessage format
          // Messages are stored as alternating user/assistant pairs
          const restoredHistory: ChatMessage[] = [];

          let i = 0;
          while (i < data.messages.length) {
            const msg = data.messages[i];

            if (msg.role === "user") {
              // Try to find the matching assistant response, which should be the next message
              let assistantMsg = null;
              if (i + 1 < data.messages.length && data.messages[i + 1].role === "assistant") {
                assistantMsg = data.messages[i + 1];
                i += 2; // Advance past this pair
              } else {
                // The assistant response failed or is missing, we create a placeholder or just display the user message
                assistantMsg = { role: "assistant", content: "Error: No response generated." };
                i += 1; // Only advance past the user message
              }

              restoredHistory.push({
                id: crypto.randomUUID(),
                query: msg.content,
                response: {
                  text_response: assistantMsg.content,
                  audio_url: "", // Historical messages don't have audio
                  tool_type: "general_conversation",
                  latency_ms: 0,
                  session_id: sessionId,
                },
                timestamp: new Date(),
              });
            } else {
              // If we see an assistant message without a preceding user message for some reason, ignore it or handle it.
              i += 1;
            }
          }

          setHistory(restoredHistory);
        }
      } catch (err) {
        console.error("Failed to load conversation history:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setIsLoading(false);
      }
    };

    if (sessionId) {
      loadHistory();
    }
  }, [sessionId]);

  const addMessage = (message: ChatMessage) => {
    setHistory((prev) => [...prev, message]);
  };

  const clearHistory = () => {
    setHistory([]);
  };

  return {
    history,
    isLoading,
    error,
    addMessage,
    clearHistory,
  };
};
