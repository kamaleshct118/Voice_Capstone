import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Loader2, Send } from "lucide-react";
import type { ApiResponse, AppStatus } from "@/types/clinical";

interface ChatInputProps {
  onResponse: (data: ApiResponse, query: string) => void;
  onError: (msg: string) => void;
  status: AppStatus;
  onStatusChange: (status: AppStatus) => void;
}

const ChatInput = ({ onResponse, onError, status, onStatusChange }: ChatInputProps) => {
  const [text, setText] = useState("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const isRecording = status === "recording";
  const isProcessing = status === "processing";
  const disabled = isProcessing;

  const sendAudio = useCallback(async (blob: Blob) => {
    onStatusChange("processing");
    try {
      const formData = new FormData();
      formData.append("audio", blob, "recording.webm");
      const res = await fetch("http://localhost:8000/api/process", { method: "POST", body: formData });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data: ApiResponse = await res.json();
      onStatusChange("ready");
      onResponse(data, "[Voice message]");
    } catch (err: any) {
      onStatusChange("error");
      onError(err.message || "Failed to process audio");
    }
  }, [onResponse, onError, onStatusChange]);

  const sendText = useCallback(async () => {
    if (!text.trim()) return;
    const query = text.trim();
    setText("");
    onStatusChange("processing");
    try {
      const res = await fetch("http://localhost:8000/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: query }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data: ApiResponse = await res.json();
      onStatusChange("ready");
      onResponse(data, query);
    } catch (err: any) {
      onStatusChange("error");
      onError(err.message || "Failed to process text");
    }
  }, [text, onResponse, onError, onStatusChange]);

  const toggleRecording = useCallback(async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mediaRecorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        sendAudio(new Blob(chunksRef.current, { type: "audio/webm" }));
      };
      mediaRecorder.start();
      onStatusChange("recording");
    } catch {
      onError("Microphone access denied.");
      onStatusChange("error");
    }
  }, [isRecording, sendAudio, onError, onStatusChange]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendText();
    }
  };

  return (
    <div className="border-t border-border bg-card p-4">
      {/* Recording indicator */}
      <AnimatePresence>
        {isRecording && (
          <motion.div
            className="flex items-center justify-center gap-2 mb-3"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="flex items-end gap-0.5 h-5">
              {[...Array(5)].map((_, i) => (
                <motion.div
                  key={i}
                  className="w-1 rounded-full bg-destructive"
                  animate={{ height: [6, 18, 8, 20, 6] }}
                  transition={{ duration: 0.7, repeat: Infinity, delay: i * 0.08, ease: "easeInOut" }}
                />
              ))}
            </div>
            <span className="text-xs text-destructive font-medium">Recording...</span>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex items-end gap-2">
        {/* Mic button */}
        <button
          onClick={toggleRecording}
          disabled={disabled}
          className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all
            ${isRecording
              ? "bg-destructive animate-recording-pulse"
              : "bg-muted hover:bg-primary/10 text-muted-foreground hover:text-primary"
            } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
          aria-label={isRecording ? "Stop recording" : "Start recording"}
        >
          {isRecording ? <MicOff className="w-5 h-5 text-destructive-foreground" /> : <Mic className="w-5 h-5" />}
        </button>

        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder={isRecording ? "Recording voice..." : "Type your query or tap the mic..."}
            rows={1}
            className="w-full resize-none rounded-xl border border-border bg-background px-4 py-2.5 pr-12 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
          />
          {/* Send button */}
          <button
            onClick={sendText}
            disabled={disabled || !text.trim()}
            className="absolute right-2 bottom-1.5 p-1.5 rounded-lg bg-primary text-primary-foreground disabled:opacity-30 hover:brightness-110 transition"
            aria-label="Send"
          >
            {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
