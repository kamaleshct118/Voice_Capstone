import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Loader2, Send, Camera, MapPin, MapPinOff, Square } from "lucide-react";
import type { ApiResponse, AppStatus } from "@/types/clinical";

interface ChatInputProps {
  onResponse: (data: ApiResponse, query: string) => void;
  onError: (msg: string) => void;
  onAbort?: () => void;
  status: AppStatus;
  onStatusChange: (status: AppStatus) => void;
  sessionId: string;
}

const API = "http://localhost:8000/api";

type GeoStatus = "idle" | "requesting" | "granted" | "denied";

const ChatInput = ({ onResponse, onError, onAbort, status, onStatusChange, sessionId }: ChatInputProps) => {
  const [text, setText] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [userCoords, setUserCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [geoStatus, setGeoStatus] = useState<GeoStatus>("idle");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const watchIdRef = useRef<number | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // ── Stop everything mid-flight ──────────────────────────────────
  const stopAll = useCallback(() => {
    // Cancel the in-flight HTTP fetch
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    // Stop recording if active
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    // Stop any playing TTS audio
    window.dispatchEvent(new CustomEvent("stop-audio-playback"));

    onStatusChange("idle");
    onAbort?.();
  }, [onStatusChange, onAbort]);

  // ── Request geolocation from Chrome ────────────────────────────
  const requestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setGeoStatus("denied");
      return;
    }
    setGeoStatus("requesting");

    // Clear any previous watch
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
    }

    // Use watchPosition so coords stay fresh as user moves
    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        setUserCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setGeoStatus("granted");
      },
      (err) => {
        console.warn("Geolocation error:", err.message);
        setGeoStatus("denied");
        setUserCoords(null);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    );
  }, []);

  // Auto-request on mount
  useEffect(() => {
    requestLocation();
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  // Expose stopAll to parent via a stable ref effect
  useEffect(() => {
    // Nothing: stopAll is passed via onAbort prop when stop button is needed
  }, []);

  const isRecording = status === "recording";
  const isProcessing = status === "processing";
  const disabled = isProcessing;

  const handleStop = useCallback(() => {
    stopAll();
  }, [stopAll]);

  // ── Stream Reader & Audio Player ─────────────────────────────────
  const handleStreamResponse = async (res: Response, query: string, controller: AbortController) => {
    const reader = res.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let buffer = "";
    let audioCtx: AudioContext | null = null;
    let nextPlayTime = 0;

    window.addEventListener("stop-audio-playback", () => {
      if (audioCtx?.state !== "closed") audioCtx?.close();
    }, { once: true });

    try {
      while (true) {
        if (controller.signal.aborted) break;
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const msgStr = line.replace("data: ", "").trim();
          if (!msgStr) continue;

          try {
            const msg = JSON.parse(msgStr);
            if (msg.type === "metadata") {
              onStatusChange("ready");
              onResponse(msg.data, query);
            } else if (msg.type === "audio") {
              if (!audioCtx) {
                audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
                nextPlayTime = audioCtx.currentTime + 0.1; // small buffer
              }
              const binaryString = atob(msg.data);
              const len = binaryString.length;
              const bytes = new Uint8Array(len);
              for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);

              const floatData = new Float32Array(bytes.length / 2);
              const dataView = new DataView(bytes.buffer);
              for (let i = 0; i < floatData.length; i++) {
                floatData[i] = dataView.getInt16(i * 2, true) / 32768.0;
              }

              const audioBuffer = audioCtx.createBuffer(1, floatData.length, 24000);
              audioBuffer.getChannelData(0).set(floatData);

              const source = audioCtx.createBufferSource();
              source.buffer = audioBuffer;
              source.connect(audioCtx.destination);

              if (nextPlayTime < audioCtx.currentTime) {
                nextPlayTime = audioCtx.currentTime + 0.05;
              }
              source.start(nextPlayTime);
              nextPlayTime += audioBuffer.duration;
            }
          } catch (e) {
            console.error("Stream parse error", e);
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  };

  // ── Send audio ─────────────────────────────────────────────────
  const sendAudio = useCallback(
    async (blob: Blob) => {
      onStatusChange("processing");
      const controller = new AbortController();
      abortControllerRef.current = controller;
      try {
        const formData = new FormData();
        formData.append("audio", blob, "recording.webm");
        formData.append("session_id", sessionId);
        if (userCoords) {
          formData.append("lat", String(userCoords.lat));
          formData.append("lng", String(userCoords.lng));
        }
        const res = await fetch(`${API}/process`, {
          method: "POST",
          headers: { "x-streaming-audio": "true" },
          body: formData,
          signal: controller.signal
        });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);

        await handleStreamResponse(res, "[Voice message]", controller);
      } catch (err: any) {
        if (err.name === "AbortError") return; // silently cancel
        onStatusChange("error");
        onError(err.message || "Failed to process audio");
      } finally {
        abortControllerRef.current = null;
      }
    },
    [onResponse, onError, onStatusChange, sessionId, userCoords]
  );

  // ── Send text ──────────────────────────────────────────────────
  const sendText = useCallback(async () => {
    if (!text.trim()) return;
    const query = text.trim();
    setText("");
    onStatusChange("processing");
    const controller = new AbortController();
    abortControllerRef.current = controller;
    try {
      const payload: Record<string, any> = { text: query, session_id: sessionId };
      if (userCoords) {
        payload.lat = userCoords.lat;
        payload.lng = userCoords.lng;
      }
      const res = await fetch(`${API}/process`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-streaming-audio": "true"
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);

      await handleStreamResponse(res, query, controller);
    } catch (err: any) {
      if (err.name === "AbortError") return; // silently cancel
      onStatusChange("error");
      onError(err.message || "Failed to process text");
    } finally {
      abortControllerRef.current = null;
    }
  }, [text, onResponse, onError, onStatusChange, sessionId, userCoords]);

  // ── Send combined image+text or image only (medicine classifier) ──────────────────────────
  const sendImageRequest = useCallback(
    async () => {
      if (!selectedImage) return;
      onStatusChange("processing");
      const currentText = text.trim();
      setText("");
      setSelectedImage(null);
      try {
        const formData = new FormData();
        formData.append("mode", currentText ? "image+text" : "image");
        formData.append("image", selectedImage);
        if (currentText) {
          formData.append("medicine_name", currentText);
        }
        formData.append("session_id", sessionId);
        const res = await fetch(`${API}/classify-medicine`, {
          method: "POST",
          body: formData,
        });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        const raw = await res.json();
        // Normalise to ApiResponse shape
        const data: ApiResponse = {
          text_response: `${raw.medicine_name} — ${raw.purpose}`,
          audio_url: raw.audio_url,
          tool_type: "medicine_info",
          medicine_data: {
            medicine_name: raw.medicine_name,
            chemical_composition: raw.chemical_composition,
            drug_category: raw.drug_category,
            purpose: raw.purpose,
            basic_safety_notes: raw.basic_safety_notes,
            disclaimer: raw.disclaimer,
            input_mode: currentText ? "image+text" : "image",
          },
          session_id: raw.session_id,
        };
        onStatusChange("ready");
        onResponse(data, currentText ? `[Image] ${currentText}` : "[Medicine image]");
      } catch (err: any) {
        onStatusChange("error");
        onError(err.message || "Failed to classify medicine image");
      }
    },
    [selectedImage, text, onResponse, onError, onStatusChange, sessionId]
  );

  const handleSubmit = useCallback(() => {
    if (selectedImage) {
      sendImageRequest();
    } else {
      sendText();
    }
  }, [selectedImage, sendImageRequest, sendText]);

  // ── Toggle microphone recording ────────────────────────────────
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
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
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
      handleSubmit();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      e.target.value = "";
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

      {/* Location status badge */}
      <div className="flex items-center justify-end mb-2">
        {geoStatus === "requesting" && (
          <span className="inline-flex items-center gap-1.5 text-[11px] text-amber-400 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 animate-pulse">
            <MapPin className="w-3 h-3" />
            Getting location...
          </span>
        )}
        {geoStatus === "granted" && userCoords && (
          <span className="inline-flex items-center gap-1.5 text-[11px] text-emerald-400 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <MapPin className="w-3 h-3" />
            Location active
          </span>
        )}
        {geoStatus === "denied" && (
          <button
            onClick={requestLocation}
            className="inline-flex items-center gap-1.5 text-[11px] text-red-400 px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 transition-colors"
            title="Click to enable location for clinic search"
          >
            <MapPinOff className="w-3 h-3" />
            Enable Location
          </button>
        )}
      </div>

      {/* Image Preview Attachment */}
      <AnimatePresence>
        {selectedImage && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex items-center gap-2 mb-2 p-1.5 pr-2 w-max bg-muted/80 rounded-lg border border-border"
          >
            <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center shrink-0">
              <Camera className="w-4 h-4 text-primary" />
            </div>
            <span className="text-xs text-foreground font-medium truncate max-w-[150px] sm:max-w-[200px]">
              {selectedImage.name}
            </span>
            <button
              onClick={() => setSelectedImage(null)}
              className="ml-1 p-1 hover:bg-destructive/10 rounded-full text-muted-foreground hover:text-destructive transition-colors shrink-0"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input row: Mic + Camera + Textarea */}
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
          {isRecording ? (
            <MicOff className="w-5 h-5 text-destructive-foreground" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
        </button>

        {/* Image upload button — medicine classifier */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          title="Upload medicine image"
          className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all
              bg-muted hover:bg-violet-500/10 text-muted-foreground hover:text-violet-400
              ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
          aria-label="Upload medicine image"
        >
          <Camera className="w-5 h-5" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleFileChange}
        />

        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder={
              isRecording
                ? "Recording voice..."
                : "Type your query, tap 🎤 to speak, or 📷 for medicine image..."
            }
            rows={1}
            className="w-full resize-none rounded-xl border border-border bg-background px-4 py-2.5 pr-12 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
          />
          {/* Send or Stop button */}
          {isProcessing ? (
            <button
              onClick={handleStop}
              className="absolute right-2 bottom-1.5 py-1.5 px-3 rounded-lg bg-destructive text-destructive-foreground hover:bg-destructive/90 transition flex items-center gap-1.5"
              aria-label="Stop processing"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span className="text-xs font-bold leading-none">Stop</span>
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={(!text.trim() && !selectedImage) || isRecording}
              className="absolute right-2 bottom-1.5 p-1.5 rounded-lg bg-primary text-primary-foreground disabled:opacity-30 hover:brightness-110 transition"
              aria-label="Send"
            >
              <Send className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
