import { useState } from "react";
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, ReferenceLine, Legend,
} from "recharts";
import type { HealthLogEntry } from "@/types/clinical";

interface HealthTrendChartProps {
    logs: HealthLogEntry[];
}

type Metric = "bp" | "sugar" | "weight";

const TABS: { key: Metric; label: string }[] = [
    { key: "bp", label: "Blood Pressure" },
    { key: "sugar", label: "Blood Sugar" },
    { key: "weight", label: "Weight" },
];

const HealthTrendChart = ({ logs }: HealthTrendChartProps) => {
    const [metric, setMetric] = useState<Metric>("bp");

    const chartData = logs.map((log, i) => ({
        index: i + 1,
        systolic: log.systolic_bp,
        diastolic: log.diastolic_bp,
        fasting: log.sugar_fasting,
        postmeal: log.sugar_postmeal,
        weight: log.weight_kg,
    }));

    return (
        <div className="space-y-3">
            {/* Tab switcher */}
            <div className="flex gap-1 bg-muted rounded-xl p-1">
                {TABS.map((t) => (
                    <button
                        key={t.key}
                        onClick={() => setMetric(t.key)}
                        className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${metric === t.key
                                ? "bg-background text-foreground shadow-sm"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                    >
                        {t.label}
                    </button>
                ))}
            </div>

            {/* Chart */}
            <div className="h-52">
                {logs.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
                        No data yet. Log your first reading.
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                            <XAxis dataKey="index" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                            <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: "hsl(var(--card))",
                                    border: "1px solid hsl(var(--border))",
                                    borderRadius: 12,
                                    fontSize: 12,
                                }}
                            />
                            <Legend wrapperStyle={{ fontSize: 11 }} />

                            {metric === "bp" && (
                                <>
                                    <ReferenceLine y={140} stroke="#ef4444" strokeDasharray="4 2" label={{ value: "Danger 140", fontSize: 10, fill: "#ef4444" }} />
                                    <ReferenceLine y={120} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: "Warning 120", fontSize: 10, fill: "#f59e0b" }} />
                                    <Line type="monotone" dataKey="systolic" stroke="#6366f1" strokeWidth={2} dot={{ r: 3 }} name="Systolic" />
                                    <Line type="monotone" dataKey="diastolic" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} name="Diastolic" />
                                </>
                            )}

                            {metric === "sugar" && (
                                <>
                                    <ReferenceLine y={126} stroke="#ef4444" strokeDasharray="4 2" label={{ value: "Danger 126", fontSize: 10, fill: "#ef4444" }} />
                                    <ReferenceLine y={100} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: "Warning 100", fontSize: 10, fill: "#f59e0b" }} />
                                    <Line type="monotone" dataKey="fasting" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} name="Fasting" />
                                    <Line type="monotone" dataKey="postmeal" stroke="#14b8a6" strokeWidth={2} dot={{ r: 3 }} name="Post-meal" />
                                </>
                            )}

                            {metric === "weight" && (
                                <Line type="monotone" dataKey="weight" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} name="Weight (kg)" />
                            )}
                        </LineChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
};

export default HealthTrendChart;
