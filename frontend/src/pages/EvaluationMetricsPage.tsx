import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowLeft, Activity, Server, Zap, Mic, Volume2 } from "lucide-react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    LineChart,
    Line,
    AreaChart,
    Area,
} from "recharts";

const COLORS = {
    stt: "#0ea5e9",      // Cyan
    llm: "#eab308",      // Yellow
    tts: "#22c55e",      // Green
    tool: "#d946ef",     // Magenta
    intent: "#3b82f6",   // Blue
    total: "#f87171",    // Red
};

interface MetricLog {
    session_id: string;
    stt_ms: number;
    intent_ms: number;
    tool_ms: number;
    llm_ms: number;
    tts_ms: number;
    total_ms: number;
    cache_hit: boolean;
    timestamp: string;
}

export default function EvaluationMetricsPage() {
    const [metrics, setMetrics] = useState<MetricLog[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetch("http://localhost:8000/api/metrics")
            .then((r) => r.json())
            .then((data) => {
                // Format for Recharts, sort oldest to newest
                const formatted = (data.metrics || []).reverse().map((m: any, i: number) => ({
                    name: `Req ${i + 1}`,
                    stt_ms: m.stt_ms,
                    intent_ms: m.intent_ms,
                    llm_ms: m.llm_ms,
                    tool_ms: m.tool_ms,
                    tts_ms: m.tts_ms,
                    total_ms: m.total_ms,
                    cache_hit: m.cache_hit ? 1 : 0,
                }));
                setMetrics(formatted);
                setIsLoading(false);
            })
            .catch((e) => {
                console.error(e);
                setIsLoading(false);
            });
    }, []);

    // Mock data for hard-to-track acoustic properties (as requested by user architecture)
    const mockConfidence = [
        { name: "0-50%", count: 2 },
        { name: "50-80%", count: 15 },
        { name: "80-90%", count: 35 },
        { name: "90-100%", count: 120 },
    ];

    return (
        <div className="min-h-screen bg-background text-foreground flex flex-col">
            {/* Header */}
            <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-40">
                <div className="flex items-center px-4 h-14 gap-3 max-w-7xl mx-auto w-full">
                    <Link
                        to="/assistant"
                        className="p-2 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <h1 className="text-lg font-bold flex items-center gap-2">
                        <Activity className="w-5 h-5 text-primary" />
                        Live Evaluation Metrics
                    </h1>
                </div>
            </header>

            <main className="flex-1 overflow-y-auto p-4 md:p-8">
                <div className="max-w-7xl mx-auto space-y-8">

                    <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-end">
                        <div>
                            <h2 className="text-3xl font-black text-foreground tracking-tight">System Performance Core</h2>
                            <p className="text-muted-foreground mt-1 text-sm max-w-2xl">
                                Real-time latency breakdown across the VAD → STT → LLM → MCP → TTS pipeline.
                                Monitoring Dr. Elena's multimodal backend execution times.
                            </p>
                        </div>
                        {metrics.length > 0 && (
                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-sm font-bold">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                                </span>
                                {metrics.length} LIVE SESSIONS LOGGED
                            </div>
                        )}
                    </div>

                    {isLoading ? (
                        <div className="h-64 flex items-center justify-center">
                            <Activity className="w-8 h-8 text-primary animate-pulse" />
                        </div>
                    ) : metrics.length === 0 ? (
                        <div className="h-64 flex items-center justify-center text-muted-foreground bg-card rounded-2xl border border-border">
                            No live metrics recorded yet. Make some voice queries first!
                        </div>
                    ) : (
                        <div className="space-y-6">

                            {/* 1. LATENCY METRICS (CRITICAL) */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
                                className="grid gap-6 grid-cols-1 lg:grid-cols-2"
                            >
                                {/* Stacked Bar for breakdown */}
                                <div className="p-5 rounded-2xl border border-border bg-card shadow-sm col-span-1 lg:col-span-2">
                                    <div className="flex items-center gap-2 mb-6">
                                        <div className="p-2 bg-primary/10 rounded-lg">
                                            <Zap className="w-5 h-5 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-bold">Pipeline Latency Breakdown (Stacked)</h3>
                                            <p className="text-xs text-muted-foreground">End-to-end execution time segmented by AI service</p>
                                        </div>
                                    </div>
                                    <div className="h-[300px] w-full">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={metrics} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                                                <XAxis dataKey="name" stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                                                <YAxis stroke="#888" fontSize={12} tickLine={false} axisLine={false} unit="ms" />
                                                <Tooltip
                                                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                                    contentStyle={{ borderRadius: '12px', border: '1px solid #333', background: '#111' }}
                                                />
                                                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                                                <Bar dataKey="stt_ms" stackId="a" fill={COLORS.stt} name="Whisper STT" radius={[0, 0, 4, 4]} animationDuration={1500} />
                                                <Bar dataKey="intent_ms" stackId="a" fill={COLORS.intent} name="Intent Classifier" animationDuration={1500} />
                                                <Bar dataKey="tool_ms" stackId="a" fill={COLORS.tool} name="MCP Tools" animationDuration={1500} />
                                                <Bar dataKey="llm_ms" stackId="a" fill={COLORS.llm} name="Gemini Gen" animationDuration={1500} />
                                                <Bar dataKey="tts_ms" stackId="a" fill={COLORS.tts} name="Kokoro TTS" radius={[4, 4, 0, 0]} animationDuration={1500} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                {/* Total End to End Flow */}
                                <div className="p-5 rounded-2xl border border-border bg-card shadow-sm">
                                    <div className="flex items-center gap-2 mb-6">
                                        <div className="p-2 bg-red-500/10 rounded-lg">
                                            <Server className="w-5 h-5 text-red-500" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-bold">End-to-End Latency Trend</h3>
                                            <p className="text-xs text-muted-foreground">Total Audio-in to Audio-out Wall Time</p>
                                        </div>
                                    </div>
                                    <div className="h-[250px] w-full">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart data={metrics} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                                <defs>
                                                    <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor={COLORS.total} stopOpacity={0.3} />
                                                        <stop offset="95%" stopColor={COLORS.total} stopOpacity={0} />
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                                                <XAxis dataKey="name" stroke="#888" fontSize={10} tickLine={false} axisLine={false} />
                                                <YAxis stroke="#888" fontSize={10} tickLine={false} axisLine={false} />
                                                <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid #333', background: '#111' }} />
                                                <Area type="monotone" dataKey="total_ms" stroke={COLORS.total} strokeWidth={3} fillOpacity={1} fill="url(#colorTotal)" animationDuration={2000} />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                <div className="p-5 rounded-2xl border border-border bg-card shadow-sm">
                                    <div className="flex items-center gap-2 mb-6">
                                        <div className="p-2 bg-cyan-500/10 rounded-lg">
                                            <Mic className="w-5 h-5 text-cyan-500" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-bold">STT Whisper Latency (Local GPU)</h3>
                                            <p className="text-xs text-muted-foreground">Raw translation inference speed</p>
                                        </div>
                                    </div>
                                    <div className="h-[250px] w-full">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={metrics} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                                                <XAxis dataKey="name" stroke="#888" fontSize={10} tickLine={false} axisLine={false} />
                                                <YAxis stroke="#888" fontSize={10} tickLine={false} axisLine={false} />
                                                <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid #333', background: '#111' }} />
                                                <Line type="monotone" dataKey="stt_ms" stroke={COLORS.stt} strokeWidth={3} dot={{ r: 4, fill: COLORS.stt, strokeWidth: 0 }} animationDuration={1500} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                            </motion.div>

                            {/* 2. SPEECH CONFIDENCE & TTS STABILITY (Mocked for Visual Completeness per request) */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}
                                className="grid gap-6 grid-cols-1 lg:grid-cols-2"
                            >
                                <div className="p-5 rounded-2xl border border-border bg-card shadow-sm">
                                    <div className="flex items-center gap-2 mb-6">
                                        <div className="p-2 bg-green-500/10 rounded-lg">
                                            <Volume2 className="w-5 h-5 text-green-500" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-bold">Kokoro TTS Generation Time</h3>
                                            <p className="text-xs text-muted-foreground">Audio synthesis stability</p>
                                        </div>
                                    </div>
                                    <div className="h-[200px] w-full">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={metrics} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                                                <XAxis dataKey="name" stroke="#888" fontSize={10} tickLine={false} axisLine={false} />
                                                <YAxis stroke="#888" fontSize={10} tickLine={false} axisLine={false} />
                                                <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid #333', background: '#111' }} />
                                                <Line type="stepAfter" dataKey="tts_ms" stroke={COLORS.tts} strokeWidth={3} dot={false} animationDuration={1500} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                <div className="p-5 rounded-2xl border border-border bg-card shadow-sm flex flex-col justify-between">
                                    <div className="flex items-center gap-2 mb-2">
                                        <div className="p-2 bg-indigo-500/10 rounded-lg">
                                            <Activity className="w-5 h-5 text-indigo-500" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-bold">Other Key Metrics & Cache Hits</h3>
                                            <p className="text-xs text-muted-foreground">Tool distribution and Redis DB1 Hits</p>
                                        </div>
                                    </div>

                                    <div className="flex-1 flex flex-col justify-center gap-6">
                                        <div className="p-4 rounded-xl bg-background border border-border flex items-center justify-between">
                                            <div>
                                                <p className="text-sm font-medium text-muted-foreground">Redis DB1 (CAG) Cache Hits</p>
                                                <p className="text-xs text-muted-foreground mt-0.5">Avoids expensive Gemini API calls</p>
                                            </div>
                                            <div className="text-3xl font-black text-emerald-400">
                                                {((metrics.filter(m => m.cache_hit).length / Math.max(1, metrics.length)) * 100).toFixed(0)}%
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="p-3 bg-muted rounded-xl">
                                                <p className="text-xs text-muted-foreground">Avg Word Error Rate (WER)</p>
                                                <p className="text-xl font-bold mt-1 text-foreground">3.4%</p>
                                            </div>
                                            <div className="p-3 bg-muted rounded-xl">
                                                <p className="text-xs text-muted-foreground">Avg TTS Prosody Stability</p>
                                                <p className="text-xl font-bold mt-1 text-foreground">98.1%</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                            </motion.div>

                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
