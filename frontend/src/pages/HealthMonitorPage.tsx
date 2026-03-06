import { useMemo } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
    HeartPulse, ArrowLeft, BarChart2, Loader2, MessageSquare,
    CheckSquare, ClipboardList, Activity
} from "lucide-react";
import { useHealthMonitor } from "@/hooks/useHealthMonitor";
import { getOrCreateHealthSession } from "@/utils/session";
import HealthLogForm from "@/components/HealthLogForm";
import HealthTrendChart from "@/components/HealthTrendChart";
import HealthSummaryCard from "@/components/HealthSummaryCard";
import HealthChatPanel from "@/components/HealthChatPanel";

const HealthMonitorPage = () => {
    const sessionId = useMemo(getOrCreateHealthSession, []);
    const { logs, analysis, isLogging, isAnalyzing, error, logReading, getAnalysis } =
        useHealthMonitor(sessionId);

    const checklist: string[] = analysis?.daily_checklist ?? [];

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
                            <h1 className="font-bold text-foreground">Health Monitor Dashboard</h1>
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

                {/* ── ROW 1: Log form + Chart ─────────────────────────── */}
                <div className="grid lg:grid-cols-2 gap-6">
                    {/* Log Form */}
                    <div className="rounded-2xl border border-border bg-card p-5">
                        <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                            <HeartPulse className="w-4 h-4 text-primary" />
                            Log a Reading
                        </h2>
                        <HealthLogForm onSubmit={logReading} isLoading={isLogging} />
                    </div>

                    {/* Chart */}
                    <div className="rounded-2xl border border-border bg-card p-5">
                        <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                            <BarChart2 className="w-4 h-4 text-primary" />
                            Health Trends
                        </h2>
                        <HealthTrendChart logs={logs} />
                    </div>
                </div>

                {/* ── ROW 2: Analyze button + Analysis card ──────────── */}
                <div className="space-y-4">
                    <button
                        onClick={getAnalysis}
                        disabled={isAnalyzing || logs.length === 0}
                        className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:brightness-110 transition disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        {isAnalyzing ? (
                            <><Loader2 className="w-4 h-4 animate-spin" /> Analysing trends...</>
                        ) : (
                            <><Activity className="w-4 h-4" /> Analyse My Health Trends</>
                        )}
                    </button>

                    <AnimatePresence>
                        {analysis && (
                            <motion.div
                                className="grid lg:grid-cols-2 gap-6"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0 }}
                            >
                                {/* AI Analysis Summary */}
                                <div className="rounded-2xl border border-border bg-card p-5">
                                    <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                                        <HeartPulse className="w-4 h-4 text-primary" />
                                        AI Health Analysis
                                    </h2>
                                    <HealthSummaryCard analysis={analysis} />
                                </div>

                                {/* Daily Checklist */}
                                {checklist.length > 0 && (
                                    <motion.div
                                        className="rounded-2xl border border-border bg-card p-5"
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: 0.15 }}
                                    >
                                        <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                                            <CheckSquare className="w-4 h-4 text-emerald-400" />
                                            Daily Checklist
                                            <span className="text-xs text-muted-foreground font-normal ml-1">
                                                — AI-generated for you
                                            </span>
                                        </h2>
                                        <ul className="space-y-2">
                                            {checklist.map((item, i) => (
                                                <motion.li
                                                    key={i}
                                                    className="flex items-start gap-3 p-2.5 rounded-xl bg-emerald-500/5 border border-emerald-500/15 text-sm text-foreground"
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: i * 0.07 }}
                                                >
                                                    <span className="mt-0.5 w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0 text-emerald-400 font-bold text-xs">
                                                        {i + 1}
                                                    </span>
                                                    <span>{item}</span>
                                                </motion.li>
                                            ))}
                                        </ul>
                                    </motion.div>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* ── ROW 3: Health Insights Chat (full width) ─────────── */}
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
