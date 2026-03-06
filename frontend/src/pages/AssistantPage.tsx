import { useState, useRef, useEffect, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Activity, Wifi, AlertCircle, ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import ChatSidebar from "@/components/ChatSidebar";
import ChatInput from "@/components/ChatInput";
import ResponseCard from "@/components/ResponseCard";
import AudioPlayer from "@/components/AudioPlayer";
import { useConversationHistory } from "@/hooks/useConversationHistory";
import { getOrCreateAssistantSession } from "@/utils/session";
import type { ApiResponse, AppStatus, ChatMessage } from "@/types/clinical";

const statusConfig: Record<AppStatus, { label: string; color: string }> = {
  idle: { label: "Ready", color: "bg-clinical-green" },
  recording: { label: "Recording", color: "bg-destructive" },
  processing: { label: "Processing", color: "bg-clinical-amber" },
  ready: { label: "Connected", color: "bg-clinical-green" },
  error: { label: "Error", color: "bg-destructive" },
};

const AssistantPage = () => {
  const sessionId = useMemo(getOrCreateAssistantSession, []);
  const { history, isLoading: isLoadingHistory, addMessage } = useConversationHistory(sessionId);
  const [status, setStatus] = useState<AppStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom whenever a new message is added
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history.length]);

  const handleResponse = (data: ApiResponse, query: string) => {
    const msg: ChatMessage = {
      id: crypto.randomUUID(),
      query,
      response: data,
      timestamp: new Date(),
    };
    addMessage(msg);
    setError(null);
  };

  const handleError = (msg: string) => {
    setError(msg);
    setStatus("error");
  };

  const st = statusConfig[status];

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        {/* Sidebar shows full history for navigation */}
        <ChatSidebar
          history={[...history].reverse()}   // sidebar shows newest first
          onSelect={() => { }}                 // clicking sidebar just highlights (no-op here)
          activeId={history[history.length - 1]?.id}
        />

        <div className="flex-1 flex flex-col min-h-screen">
          {/* ── Header ─────────────────────────────────────────── */}
          <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-40">
            <div className="flex items-center justify-between px-4 h-14">
              <div className="flex items-center gap-2">
                <SidebarTrigger />
                <Link
                  to="/"
                  className="p-2 rounded-lg hover:bg-muted transition-colors text-muted-foreground"
                >
                  <ArrowLeft className="w-4 h-4" />
                </Link>
                <h1 className="text-base font-bold text-foreground flex items-center gap-2">
                  <Activity className="w-4 h-4 text-primary" />
                  Clinical Assistant
                </h1>
              </div>
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full text-primary-foreground ${st.color}`}
              >
                <Wifi className="w-3 h-3" />
                {st.label}
              </span>
            </div>
          </header>

          {/* ── Scrollable chat feed ────────────────────────────── */}
          <div className="flex-1 overflow-y-auto p-4 md:p-6">
            <div className="max-w-2xl mx-auto space-y-6">

              {/* Loading history indicator */}
              {isLoadingHistory && (
                <motion.div
                  className="text-center py-20"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                    <Activity className="w-8 h-8 text-primary animate-pulse" />
                  </div>
                  <p className="text-sm text-muted-foreground">Loading conversation history...</p>
                </motion.div>
              )}

              {/* Welcome screen — only when empty and not loading */}
              {!isLoadingHistory && history.length === 0 && !error && (
                <motion.div
                  className="text-center py-20"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                    <Activity className="w-8 h-8 text-primary" />
                  </div>
                  <h2 className="text-xl font-semibold text-foreground">
                    How can I help you?
                  </h2>
                  <p className="text-sm text-muted-foreground mt-2 max-w-md mx-auto">
                    Speak or type to ask about medications, medical news,
                    generate a health report, or just have a healthcare
                    conversation.
                  </p>
                  <div className="mt-6 grid grid-cols-2 gap-3 max-w-sm mx-auto text-left">
                    {[
                      "Tell me about ibuprofen",
                      "Latest cancer research news",
                      "Generate my health report",
                      "What's a normal blood pressure?",
                    ].map((example) => (
                      <div
                        key={example}
                        className="px-3 py-2 rounded-xl border border-border bg-card text-xs text-muted-foreground select-none"
                      >
                        {example}
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Error banner */}
              <AnimatePresence>
                {error && (
                  <motion.div
                    className="flex items-center gap-3 p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <AlertCircle className="w-5 h-5 shrink-0" />
                    {error}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* ── All messages, oldest → newest ─────────────── */}
              {history.map((msg) => (
                <motion.div
                  key={msg.id}
                  className="space-y-3"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35 }}
                >
                  {/* User query bubble */}
                  <div className="flex justify-end">
                    <div className="px-4 py-2.5 rounded-2xl rounded-br-md bg-primary text-primary-foreground text-sm max-w-[80%]">
                      {msg.query}
                    </div>
                  </div>

                  {/* Assistant response card */}
                  <ResponseCard data={msg.response} />

                  {/* Audio player */}
                  {msg.response.audio_url && (
                    <AudioPlayer audioUrl={msg.response.audio_url} />
                  )}
                </motion.div>
              ))}

              {/* Processing indicator */}
              {status === "processing" && (
                <motion.div
                  className="flex gap-1.5 px-4 py-3"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  {[0, 1, 2].map((i) => (
                    <motion.div
                      key={i}
                      className="w-2 h-2 rounded-full bg-primary"
                      animate={{ y: [0, -6, 0] }}
                      transition={{
                        duration: 0.6,
                        repeat: Infinity,
                        delay: i * 0.15,
                      }}
                    />
                  ))}
                </motion.div>
              )}

              {/* Invisible anchor — always scrolled into view */}
              <div ref={bottomRef} />
            </div>
          </div>

          {/* ── Input bar ──────────────────────────────────────── */}
          <ChatInput
            status={status}
            onStatusChange={setStatus}
            onResponse={handleResponse}
            onError={handleError}
            sessionId={sessionId}
          />
        </div>
      </div>
    </SidebarProvider>
  );
};

export default AssistantPage;
