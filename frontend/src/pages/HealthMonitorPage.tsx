import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { HeartPulse, ArrowLeft, BarChart2, Loader2, MessageSquare } from "lucide-react";
import { useHealthMonitor } from "@/hooks/useHealthMonitor";
import HealthLogForm from "@/components/HealthLogForm";
import HealthTrendChart from "@/components/HealthTrendChart";
import HealthSummaryCard from "@/components/HealthSummaryCard";
import HealthChatPanel from "@/components/HealthChatPanel";

// Persist session ID in localStorage for continuity across page reloads
const getOrCreateSessionId = () => {
    const key = "health_monitor_session_id";
    let id = localStorage.getItem(key);
    if (!id) {
        id = crypto.randomUUID();
        localStorage.setItem(key, id);
    }
    return id;
};

const HealthMonitorPage = () => {
    const sessionId = useMemo(getOrCreateSessionId, []);
    const { logs, analysis, isLogging, isAnalyzing, error, logReading, getAnalysis } =
        useHealthMonitor(sessionId);

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-40">
                <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Link
                            to="/"
                            className="p-2 rounded-lg hover:bg-muted text-muted-foreground transition-colors"
                        >
                            <ArrowLeft className="w-4 h-4" />
                        </Link>
                        <div className="flex items-center gap-2">
                            <HeartPulse className="w-5 h-5 text-primary" />
                            <h1 className="font-bold text-foreground">Long-Term Health Monitor</h1>
                        </div>
                    </div>
                    <span className="text-xs text-muted-foreground hidden sm:block">
                        {logs.length} reading{logs.length !== 1 ? "s" : ""} logged this session
                    </span>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
                {/* Medical disclaimer banner */}
                <motion.div
                    className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-start gap-2"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <span className="text-amber-400 font-bold shrink-0">⚠️</span>
                    <span>
                        <strong>Medical Disclaimer:</strong> This tool is for personal health tracking only.
                        It does not constitute medical advice, diagnosis, or treatment.
                        Always consult a qualified healthcare provider for medical decisions.
                    </span>
                </motion.div>

                {/* Error */}
                <AnimatePresence>
                    {error && (
                        <motion.div
                            className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            {error}
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* ── ROW 1: Log form + Chart ── */}
                <div className="grid lg:grid-cols-2 gap-6">
                    {/* Log Form */}
                    <div className="rounded-2xl border border-border bg-card p-5">
                        <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                            <HeartPulse className="w-4 h-4 text-primary" />
                            Log a Reading
                        </h2>
                        <HealthLogForm onSubmit={logReading} isLoading={isLogging} />
                    </div>

                    {/* Chart + Analyze */}
                    <div className="space-y-4">
                        <div className="rounded-2xl border border-border bg-card p-5">
                            <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                                <BarChart2 className="w-4 h-4 text-primary" />
                                Health Trends
                            </h2>
                            <HealthTrendChart logs={logs} />
                        </div>

                        {/* Analyze button */}
                        <button
                            onClick={getAnalysis}
                            disabled={isAnalyzing || logs.length === 0}
                            className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:brightness-110 transition disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {isAnalyzing ? (
                                <><Loader2 className="w-4 h-4 animate-spin" /> Analysing trends...</>
                            ) : (
                                <>Analyse My Health Trends</>
                            )}
                        </button>

                        {/* Analysis card */}
                        <AnimatePresence>
                            {analysis && (
                                <motion.div
                                    className="rounded-2xl border border-border bg-card p-5"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0 }}
                                >
                                    <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                                        <HeartPulse className="w-4 h-4 text-primary" />
                                        AI Health Analysis
                                    </h2>
                                    <HealthSummaryCard analysis={analysis} />
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>

                {/* ── ROW 2: Health Insights Chat (full width) ── */}
                <div>
                    <div className="flex items-center gap-2 mb-3">
                        <MessageSquare className="w-4 h-4 text-primary" />
                        <h2 className="font-semibold text-foreground">
                            Health Insights Chat
                        </h2>
                        <span className="text-xs text-muted-foreground ml-1">
                            — Ask the AI anything about your logged readings
                        </span>
                    </div>
                    <HealthChatPanel sessionId={sessionId} hasLogs={logs.length > 0} />
                </div>
            </div>
        </div>
    );
};

export default HealthMonitorPage;
