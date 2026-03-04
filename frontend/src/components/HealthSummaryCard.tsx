import React from "react";
import { motion } from "framer-motion";
import {
    AlertTriangle, Salad, Activity, Brain, ShieldAlert, Volume2,
} from "lucide-react";
import type { HealthAnalysis, FlaggedReading } from "@/types/clinical";
import AudioPlayer from "./AudioPlayer";

interface HealthSummaryCardProps {
    analysis: HealthAnalysis;
}

const levelStyles: Record<string, string> = {
    warning: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    danger: "bg-red-500/15 text-red-400 border-red-500/30",
};

const FlaggedBadge = ({ reading }: { reading: FlaggedReading }) => (
    <span
        className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full border ${levelStyles[reading.level]}`}
    >
        <ShieldAlert className="w-3 h-3" />
        {reading.field.replace(/_/g, " ")} = {reading.value} ({reading.level})
    </span>
);

const HealthSummaryCard = ({ analysis }: HealthSummaryCardProps) => (
    <motion.div
        className="space-y-5"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
    >
        {/* Summary */}
        <div className="p-4 rounded-2xl bg-primary/5 border border-primary/20">
            <p className="text-sm text-foreground leading-relaxed">{analysis.summary}</p>
        </div>

        {/* Flagged readings */}
        {analysis.flagged_readings?.length > 0 && (
            <div>
                <h4 className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                    Flagged Readings
                </h4>
                <div className="flex flex-wrap gap-2">
                    {analysis.flagged_readings.map((r, i) => (
                        <FlaggedBadge key={i} reading={r} />
                    ))}
                </div>
            </div>
        )}

        {/* Diet suggestions */}
        {analysis.diet_suggestions?.length > 0 && (
            <Section icon={<Salad className="w-4 h-4 text-emerald-400" />} title="Diet Suggestions">
                <ul className="space-y-1">
                    {analysis.diet_suggestions.map((s, i) => (
                        <li key={i} className="flex gap-2 text-sm text-foreground">
                            <span className="text-emerald-400 mt-0.5">•</span>
                            {s}
                        </li>
                    ))}
                </ul>
            </Section>
        )}

        {/* Lifestyle recommendations */}
        {analysis.lifestyle_recommendations?.length > 0 && (
            <Section icon={<Activity className="w-4 h-4 text-blue-400" />} title="Lifestyle Recommendations">
                <ul className="space-y-1">
                    {analysis.lifestyle_recommendations.map((r, i) => (
                        <li key={i} className="flex gap-2 text-sm text-foreground">
                            <span className="text-blue-400 mt-0.5">•</span>
                            {r}
                        </li>
                    ))}
                </ul>
            </Section>
        )}

        {/* Mental health */}
        {analysis.mental_health_guidance && (
            <Section icon={<Brain className="w-4 h-4 text-violet-400" />} title="Mental Wellbeing">
                <p className="text-sm text-foreground italic">{analysis.mental_health_guidance}</p>
            </Section>
        )}

        {/* Audio */}
        {analysis.audio_url && (
            <div>
                <h4 className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-2">
                    <Volume2 className="w-3.5 h-3.5" />
                    Voice Summary
                </h4>
                <AudioPlayer audioUrl={analysis.audio_url} />
            </div>
        )}

        {/* Disclaimer */}
        <div className="flex gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{analysis.disclaimer}</span>
        </div>
    </motion.div>
);

const Section = ({
    icon,
    title,
    children,
}: {
    icon: React.ReactNode;
    title: string;
    children: React.ReactNode;
}) => (
    <div>
        <h4 className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-2">
            {icon}
            {title}
        </h4>
        {children}
    </div>
);

export default HealthSummaryCard;
