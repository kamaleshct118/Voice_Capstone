import { useState, useMemo } from "react";
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, ReferenceLine, Legend,
    BarChart, Bar, AreaChart, Area, ComposedChart,
    PieChart, Pie, Cell
} from "recharts";
import type { HealthLogEntry } from "@/types/clinical";

interface HealthTrendChartProps {
    logs: HealthLogEntry[];
}

type Metric = "bp" | "sugar" | "weight" | "mood";

const TABS: { key: Metric; label: string }[] = [
    { key: "bp", label: "Blood Pressure" },
    { key: "sugar", label: "Blood Sugar" },
    { key: "weight", label: "Weight" },
    { key: "mood", label: "Mood Trends" },
];

const COLORS = ['#10b981', '#6366f1', '#f59e0b', '#ef4444', '#8b5cf6'];

const HealthTrendChart = ({ logs }: HealthTrendChartProps) => {
    const [metric, setMetric] = useState<Metric>("bp");

    const chartData = useMemo(() => {
        return logs.map((log, i) => ({
            index: i + 1,
            systolic: log.systolic_bp,
            diastolic: log.diastolic_bp,
            fasting: log.sugar_fasting,
            postmeal: log.sugar_postmeal,
            weight: log.weight_kg,
            mood: log.mood || "neutral"
        }));
    }, [logs]);

    const moodData = useMemo(() => {
        if (metric !== 'mood') return [];
        const counts: Record<string, number> = {};
        logs.forEach(log => {
            if (log.mood) {
                counts[log.mood] = (counts[log.mood] || 0) + 1;
            }
        });
        return Object.entries(counts).map(([name, value]) => ({ name, value }));
    }, [logs, metric]);

    return (
        <div className="space-y-4">
            {/* Tab switcher */}
            <div className="flex flex-wrap gap-1 bg-muted/50 rounded-xl p-1.5">
                {TABS.map((t) => (
                    <button
                        key={t.key}
                        onClick={() => setMetric(t.key)}
                        className={`flex-1 min-w-[100px] py-1.5 text-xs font-medium rounded-lg transition-all ${metric === t.key
                            ? "bg-background text-foreground shadow-sm ring-1 ring-border"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted"
                            }`}
                    >
                        {t.label}
                    </button>
                ))}
            </div>

            {/* Chart */}
            <div className="h-64 w-full">
                {logs.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground text-sm border-2 border-dashed border-border/50 rounded-xl">
                        <span className="mb-2">📊</span>
                        No data yet. Log your first reading.
                    </div>
                ) : metric === "mood" && moodData.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground text-sm border-2 border-dashed border-border/50 rounded-xl">
                        <span className="mb-2">🎭</span>
                        No mood data logged yet.
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        {/* Wrapper trick: instead of inline conditional which returns booleans, we use block level assignments or conditional rendering that ensures exactly ONE child. */}
                        {metric === "bp" ? (
                            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="sysColor" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="diaColor" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                <XAxis dataKey="index" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                                <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12, fontSize: 12, boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                                />
                                <Legend wrapperStyle={{ fontSize: 11, paddingTop: '10px' }} iconType="circle" />

                                <ReferenceLine y={140} stroke="#ef4444" strokeDasharray="4 2" label={{ value: "Sys Danger (140)", fontSize: 10, fill: "#ef4444", position: 'insideTopLeft' }} />
                                <ReferenceLine y={90} stroke="#6366f1" strokeDasharray="4 2" label={{ value: "Dia Danger (90)", fontSize: 10, fill: "#6366f1", position: 'insideTopLeft' }} />

                                <Area type="monotone" dataKey="systolic" fillOpacity={1} fill="url(#sysColor)" stroke="none" />
                                <Area type="monotone" dataKey="diastolic" fillOpacity={1} fill="url(#diaColor)" stroke="none" />
                                <Line type="monotone" dataKey="systolic" stroke="#ef4444" strokeWidth={3} dot={{ r: 4, strokeWidth: 2, fill: "hsl(var(--background))" }} activeDot={{ r: 6 }} name="Systolic" />
                                <Line type="monotone" dataKey="diastolic" stroke="#6366f1" strokeWidth={3} dot={{ r: 4, strokeWidth: 2, fill: "hsl(var(--background))" }} activeDot={{ r: 6 }} name="Diastolic" />
                            </ComposedChart>
                        ) : metric === "sugar" ? (
                            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }} barGap={2} barSize={20}>
                                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                <XAxis dataKey="index" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                                <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                                <Tooltip
                                    cursor={{ fill: 'hsl(var(--muted))', opacity: 0.4 }}
                                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12, fontSize: 12, boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                                />
                                <Legend wrapperStyle={{ fontSize: 11, paddingTop: '10px' }} iconType="circle" />

                                <ReferenceLine y={126} stroke="#ef4444" strokeDasharray="4 2" label={{ value: "Danger 126", fontSize: 10, fill: "#ef4444", position: 'insideTopLeft' }} />
                                <ReferenceLine y={100} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: "Warning 100", fontSize: 10, fill: "#f59e0b", position: 'insideTopLeft' }} />

                                <Bar dataKey="fasting" fill="#10b981" radius={[4, 4, 0, 0]} name="Fasting" />
                                <Bar dataKey="postmeal" fill="#14b8a6" radius={[4, 4, 0, 0]} name="Post-meal" />
                            </BarChart>
                        ) : metric === "weight" ? (
                            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="weightColor" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8} />
                                        <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                <XAxis dataKey="index" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                                <YAxis domain={['dataMin - 2', 'dataMax + 2']} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12, fontSize: 12, boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                                />
                                <Legend wrapperStyle={{ fontSize: 11, paddingTop: '10px' }} iconType="circle" />

                                <Area type="monotone" dataKey="weight" stroke="#f59e0b" strokeWidth={3} fillOpacity={1} fill="url(#weightColor)" name="Weight (kg)" activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }} />
                            </AreaChart>
                        ) : (
                            <PieChart margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                                <Pie
                                    data={moodData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                    labelLine={false}
                                >
                                    {moodData.map((_entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12, fontSize: 12 }}
                                    itemStyle={{ color: 'hsl(var(--foreground))' }}
                                />
                            </PieChart>
                        )}
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
};

export default HealthTrendChart;
