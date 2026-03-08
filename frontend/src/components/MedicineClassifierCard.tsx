import React from "react";
import { motion } from "framer-motion";
import { Pill, FlaskConical, Shield, Info, AlertTriangle } from "lucide-react";
import type { MedicineData } from "@/types/clinical";

interface MedicineClassifierCardProps {
    data: MedicineData;
}

const inputModeBadge: Record<string, { label: string; color: string }> = {
    image: { label: "📷 Image Scan", color: "bg-violet-500/15 text-violet-400 border-violet-500/30" },
    "image+text": { label: "👁️‍🗨️ Image + Text", color: "bg-fuchsia-500/15 text-fuchsia-400 border-fuchsia-500/30" },
    voice: { label: "🎤 Voice", color: "bg-blue-500/15 text-blue-400 border-blue-500/30" },
    text: { label: "⌨️ Text", color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
};

const MedicineClassifierCard = ({ data }: MedicineClassifierCardProps) => {
    const badge = inputModeBadge[data.input_mode] ?? inputModeBadge.text;

    return (
        <motion.div
            className="rounded-2xl border border-border bg-card p-5 space-y-4"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
        >
            {/* Header */}
            <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2">
                    <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center">
                        <Pill className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h3 className="font-bold text-foreground text-base leading-tight">
                            {data.medicine_name}
                        </h3>
                        <span className="text-xs text-muted-foreground">{data.drug_category}</span>
                    </div>
                </div>
                <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${badge.color}`}>
                    {badge.label}
                </span>
            </div>

            {/* Details */}
            <div className="space-y-3 text-sm">
                <Row
                    icon={<Info className="w-4 h-4 text-emerald-400" />}
                    label="Purpose"
                    value={data.purpose}
                />
                <Row
                    icon={<Shield className="w-4 h-4 text-amber-400" />}
                    label="Safety Notes"
                    value={data.basic_safety_notes}
                />
            </div>

            {/* Disclaimer */}
            <div className="flex items-start gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{data.disclaimer}</span>
            </div>
        </motion.div>
    );
};

const Row = ({
    icon,
    label,
    value,
}: {
    icon: React.ReactNode;
    label: string;
    value: string;
}) => (
    <div className="flex gap-2">
        <div className="mt-0.5 shrink-0">{icon}</div>
        <div className="flex-1">
            <span className="text-muted-foreground font-medium">{label}</span>
            <div className="text-foreground whitespace-pre-wrap mt-0.5 leading-relaxed">{value}</div>
        </div>
    </div>
);

export default MedicineClassifierCard;
