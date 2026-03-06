import { useState } from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import type { HealthLogEntry } from "@/types/clinical";

interface HealthLogFormProps {
    onSubmit: (entry: Omit<HealthLogEntry, "session_id">) => Promise<void>;
    isLoading: boolean;
}

const MOODS = ["good", "calm", "stressed", "anxious", "tired"];

const COMMON_SYMPTOMS = [
    "headache", "fatigue", "dizziness", "nausea",
    "chest pain", "shortness of breath", "palpitations", "swelling",
];

const HealthLogForm = ({ onSubmit, isLoading }: HealthLogFormProps) => {
    const [systolicBp, setSystolicBp] = useState("");
    const [diastolicBp, setDiastolicBp] = useState("");
    const [sugarFasting, setSugarFasting] = useState("");
    const [sugarPostmeal, setSugarPostmeal] = useState("");
    const [weightKg, setWeightKg] = useState("");
    const [mood, setMood] = useState("");
    const [symptoms, setSymptoms] = useState<string[]>([]);
    const [notes, setNotes] = useState("");

    const toggleSymptom = (s: string) =>
        setSymptoms((prev) =>
            prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
        );

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await onSubmit({
            condition: "other", // Default fallback if needed by backend model, though it relies on chronic_disease now
            systolic_bp: systolicBp ? parseInt(systolicBp) : undefined,
            diastolic_bp: diastolicBp ? parseInt(diastolicBp) : undefined,
            sugar_fasting: sugarFasting ? parseFloat(sugarFasting) : undefined,
            sugar_postmeal: sugarPostmeal ? parseFloat(sugarPostmeal) : undefined,
            weight_kg: weightKg ? parseFloat(weightKg) : undefined,
            mood: mood || undefined,
            symptoms: symptoms.length > 0 ? symptoms : undefined,
            notes: notes.trim() || undefined,
        });
        // Keep condition; reset values for next log
        setSystolicBp(""); setDiastolicBp("");
        setSugarFasting(""); setSugarPostmeal("");
        setWeightKg(""); setMood(""); setSymptoms([]); setNotes("");
    };

    return (
        <motion.form
            onSubmit={handleSubmit}
            className="space-y-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
        >
            {/* Blood Pressure */}
            <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1.5">
                    Blood Pressure (mmHg)
                </label>
                <div className="flex gap-2">
                    <input
                        type="number" placeholder="Systolic"
                        value={systolicBp} onChange={(e) => setSystolicBp(e.target.value)}
                        className="flex-1 rounded-xl border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                    <span className="self-center text-muted-foreground">/</span>
                    <input
                        type="number" placeholder="Diastolic"
                        value={diastolicBp} onChange={(e) => setDiastolicBp(e.target.value)}
                        className="flex-1 rounded-xl border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                </div>
            </div>

            {/* Sugar */}
            <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1.5">
                    Blood Sugar (mg/dL)
                </label>
                <div className="flex gap-2">
                    <input
                        type="number" placeholder="Fasting"
                        value={sugarFasting} onChange={(e) => setSugarFasting(e.target.value)}
                        className="flex-1 rounded-xl border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                    <input
                        type="number" placeholder="Post-meal"
                        value={sugarPostmeal} onChange={(e) => setSugarPostmeal(e.target.value)}
                        className="flex-1 rounded-xl border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                </div>
            </div>

            {/* Weight */}
            <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1.5">
                    Weight (kg)
                </label>
                <input
                    type="number" step="0.1" placeholder="e.g. 72.5"
                    value={weightKg} onChange={(e) => setWeightKg(e.target.value)}
                    className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
            </div>

            {/* Mood */}
            <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1.5">
                    Mood
                </label>
                <div className="flex flex-wrap gap-2">
                    {MOODS.map((m) => (
                        <button
                            key={m} type="button"
                            onClick={() => setMood(mood === m ? "" : m)}
                            className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${mood === m
                                ? "bg-primary text-primary-foreground border-primary"
                                : "border-border text-muted-foreground hover:border-primary/50"
                                }`}
                        >
                            {m.charAt(0).toUpperCase() + m.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Symptoms */}
            <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1.5">
                    Symptoms
                </label>
                <div className="flex flex-wrap gap-2">
                    {COMMON_SYMPTOMS.map((s) => (
                        <button
                            key={s} type="button"
                            onClick={() => toggleSymptom(s)}
                            className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${symptoms.includes(s)
                                ? "bg-destructive/20 text-destructive border-destructive/50"
                                : "border-border text-muted-foreground hover:border-destructive/30"
                                }`}
                        >
                            {s}
                        </button>
                    ))}
                </div>
            </div>

            {/* Notes */}
            <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1.5">
                    Additional Notes
                </label>
                <textarea
                    value={notes} onChange={(e) => setNotes(e.target.value)}
                    placeholder="Any additional observations..."
                    rows={2}
                    className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                />
            </div>

            {/* Submit */}
            <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
                {isLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Logging...</>
                ) : (
                    "Log Health Reading"
                )}
            </button>
        </motion.form>
    );
};

export default HealthLogForm;
