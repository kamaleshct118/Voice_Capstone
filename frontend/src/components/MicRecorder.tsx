import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Loader2 } from "lucide-react";
import type { ApiResponse, AppStatus } from "@/types/clinical";

interface MicRecorderProps {
  onResponse: (data: ApiResponse) => void;
  onError: (msg: string) => void;
  status: AppStatus;
  onStatusChange: (status: AppStatus) => void;
}

const MicRecorder = ({ onResponse, onError, status, onStatusChange }: MicRecorderProps) => {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        onStatusChange("processing");

        try {
          const formData = new FormData();
          formData.append("audio", audioBlob, "recording.webm");

          const res = await fetch("http://localhost:8000/api/process", {
            method: "POST",
            body: formData,
          });

          if (!res.ok) throw new Error(`Server error: ${res.status}`);
          const data: ApiResponse = await res.json();
          onStatusChange("ready");
          onResponse(data);
        } catch (err: any) {
          onStatusChange("error");
          onError(err.message || "Failed to process audio");
        }
      };

      mediaRecorder.start();
      onStatusChange("recording");
    } catch {
      onError("Microphone access denied. Please allow microphone permissions.");
      onStatusChange("error");
    }
  }, [onResponse, onError, onStatusChange]);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
  }, []);

  const handleClick = () => {
    if (status === "recording") {
      stopRecording();
    } else if (status === "idle" || status === "ready" || status === "error") {
      startRecording();
    }
  };

  const isRecording = status === "recording";
  const isProcessing = status === "processing";

  return (
    <div className="flex flex-col items-center gap-6">
      <motion.button
        onClick={handleClick}
        disabled={isProcessing}
        className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-colors focus:outline-none focus-visible:ring-4 focus-visible:ring-ring
          ${isRecording 
            ? "bg-destructive animate-recording-pulse" 
            : isProcessing 
              ? "bg-muted cursor-not-allowed" 
              : "bg-primary animate-mic-glow hover:brightness-110"
          }`}
        whileTap={!isProcessing ? { scale: 0.93 } : {}}
        aria-label={isRecording ? "Stop recording" : "Start recording"}
      >
        <AnimatePresence mode="wait">
          {isProcessing ? (
            <motion.div key="loader" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <Loader2 className="w-10 h-10 text-muted-foreground animate-spin" />
            </motion.div>
          ) : isRecording ? (
            <motion.div key="stop" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
              <MicOff className="w-10 h-10 text-destructive-foreground" />
            </motion.div>
          ) : (
            <motion.div key="mic" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
              <Mic className="w-10 h-10 text-primary-foreground" />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      <p className="text-sm text-muted-foreground">
        {isRecording
          ? "Listening... Tap to stop"
          : isProcessing
            ? "Processing your request..."
            : "Tap to speak"}
      </p>

      {/* Waveform bars when recording */}
      <AnimatePresence>
        {isRecording && (
          <motion.div
            className="flex items-end gap-1 h-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {[...Array(7)].map((_, i) => (
              <motion.div
                key={i}
                className="w-1 rounded-full bg-destructive"
                animate={{ height: [8, 24, 12, 28, 8] }}
                transition={{
                  duration: 0.8,
                  repeat: Infinity,
                  delay: i * 0.1,
                  ease: "easeInOut",
                }}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MicRecorder;
