import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    MessageSquare, Send, Loader2, Bot, User, Volume2, Sparkles,
} from "lucide-react";

export interface HealthChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    audio_url?: string;
    timestamp: Date;
}

interface HealthChatPanelProps {
    sessionId: string;
    hasLogs: boolean;
}

const API = "http://localhost:8000/api";

const SUGGESTED_QUESTIONS = [
    "How has my blood pressure been trending?",
    "Is my blood sugar in a normal range?",
    "What does my recent data say about my heart health?",
    "What lifestyle changes should I consider based on my readings?",
    "Are my numbers improving over time?",
];

const HealthChatPanel = ({ sessionId, hasLogs }: HealthChatPanelProps) => {
    const [messages, setMessages] = useState<HealthChatMessage[]>([
        {
            id: "welcome",
            role: "assistant",
            content: hasLogs
                ? "Hi! I have access to your logged health readings. Ask me anything about your data — trends, patterns, recommendations, or what your numbers mean."
                : "Hi! Log some health readings first, then I can analyze your data and answer questions about your trends, BP, sugar levels, weight and more.",
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [playingAudio, setPlayingAudio] = useState<string | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async (text: string) => {
        if (!text.trim() || isLoading) return;

        const userMsg: HealthChatMessage = {
            id: crypto.randomUUID(),
            role: "user",
            content: text.trim(),
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsLoading(true);

        try {
            const res = await fetch(`${API}/health-chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionId, message: text.trim() }),
            });

            if (!res.ok) throw new Error(`Server error: ${res.status}`);
            const data = await res.json();

            const aiMsg: HealthChatMessage = {
                id: crypto.randomUUID(),
                role: "assistant",
                content: data.response,
                audio_url: data.audio_url,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, aiMsg]);
        } catch (err: any) {
            setMessages((prev) => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: "assistant",
                    content: "Sorry, I couldn't get a response right now. Please try again.",
                    timestamp: new Date(),
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const playAudio = (url: string) => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current = null;
        }
        const audio = new Audio(`http://localhost:8000${url}`);
        audioRef.current = audio;
        setPlayingAudio(url);
        audio.play();
        audio.onended = () => setPlayingAudio(null);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input);
        }
    };

    return (
        <div className="rounded-2xl border border-border bg-card flex flex-col h-[520px]">
            {/* Header */}
            <div className="flex items-center gap-2.5 px-5 py-4 border-b border-border shrink-0">
                <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center">
                    <MessageSquare className="w-4 h-4 text-primary" />
                </div>
                <div>
                    <h2 className="font-semibold text-foreground text-sm">Health Insights Chat</h2>
                    <p className="text-xs text-muted-foreground">
                        Ask the AI about your logged health data
                    </p>
                </div>
                <div className="ml-auto flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary/10 text-xs text-primary font-medium">
                    <Sparkles className="w-3 h-3" />
                    AI-Powered
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
                <AnimatePresence initial={false}>
                    {messages.map((msg) => (
                        <motion.div
                            key={msg.id}
                            className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.25 }}
                        >
                            {/* Avatar */}
                            <div
                                className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 z-10 ${msg.role === "assistant"
                                    ? "bg-primary/15 text-primary"
                                    : "bg-muted text-muted-foreground"
                                    }`}
                            >
                                {msg.role === "assistant" ? (
                                    <Bot className="w-3.5 h-3.5" />
                                ) : (
                                    <User className="w-3.5 h-3.5" />
                                )}
                            </div>

                            {/* Bubble Context Container */}
                            <div className={`w-full max-w-[85%] space-y-1.5 ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col`}>
                                <div
                                    className={`px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed ${msg.role === "user"
                                        ? "bg-primary text-primary-foreground rounded-tr-sm"
                                        : "bg-muted text-foreground rounded-tl-sm w-full"
                                        }`}
                                >
                                    <div className="whitespace-pre-wrap">{msg.content}</div>
                                </div>

                                {/* Audio player for assistant messages */}
                                {msg.audio_url && (
                                    <button
                                        onClick={() => playAudio(msg.audio_url!)}
                                        className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full transition-all border ${playingAudio === msg.audio_url
                                            ? "bg-primary/20 text-primary border-primary/30 animate-pulse"
                                            : "border-border text-muted-foreground hover:text-primary hover:border-primary/30"
                                            }`}
                                    >
                                        <Volume2 className="w-3 h-3" />
                                        {playingAudio === msg.audio_url ? "Playing..." : "Listen"}
                                    </button>
                                )}

                                <span className="text-[10px] text-muted-foreground px-1">
                                    {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                                </span>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {/* Typing indicator */}
                {isLoading && (
                    <motion.div
                        className="flex gap-2.5"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                    >
                        <div className="w-7 h-7 rounded-full bg-primary/15 flex items-center justify-center shrink-0">
                            <Bot className="w-3.5 h-3.5 text-primary" />
                        </div>
                        <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-muted flex items-center gap-1.5">
                            {[0, 1, 2].map((i) => (
                                <motion.div
                                    key={i}
                                    className="w-1.5 h-1.5 rounded-full bg-muted-foreground"
                                    animate={{ opacity: [0.3, 1, 0.3] }}
                                    transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                                />
                            ))}
                        </div>
                    </motion.div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* Suggested questions */}
            {messages.length <= 1 && hasLogs && (
                <div className="px-4 pb-2 shrink-0">
                    <p className="text-xs text-muted-foreground mb-2">Suggested questions:</p>
                    <div className="flex flex-wrap gap-1.5">
                        {SUGGESTED_QUESTIONS.map((q) => (
                            <button
                                key={q}
                                onClick={() => sendMessage(q)}
                                className="text-xs px-2.5 py-1 rounded-full border border-border text-muted-foreground hover:text-primary hover:border-primary/40 transition-all"
                            >
                                {q}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Input */}
            <div className="px-4 py-3 border-t border-border shrink-0">
                <div className="flex items-end gap-2">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isLoading}
                        placeholder="Ask about your BP trends, sugar levels, mood patterns..."
                        rows={1}
                        className="flex-1 resize-none rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                    />
                    <button
                        onClick={() => sendMessage(input)}
                        disabled={isLoading || !input.trim()}
                        className="shrink-0 w-10 h-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-40 hover:brightness-110 transition"
                    >
                        {isLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                            <Send className="w-4 h-4" />
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default HealthChatPanel;
