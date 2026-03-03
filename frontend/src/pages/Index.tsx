import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Activity, Wifi, AlertCircle } from "lucide-react";
import MicRecorder from "@/components/MicRecorder";
import ResponseCard from "@/components/ResponseCard";
import AudioPlayer from "@/components/AudioPlayer";
import MapPopup from "@/components/MapPopup";
import type { ApiResponse, AppStatus } from "@/types/clinical";

const statusConfig: Record<AppStatus, { label: string; color: string; icon: React.ReactNode }> = {
  idle: { label: "Ready", color: "bg-clinical-green", icon: <Wifi className="w-3 h-3" /> },
  recording: { label: "Recording", color: "bg-destructive", icon: <Activity className="w-3 h-3 animate-pulse" /> },
  processing: { label: "Processing", color: "bg-clinical-amber", icon: <Activity className="w-3 h-3 animate-spin" /> },
  ready: { label: "Connected", color: "bg-clinical-green", icon: <Wifi className="w-3 h-3" /> },
  error: { label: "Error", color: "bg-destructive", icon: <AlertCircle className="w-3 h-3" /> },
};

const Index = () => {
  const [status, setStatus] = useState<AppStatus>("idle");
  const [response, setResponse] = useState<ApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showMap, setShowMap] = useState(false);

  const handleResponse = (data: ApiResponse) => {
    setResponse(data);
    setError(null);
  };

  const handleError = (msg: string) => {
    setError(msg);
    setResponse(null);
  };

  const st = statusConfig[status];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="container max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-foreground tracking-tight flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary" />
              Clinical Assistant
            </h1>
            <p className="text-xs text-muted-foreground">Voice-Driven Information & Coordination</p>
          </div>
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full text-primary-foreground ${st.color}`}>
            {st.icon}
            {st.label}
          </span>
        </div>
      </header>

      {/* Main content */}
      <main className="container max-w-2xl mx-auto px-4 py-8 space-y-6">
        {/* Voice interaction card */}
        <motion.div
          className="clinical-card-elevated p-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="text-center mb-6">
            <h2 className="text-xl font-semibold text-foreground">How can I help you?</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Ask about medications, locate nearby clinics, or get medical information
            </p>
          </div>

          <MicRecorder
            status={status}
            onStatusChange={setStatus}
            onResponse={handleResponse}
            onError={handleError}
          />
        </motion.div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              className="flex items-center gap-3 p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
            >
              <AlertCircle className="w-5 h-5 shrink-0" />
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Response */}
        <AnimatePresence>
          {response && (
            <div className="space-y-4">
              <ResponseCard data={response} onShowMap={() => setShowMap(true)} />
              {response.audio_url && <AudioPlayer audioUrl={response.audio_url} />}
            </div>
          )}
        </AnimatePresence>
      </main>

      {/* Map popup */}
      <AnimatePresence>
        {showMap && response?.map_data && (
          <MapPopup data={response.map_data} onClose={() => setShowMap(false)} />
        )}
      </AnimatePresence>
    </div>
  );
};

export default Index;
