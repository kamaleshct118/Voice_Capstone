import { useMemo, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
    HeartPulse, ArrowLeft, BarChart2, Loader2, MessageSquare,
    CheckSquare, ClipboardList, Activity, Home
} from "lucide-react";
import { useHealthMonitor } from "@/hooks/useHealthMonitor";
import { getOrCreateHealthSession } from "@/utils/session";
import HealthLogForm from "@/components/HealthLogForm";
import HealthTrendChart from "@/components/HealthTrendChart";
import HealthSummaryCard from "@/components/HealthSummaryCard";
import HealthChatPanel from "@/components/HealthChatPanel";
import HealthReportModal from "@/components/HealthReportModal";
import type { MedicalReportData, HealthLogEntry } from "@/types/clinical";
import { Plus, Trash2, Stethoscope, Save, History } from "lucide-react";

const CHRONIC_DISEASES = [
    "Diabetes Type 1", "Diabetes Type 2", "Hypertension",
    "Asthma", "COPD", "Heart Disease", "Thyroid Disorder",
    "Arthritis", "Obesity", "None / General Monitoring"
];

const HealthMonitorPage = () => {
    const sessionId = useMemo(getOrCreateHealthSession, []);
    const [chronicDisease, setChronicDisease] = useState<string | null>(() => {
        return localStorage.getItem(`chronic_disease_${sessionId}`);
    });
    const [selectedDisease, setSelectedDisease] = useState("");
    const [customDisease, setCustomDisease] = useState("");
    const [showCustomInput, setShowCustomInput] = useState(false);

    const [doctorPoint, setDoctorPoint] = useState("");
    const [doctorAdvices, setDoctorAdvices] = useState<{ content: string, timestamp: string }[]>([]);
    const [isSavingAdvice, setIsSavingAdvice] = useState(false);

    const {
        logs, analysis, isLogging, isAnalyzing, error, clearError,
        logReading, getAnalysis, getReport, deleteLogsByDisease,
        addDoctorAdvice, getDoctorAdvice
    } = useHealthMonitor(sessionId, chronicDisease);

    const [report, setReport] = useState<MedicalReportData | null>(null);
    const [isGeneratingReport, setIsGeneratingReport] = useState(false);
    const [isReportOpen, setIsReportOpen] = useState(false);

    const checklist: string[] = analysis?.daily_checklist ?? [];

    useEffect(() => {
        if (chronicDisease) {
            fetchAdvice(chronicDisease);
        }
    }, [chronicDisease, sessionId]);

    // Auto-dismiss errors after 4 seconds
    useEffect(() => {
        if (!error) return;
        const t = setTimeout(() => clearError(), 4000);
        return () => clearTimeout(t);
    }, [error, clearError]);

    const handleSetDisease = (disease: string) => {
        if (!disease) return;
        localStorage.setItem(`chronic_disease_${sessionId}`, disease);
        setChronicDisease(disease);
        // Also fetch doctor advice for this disease
        fetchAdvice(disease);
    };

    const fetchAdvice = async (disease: string) => {
        const advice = await getDoctorAdvice(disease);
        setDoctorAdvices(advice);
    };

    const handleAddAdvice = async () => {
        if (!doctorPoint.trim() || !chronicDisease) return;
        setIsSavingAdvice(true);
        const success = await addDoctorAdvice(chronicDisease, doctorPoint);
        if (success) {
            setDoctorPoint("");
            fetchAdvice(chronicDisease);
        }
        setIsSavingAdvice(false);
    };

    const handleDeleteDiseaseLog = async () => {
        if (!chronicDisease) return;
        if (window.confirm(`Are you sure you want to delete the ENTIRE database of logs for ${chronicDisease}? This cannot be undone.`)) {
            const success = await deleteLogsByDisease(chronicDisease);
            if (success) {
                alert(`Logs for ${chronicDisease} have been cleared.`);
            }
        }
    };

    const handleGenerateReport = async () => {
        setIsGeneratingReport(true);
        try {
            const data = await getReport(chronicDisease || undefined);
            if (data) {
                setReport(data);
                setIsReportOpen(true);
            }
        } finally {
            setIsGeneratingReport(false);
        }
    };

    if (!chronicDisease) {
        return (
            <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="max-w-md w-full rounded-2xl border border-border bg-card p-6 shadow-xl relative"
                >
                    <Link
                        to="/"
                        className="absolute top-4 right-4 p-2 rounded-lg hover:bg-muted text-muted-foreground transition-colors"
                        title="Go to Home"
                    >
                        <Home className="w-5 h-5" />
                    </Link>

                    <div className="flex items-center justify-center mb-6">
                        <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                            <HeartPulse className="w-6 h-6 text-primary" />
                        </div>
                    </div>
                    <h2 className="text-2xl font-bold text-center mb-2">Welcome to Health Monitor</h2>
                    <p className="text-muted-foreground text-center text-sm mb-6">
                        To personalize your AI analysis and tracking, please select your primary health focus or chronic condition.
                    </p>

                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-2">
                            {CHRONIC_DISEASES.map(d => (
                                <button
                                    key={d}
                                    onClick={() => {
                                        setSelectedDisease(d);
                                        setShowCustomInput(false);
                                    }}
                                    className={`p-3 rounded-xl border text-xs font-medium transition-all text-center ${selectedDisease === d && !showCustomInput
                                        ? "bg-primary text-primary-foreground border-primary shadow-lg shadow-primary/20"
                                        : "bg-card border-border hover:border-primary/50 text-muted-foreground"
                                        }`}
                                >
                                    {d}
                                </button>
                            ))}
                            <button
                                onClick={() => {
                                    setShowCustomInput(true);
                                    setSelectedDisease("");
                                }}
                                className={`p-3 rounded-xl border border-dashed text-xs font-medium transition-all text-center flex items-center justify-center gap-2 ${showCustomInput
                                    ? "bg-primary text-primary-foreground border-primary shadow-lg shadow-primary/20"
                                    : "bg-card border-border hover:border-primary/50 text-muted-foreground"
                                    }`}
                            >
                                <Plus className="w-4 h-4" /> Create New
                            </button>
                        </div>

                        {showCustomInput && (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="space-y-2 p-3 rounded-xl bg-primary/5 border border-primary/10"
                            >
                                <label className="text-[10px] font-bold text-primary uppercase tracking-wider">New Disease Database</label>
                                <input
                                    type="text"
                                    value={customDisease}
                                    onChange={(e) => setCustomDisease(e.target.value)}
                                    placeholder="Enter disease name..."
                                    className="w-full bg-background border border-border px-3 py-2 rounded-lg text-sm focus:ring-2 focus:ring-primary outline-none"
                                />
                            </motion.div>
                        )}

                        <button
                            onClick={() => handleSetDisease(showCustomInput ? customDisease : selectedDisease)}
                            disabled={showCustomInput ? !customDisease.trim() : !selectedDisease}
                            className="w-full py-3.5 rounded-xl bg-primary text-primary-foreground font-bold text-sm hover:brightness-110 shadow-lg shadow-primary/25 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                        >
                            <History className="w-4 h-4" />
                            {showCustomInput ? "Initialize New Database" : "Access Database"}
                        </button>
                    </div>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-40">
                <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link
                            to="/"
                            className="p-2 rounded-lg hover:bg-muted text-muted-foreground transition-colors flex items-center gap-2 text-xs font-semibold border border-transparent hover:border-border"
                            title="Back to Home"
                        >
                            <Home className="w-4 h-4" /> Home
                        </Link>
                        <div className="h-4 w-[1px] bg-border mx-1" />
                        <button
                            onClick={() => setChronicDisease(null)}
                            className="p-2 rounded-lg hover:bg-muted text-muted-foreground transition-colors flex items-center gap-2 text-xs font-semibold border border-transparent hover:border-border"
                        >
                            <ArrowLeft className="w-4 h-4" /> Switch Condition
                        </button>
                        <div className="h-4 w-[1px] bg-border mx-1" />
                        <div className="flex items-center gap-2">
                            <HeartPulse className="w-5 h-5 text-primary" />
                            <h1 className="font-bold text-foreground">Health Monitor Database</h1>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={handleDeleteDiseaseLog}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-destructive/10 text-destructive border border-destructive/20 text-[10px] font-bold hover:bg-destructive/20 transition uppercase tracking-tighter"
                        >
                            <Trash2 className="w-3.5 h-3.5" /> Clear All Logs
                        </button>
                        <span className="text-xs text-muted-foreground hidden lg:block">
                            {logs.length} reading{logs.length !== 1 ? "s" : ""} logged
                        </span>
                    </div>
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

                {/* Error - auto-dismisses after 4s */}
                <AnimatePresence>
                    {error && (
                        <motion.div
                            className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center justify-between gap-3"
                            initial={{ opacity: 0, y: -6 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                        >
                            <span>{error}</span>
                            <button
                                onClick={clearError}
                                className="shrink-0 text-xs font-bold opacity-70 hover:opacity-100"
                            >
                                ✕
                            </button>
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
                            <span className="ml-auto text-xs px-2 py-1 bg-primary/10 text-primary rounded-full">
                                {chronicDisease}
                            </span>
                        </h2>
                        <HealthLogForm onSubmit={(entry) => logReading({ ...entry, chronic_disease: chronicDisease })} isLoading={isLogging} />
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
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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

                        <button
                            onClick={handleGenerateReport}
                            disabled={isGeneratingReport || logs.length === 0}
                            className="w-full py-3 rounded-xl bg-emerald-600 text-white font-semibold text-sm hover:bg-emerald-500 transition disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/20"
                        >
                            {isGeneratingReport ? (
                                <><Loader2 className="w-4 h-4 animate-spin" /> Generating Report...</>
                            ) : (
                                <><ClipboardList className="w-4 h-4" /> Generate Full Medical Report</>
                            )}
                        </button>
                    </div>

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
                    <HealthChatPanel sessionId={sessionId} hasLogs={logs.length > 0} chronicDisease={chronicDisease} />
                </div>

                {/* ── DOCTOR'S POINTS SECTION ── */}
                <div className="space-y-4 pt-6 mt-6 border-t border-border">
                    <div className="flex items-center gap-2">
                        <Stethoscope className="w-4 h-4 text-primary" />
                        <h2 className="font-semibold text-foreground">Doctor's Clinical Points</h2>
                    </div>

                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={doctorPoint}
                            onChange={(e) => setDoctorPoint(e.target.value)}
                            placeholder="Add a point from your doctor (e.g. Reduce salt intake)"
                            className="flex-1 bg-card border border-border px-4 py-2 rounded-xl text-sm focus:ring-2 focus:ring-primary outline-none"
                        />
                        <button
                            onClick={handleAddAdvice}
                            disabled={isSavingAdvice || !doctorPoint}
                            className="px-4 py-2 bg-primary text-primary-foreground rounded-xl flex items-center gap-2 text-sm font-bold"
                        >
                            {isSavingAdvice ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            Save Point
                        </button>
                    </div>

                    <div className="space-y-2 max-h-[200px] overflow-y-auto pr-2">
                        {doctorAdvices.length === 0 ? (
                            <div className="p-8 rounded-2xl border-2 border-dashed border-border/50 flex flex-col items-center justify-center text-muted-foreground text-xs italic">
                                <History className="w-8 h-8 opacity-20 mb-2" />
                                No doctor's points recorded yet.
                            </div>
                        ) : (
                            doctorAdvices.map((adv, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    className="p-3 rounded-xl bg-primary/5 border border-primary/10 flex flex-col gap-1"
                                >
                                    <p className="text-sm text-foreground font-medium">"{adv.content}"</p>
                                    <span className="text-[10px] text-muted-foreground text-right italic">
                                        Added on {new Date(adv.timestamp).toLocaleDateString()}
                                    </span>
                                </motion.div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            <HealthReportModal
                isOpen={isReportOpen}
                onClose={() => setIsReportOpen(false)}
                report={report}
            />
        </div>
    );
};

export default HealthMonitorPage;
