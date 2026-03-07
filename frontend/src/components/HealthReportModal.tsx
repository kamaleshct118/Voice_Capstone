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
            <DialogContent className="max-w-4xl w-[95vw] max-h-[90vh] p-0 overflow-hidden flex flex-col glass-morphism border-primary/20 bg-card/95">
                <DialogHeader className="p-6 pb-2">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-xl bg-primary/20 text-primary">
                                <FileText className="w-5 h-5" />
                            </div>
                            <div>
                                <DialogTitle className="text-xl font-bold">Personalized Health Report</DialogTitle>
                                <DialogDescription className="text-xs text-muted-foreground flex items-center gap-2 mt-1">
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

                <ScrollArea className="flex-1 p-6">
                    <div ref={reportRef} className="space-y-8 print:p-8">
                        {/* 1. Dashboard summary banner */}
                        <div className="p-5 rounded-2xl bg-primary/5 border border-primary/10 flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
                            <div>
                                <h3 className="text-sm font-semibold text-primary uppercase tracking-wider">Health Condition</h3>
                                <p className="text-2xl font-bold text-foreground mt-1">{report.chronic_disease}</p>
                            </div>
                            <div className="text-right sm:text-right">
                                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Recorded History</h3>
                                <p className="text-xl font-bold text-foreground mt-1">{report.detailed_logs.length} Data Points</p>
                            </div>
                        </div>

                        {/* 2. Visual Trends (Graphs) */}
                        <section className="space-y-4">
                            <h3 className="text-lg font-bold flex items-center gap-2 text-foreground">
                                <TrendingUp className="w-5 h-5 text-emerald-400" />
                                Interactive Health Trends
                            </h3>
                            <div className="p-4 rounded-2xl border border-border bg-card/50">
                                <HealthTrendChart logs={report.detailed_logs} />
                            </div>
                        </section>

                        {/* 3. Personalized Tips (6 Points) */}
                        <section className="space-y-4">
                            <h3 className="text-lg font-bold flex items-center gap-2 text-foreground">
                                <Lightbulb className="w-5 h-5 text-amber-400" />
                                AI-Generated Wellness Strategies
                            </h3>
                            <div className="grid sm:grid-cols-2 gap-3">
                                {report.health_tips.map((tip, i) => (
                                    <motion.div
                                        key={i}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: i * 0.1 }}
                                        className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/10 flex gap-3 text-sm"
                                    >
                                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-amber-500/20 text-amber-500 flex items-center justify-center font-bold text-xs ring-1 ring-amber-500/30">
                                            {i + 1}
                                        </span>
                                        <p className="text-foreground leading-relaxed italic">{tip}</p>
                                    </motion.div>
                                ))}
                            </div>
                        </section>

                        {/* 4. Detailed Data Table */}
                        <section className="space-y-4">
                            <h3 className="text-lg font-bold flex items-center gap-2 text-foreground">
                                <Clipboard className="w-5 h-5 text-blue-400" />
                                Detailed Observation Log
                            </h3>
                            <div className="rounded-xl border border-border overflow-hidden">
                                <Table>
                                    <TableHeader className="bg-muted/50">
                                        <TableRow>
                                            <TableHead className="text-xs uppercase">Date</TableHead>
                                            <TableHead className="text-xs uppercase">Metric (BP/Sugar/Wh)</TableHead>
                                            <TableHead className="text-xs uppercase">Symptoms/Notes</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {report.detailed_logs.map((log, i) => (
                                            <TableRow key={i} className="hover:bg-primary/5 transition-colors">
                                                <TableCell className="text-xs font-medium">
                                                    {new Date(log.timestamp!).toLocaleDateString()}
                                                </TableCell>
                                                <TableCell className="text-xs space-y-1">
                                                    {log.systolic_bp && (
                                                        <div className="flex items-center gap-1">
                                                            <span className="text-muted-foreground w-12">BP:</span>
                                                            <span className="font-semibold text-rose-400">{log.systolic_bp}/{log.diastolic_bp}</span>
                                                        </div>
                                                    )}
                                                    {log.sugar_fasting && (
                                                        <div className="flex items-center gap-1">
                                                            <span className="text-muted-foreground w-12">Sugar:</span>
                                                            <span className="font-semibold text-emerald-400">{log.sugar_fasting} F / {log.sugar_postmeal} PM</span>
                                                        </div>
                                                    )}
                                                    {log.weight_kg && (
                                                        <div className="flex items-center gap-1">
                                                            <span className="text-muted-foreground w-12">Wh:</span>
                                                            <span className="font-semibold text-amber-400">{log.weight_kg} kg</span>
                                                        </div>
                                                    )}
                                                </TableCell>
                                                <TableCell className="text-xs italic text-muted-foreground max-w-[200px] truncate">
                                                    {log.symptoms?.join(", ") || log.notes || "—"}
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </div>
                        </section>

                        {/* 5. Disclaimer */}
                        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-[10px] text-destructive italic text-center leading-relaxed">
                            <strong>Disclaimer:</strong> {report.disclaimer}
                        </div>
                    </div>
                </ScrollArea>

                <DialogFooter className="p-6 pt-2 border-t border-border bg-muted/20">
                    <Button onClick={onClose} className="rounded-xl w-full sm:w-auto">Close Report</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

export default HealthReportModal;
