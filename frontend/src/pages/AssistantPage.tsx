import { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Activity, Wifi, AlertCircle, ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import ChatSidebar from "@/components/ChatSidebar";
import ChatInput from "@/components/ChatInput";
import ResponseCard from "@/components/ResponseCard";
import AudioPlayer from "@/components/AudioPlayer";
import MapPopup from "@/components/MapPopup";
import type { ApiResponse, AppStatus, ChatMessage } from "@/types/clinical";

const statusConfig: Record<AppStatus, { label: string; color: string }> = {
  idle: { label: "Ready", color: "bg-clinical-green" },
  recording: { label: "Recording", color: "bg-destructive" },
  processing: { label: "Processing", color: "bg-clinical-amber" },
  ready: { label: "Connected", color: "bg-clinical-green" },
  error: { label: "Error", color: "bg-destructive" },
};

const AssistantPage = () => {
  const [status, setStatus] = useState<AppStatus>("idle");
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [selectedMsg, setSelectedMsg] = useState<ChatMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showMap, setShowMap] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleResponse = (data: ApiResponse, query: string) => {
    const msg: ChatMessage = {
      id: crypto.randomUUID(),
      query,
      response: data,
      timestamp: new Date(),
    };
    setHistory((prev) => [msg, ...prev]);
    setSelectedMsg(msg);
    setError(null);
  };

  const handleError = (msg: string) => {
    setError(msg);
  };

  // Auto-scroll when new message
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }, [history.length]);

  const st = statusConfig[status];
  const displayMsg = selectedMsg;

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <ChatSidebar
          history={history}
          onSelect={setSelectedMsg}
          activeId={selectedMsg?.id}
        />
        <div className="flex-1 flex flex-col min-h-screen">
          {/* Header */}
          <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-40">
            <div className="flex items-center justify-between px-4 h-14">
              <div className="flex items-center gap-2">
                <SidebarTrigger />
                <Link to="/" className="p-2 rounded-lg hover:bg-muted transition-colors text-muted-foreground">
                  <ArrowLeft className="w-4 h-4" />
                </Link>
                <div>
                  <h1 className="text-base font-bold text-foreground flex items-center gap-2">
                    <Activity className="w-4 h-4 text-primary" />
                    Clinical Assistant
                  </h1>
                </div>
              </div>
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full text-primary-foreground ${st.color}`}>
                <Wifi className="w-3 h-3" />
                {st.label}
              </span>
            </div>
          </header>

          {/* Chat area */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 md:p-6">
            <div className="max-w-2xl mx-auto space-y-4">
              {/* Welcome when empty */}
              {history.length === 0 && !error && (
                <motion.div
                  className="text-center py-20"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                    <Activity className="w-8 h-8 text-primary" />
                  </div>
                  <h2 className="text-xl font-semibold text-foreground">How can I help you?</h2>
                  <p className="text-sm text-muted-foreground mt-2 max-w-md mx-auto">
                    Type a query or tap the microphone to ask about medications, locate clinics, or get medical information.
                  </p>
                </motion.div>
              )}

              {/* Error */}
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

              {/* Selected message response */}
              {displayMsg && (
                <div className="space-y-3">
                  {/* User query bubble */}
                  <motion.div
                    className="flex justify-end"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                  >
                    <div className="px-4 py-2.5 rounded-2xl rounded-br-md bg-primary text-primary-foreground text-sm max-w-[80%]">
                      {displayMsg.query}
                    </div>
                  </motion.div>

                  {/* Assistant response */}
                  <ResponseCard data={displayMsg.response} onShowMap={() => setShowMap(true)} />
                  {displayMsg.response.audio_url && (
                    <AudioPlayer audioUrl={displayMsg.response.audio_url} />
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Input */}
          <ChatInput
            status={status}
            onStatusChange={setStatus}
            onResponse={handleResponse}
            onError={handleError}
          />
        </div>
      </div>

      {/* Map popup */}
      <AnimatePresence>
        {showMap && displayMsg?.response.map_data && (
          <MapPopup data={displayMsg.response.map_data} onClose={() => setShowMap(false)} />
        )}
      </AnimatePresence>
    </SidebarProvider>
  );
};

export default AssistantPage;
