import { useRef } from "react";
import {
    Dialog, DialogContent, DialogHeader, DialogTitle,
    DialogDescription, DialogFooter
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    Table, TableBody, TableCell, TableHead,
    TableHeader, TableRow
} from "@/components/ui/table";
import {
    FileText, Download, Printer, TrendingUp,
    Lightbulb, Clipboard, Calendar
} from "lucide-react";
import type { MedicalReportData } from "@/types/clinical";
import HealthTrendChart from "./HealthTrendChart";
import { motion } from "framer-motion";

interface HealthReportModalProps {
    isOpen: boolean;
    onClose: () => void;
    report: MedicalReportData | null;
}

const HealthReportModal = ({ isOpen, onClose, report }: HealthReportModalProps) => {
    const reportRef = useRef<HTMLDivElement>(null);

    if (!report) return null;

    const handlePrint = () => {
        window.print();
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl w-[95vw] max-h-[90vh] p-0 overflow-hidden flex flex-col glass-morphism border-primary/20 bg-card/95 print:w-full print:max-w-full print:h-auto print:max-h-none print:shadow-none print:border-none print:bg-white print:text-black print:overflow-visible">
                <DialogHeader className="p-6 pb-2">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-1.5 rounded-xl bg-primary/20 text-primary print:hidden">
                                <FileText className="w-5 h-5" />
                            </div>
                            <div>
                                <DialogTitle className="text-xl font-bold print:hidden">Personalized Health Report</DialogTitle>
                                <DialogDescription className="text-xs text-muted-foreground flex items-center gap-2 mt-1 print:hidden">
                                    <Calendar className="w-3 h-3" />
                                    Generated on {new Date(report.generated_at).toLocaleDateString()} at {new Date(report.generated_at).toLocaleTimeString()}
                                </DialogDescription>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <Button variant="outline" size="sm" onClick={handlePrint} className="rounded-xl flex items-center gap-2">
                                <Printer className="w-4 h-4" />
                                <span className="hidden sm:inline">Print Report</span>
                            </Button>
                        </div>
                    </div>
                </DialogHeader>

                <ScrollArea className="flex-1 p-2 sm:p-4 print:p-0 print:overflow-visible">
                    <div ref={reportRef} className="space-y-3 print:m-0 print:p-0">
                        <style>{`
                            @media print {
                                @page { size: A4 portrait; margin: 0.5cm; }
                                #root { display: none !important; }
                                /* Shadcn/Radix Dialog Portal */
                                body > div[data-radix-portal] {
                                    position: absolute !important;
                                    top: 0 !important;
                                    left: 0 !important;
                                    width: 100% !important;
                                    height: auto !important;
                                    margin: 0 !important;
                                    padding: 0 !important;
                                }
                                [role="dialog"] {
                                    position: relative !important;
                                    top: auto !important;
                                    left: auto !important;
                                    transform: none !important;
                                    width: 100% !important;
                                    max-width: 100% !important;
                                    height: auto !important;
                                    max-height: none !important;
                                    box-shadow: none !important;
                                    border: none !important;
                                    background: white !important;
                                }
                                .print\\:hidden { display: none !important; }
                            }
                        `}</style>
                        <div className="w-full bg-transparent">
                            {/* 1. Dashboard summary banner -> now "Condition" */}
                            <div className="text-center pb-2 border-b border-primary/20">
                                <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">Condition</h3>
                                <p className="text-xl font-bold text-primary uppercase tracking-widest">{report.chronic_disease}</p>
                            </div>

                            {/* 2. Analysed Data Box */}
                            <div className="p-4 rounded-xl border-2 border-primary/20 bg-card/60 space-y-2.5">
                                <h3 className="text-lg font-bold flex items-center gap-2 text-foreground">
                                    <Clipboard className="w-4 h-4 text-blue-400" />
                                    Analysed Data
                                </h3>
                                <p className="text-xs text-foreground/80 leading-snug font-medium">
                                    Based on {report.detailed_logs.length} data points and recent interactions, the AI assistant recommends the following wellness strategies:
                                </p>
                                <ul className="grid sm:grid-cols-2 gap-2 mt-2">
                                    {report.health_tips.map((tip, i) => (
                                        <li key={i} className="flex gap-2 text-xs bg-primary/5 p-2 rounded-lg border border-primary/10 items-start">
                                            <span className="flex-shrink-0 w-4 h-4 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-[9px] mt-0.5">
                                                {i + 1}
                                            </span>
                                            <span className="text-foreground leading-relaxed italic">{tip}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            {/* 3. 2x2 Trends Grid */}
                            <div className="grid sm:grid-cols-2 gap-3 mt-4">
                                {/* Sugar Trend */}
                                <div className="p-3 rounded-xl border border-border bg-card/50">
                                    <h4 className="text-xs font-bold text-center mb-1.5 text-foreground tracking-wide uppercase">Sugar Trend</h4>
                                    <div className="h-[170px] w-full">
                                        <HealthTrendChart logs={report.detailed_logs} forceMetric="sugar" />
                                    </div>
                                </div>
                                {/* Pressure Trend */}
                                <div className="p-3 rounded-xl border border-border bg-card/50">
                                    <h4 className="text-xs font-bold text-center mb-1.5 text-foreground tracking-wide uppercase">Pressure Trend</h4>
                                    <div className="h-[170px] w-full">
                                        <HealthTrendChart logs={report.detailed_logs} forceMetric="bp" />
                                    </div>
                                </div>
                                {/* Weight Trend */}
                                <div className="p-3 rounded-xl border border-border bg-card/50">
                                    <h4 className="text-xs font-bold text-center mb-1.5 text-foreground tracking-wide uppercase">Weight Trend</h4>
                                    <div className="h-[170px] w-full">
                                        <HealthTrendChart logs={report.detailed_logs} forceMetric="weight" />
                                    </div>
                                </div>
                                {/* Mood Trend */}
                                <div className="p-3 rounded-xl border border-border bg-card/50">
                                    <h4 className="text-xs font-bold text-center mb-1.5 text-foreground tracking-wide uppercase">Mood Trend</h4>
                                    <div className="h-[170px] w-full">
                                        <HealthTrendChart logs={report.detailed_logs} forceMetric="mood" />
                                    </div>
                                </div>
                            </div>

                            {/* Disclaimer */}
                            <div className="p-1.5 rounded-md bg-destructive/10 border border-destructive/20 text-[7px] text-destructive italic text-center leading-tight mt-2">
                                <strong>Disclaimer:</strong> {report.disclaimer}
                            </div>
                        </div>
                    </div>
                </ScrollArea>

                <DialogFooter className="p-4 border-t border-border bg-muted/20 print:hidden">
                    <Button onClick={onClose} className="rounded-xl w-full sm:w-auto">Close Report</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

export default HealthReportModal;
