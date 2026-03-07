import { useState, useCallback, useEffect } from "react";
import type { HealthLogEntry, HealthAnalysis } from "@/types/clinical";

const API = "http://localhost:8000/api";

export const useHealthMonitor = (sessionId: string) => {
    const [logs, setLogs] = useState<HealthLogEntry[]>([]);
    const [analysis, setAnalysis] = useState<HealthAnalysis | null>(null);
    const [isLogging, setIsLogging] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Fetch persistent logs on mount
    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const res = await fetch(`${API}/health-log/${sessionId}`);
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
    }, [sessionId]);

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
            const res = await fetch(`${API}/health-summary/${sessionId}`);
            if (!res.ok) throw new Error(`Server error: ${res.status}`);
            const data: HealthAnalysis = await res.json();
            setAnalysis(data);
        } catch (e: any) {
            setError(e.message || "Failed to get analysis");
        } finally {
            setIsAnalyzing(false);
        }
    }, [sessionId]);

    return { logs, analysis, isLogging, isAnalyzing, error, logReading, getAnalysis };
};
