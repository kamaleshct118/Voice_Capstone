import { useRef, useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Play, Pause, Volume2 } from "lucide-react";

const API_BASE = "http://localhost:8000";

interface AudioPlayerProps {
  audioUrl: string;
}

/** Resolve relative /static/... URLs to the backend origin */
const resolveUrl = (url: string) =>
  url.startsWith("http") ? url : `${API_BASE}${url}`;

const AudioPlayer = ({ audioUrl }: AudioPlayerProps) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const src = resolveUrl(audioUrl);

  // Auto-play when a new audio URL arrives
  useEffect(() => {
    if (!audioRef.current) return;
    audioRef.current.load();
    audioRef.current
      .play()
      .then(() => setIsPlaying(true))
      .catch(() => {
        // Auto-play blocked by browser policy — user must click play
        setIsPlaying(false);
      });
  }, [src]);

  // Global stop listener from the ChatInput Stop button
  useEffect(() => {
    const handleGlobalStop = () => {
      if (audioRef.current && !audioRef.current.paused) {
        audioRef.current.pause();
        setIsPlaying(false);
      }
    };
    window.addEventListener("stop-audio-playback", handleGlobalStop);
    return () => window.removeEventListener("stop-audio-playback", handleGlobalStop);
  }, []);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleTimeUpdate = () => {
    if (!audioRef.current) return;
    const pct =
      (audioRef.current.currentTime / audioRef.current.duration) * 100;
    setProgress(isNaN(pct) ? 0 : pct);
  };

  const handleEnded = () => {
    setIsPlaying(false);
    setProgress(0);
  };

  return (
    <motion.div
      className="clinical-card p-4 flex items-center gap-4"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.2 }}
    >
      <button
        onClick={togglePlay}
        className="w-10 h-10 rounded-full bg-primary flex items-center justify-center shrink-0 hover:brightness-110 transition"
        aria-label={isPlaying ? "Pause" : "Play"}
      >
        {isPlaying ? (
          <Pause className="w-5 h-5 text-primary-foreground" />
        ) : (
          <Play className="w-5 h-5 text-primary-foreground ml-0.5" />
        )}
      </button>

      <div className="flex-1 space-y-1">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Volume2 className="w-4 h-4" />
          <span>Voice Response</span>
        </div>
        {/* Progress bar */}
        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-primary"
            style={{ width: `${progress}%` }}
            transition={{ duration: 0.1 }}
          />
        </div>
      </div>

      <audio
        ref={audioRef}
        src={src}
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleEnded}
        preload="auto"
      />
    </motion.div>
  );
};

export default AudioPlayer;
