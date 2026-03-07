import { useState, useCallback, useEffect } from "react";
import type { HealthLogEntry, HealthAnalysis } from "@/types/clinical";

const API = "http://localhost:8000/api";

export const useHealthMonitor = (sessionId: string, currentDisease?: string | null) => {
    const [logs, setLogs] = useState<HealthLogEntry[]>([]);
    const [analysis, setAnalysis] = useState<HealthAnalysis | null>(null);
    const [isLogging, setIsLogging] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Fetch persistent logs on mount and when disease changes
    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const url = currentDisease
                    ? `${API}/health-log/${sessionId}?chronic_disease=${encodeURIComponent(currentDisease)}`
                    : `${API}/health-log/${sessionId}`;
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    if (Array.isArray(data)) {
                        setLogs(data);
                    }
                }
            } catch (e) {
                console.error("Failed to fetch persistent health logs:", e);
            }
        };
        fetchLogs();
    }, [sessionId, currentDisease]);

    const logReading = useCallback(
        async (entry: Omit<HealthLogEntry, "session_id">) => {
            setIsLogging(true);
            setError(null);
            try {
                const res = await fetch(`${API}/health-log`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ ...entry, session_id: sessionId }),
                });
                if (!res.ok) throw new Error(`Server error: ${res.status}`);
                const full: HealthLogEntry = { ...entry, session_id: sessionId };
                setLogs((prev) => [...prev, full]);
            } catch (e: any) {
                setError(e.message || "Failed to log reading");
            } finally {
                setIsLogging(false);
            }
        },
        [sessionId]
    );

    const getAnalysis = useCallback(async () => {
        setIsAnalyzing(true);
        setError(null);
        try {
            const url = currentDisease
                ? `${API}/health-summary/${sessionId}?chronic_disease=${encodeURIComponent(currentDisease)}`
                : `${API}/health-summary/${sessionId}`;
            const res = await fetch(url);
            if (!res.ok) throw new Error(`Server error: ${res.status}`);
            const data: HealthAnalysis = await res.json();
            setAnalysis(data);
        } catch (e: any) {
            setError(e.message || "Failed to get analysis");
        } finally {
            setIsAnalyzing(false);
        }
    }, [sessionId, currentDisease]);

    const getReport = useCallback(async (chronicDisease?: string) => {
        setError(null);
        try {
            const url = chronicDisease
                ? `${API}/medical-report/${sessionId}?chronic_disease=${encodeURIComponent(chronicDisease)}`
                : `${API}/medical-report/${sessionId}`;
            const res = await fetch(url);
            if (!res.ok) throw new Error(`Server error: ${res.status}`);
            return await res.json();
        } catch (e: any) {
            setError(e.message || "Failed to generate medical report");
            return null;
        }
    }, [sessionId]);

    const deleteLogsByDisease = useCallback(async (disease: string) => {
        setError(null);
        try {
            const res = await fetch(`${API}/health-log/${sessionId}/${encodeURIComponent(disease)}`, {
                method: "DELETE"
            });
            if (!res.ok) throw new Error("Failed to delete logs");

            setLogs((prev) => prev.filter(l => {
                const logDisease = (l.chronic_disease || "None / General Monitoring").toLowerCase();
                const targetDisease = disease.toLowerCase();
                return logDisease !== targetDisease;
            }));
            return true;
        } catch (e: any) {
            setError(e.message);
            return false;
        }
    }, [sessionId]);

    const addDoctorAdvice = useCallback(async (disease: string, point: string) => {
        try {
            const res = await fetch(`${API}/doctor-advice`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionId, chronic_disease: disease, point })
            });
            return res.ok;
        } catch (e) {
            return false;
        }
    }, [sessionId]);

    const getDoctorAdvice = useCallback(async (disease: string) => {
        try {
            const res = await fetch(`${API}/doctor-advice/${sessionId}/${encodeURIComponent(disease)}`);
            if (res.ok) return await res.json();
            return [];
        } catch (e) {
            return [];
        }
    }, [sessionId]);

    return {
        logs,
        analysis,
        isLogging,
        isAnalyzing,
        error,
        logReading,
        getAnalysis,
        getReport,
        deleteLogsByDisease,
        addDoctorAdvice,
        getDoctorAdvice
    };
};
