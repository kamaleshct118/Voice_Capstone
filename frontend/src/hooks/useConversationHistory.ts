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
          
          for (let i = 0; i < data.messages.length; i += 2) {
            const userMsg = data.messages[i];
            const assistantMsg = data.messages[i + 1];
            
            if (userMsg && assistantMsg && userMsg.role === "user" && assistantMsg.role === "assistant") {
              restoredHistory.push({
                id: crypto.randomUUID(),
                query: userMsg.content,
                response: {
                  text_response: assistantMsg.content,
                  audio_url: "", // Historical messages don't have audio
                  tool_type: "general_conversation",
                  latency_ms: 0,
                  session_id: sessionId,
                },
                timestamp: new Date(),
              });
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
