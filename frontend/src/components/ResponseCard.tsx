import React from "react";
import { motion } from "framer-motion";
import {
  Stethoscope, Pill, FileText, Activity, Newspaper,
  MessageCircle, ClipboardList, MapPin, Lightbulb, HeartPulse
} from "lucide-react";
import type { ApiResponse } from "@/types/clinical";
import { TOOL_LABELS } from "@/types/clinical";
import MedicineClassifierCard from "./MedicineClassifierCard";
import MapComponent from "./MapComponent";
import NewsCard from "./NewsCard";

interface ResponseCardProps {
  data: ApiResponse;
}

const toolIcons: Record<string, React.ReactNode> = {
  medicine_info: <Pill className="w-4 h-4" />,
  medical_news: <Newspaper className="w-4 h-4" />,
  medical_report: <ClipboardList className="w-4 h-4" />,
  health_monitoring: <Stethoscope className="w-4 h-4" />,
  general_conversation: <MessageCircle className="w-4 h-4" />,
  nearby_clinic: <MapPin className="w-4 h-4" />
};

const ResponseCard = ({ data }: ResponseCardProps) => {
  const icon = toolIcons[data.tool_type] ?? <Activity className="w-4 h-4" />;
  const label = TOOL_LABELS[data.tool_type] ?? data.tool_type;

  return (
    <motion.div
      className="clinical-card-elevated p-6 space-y-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Tool type badge */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="inline-flex items-center gap-2 px-3 py-1 text-xs font-semibold rounded-full bg-primary/10 text-primary">
          {icon}
          {label}
        </span>
      </div>

      {/* Medicine classifier — special detail card */}
      {data.tool_type === "medicine_info" && data.medicine_data ? (
        <MedicineClassifierCard data={data.medicine_data} />
      ) : data.tool_type === "medical_news" && data.news_data ? (
        /* Premium accordion-style news card */
        <NewsCard data={data.news_data} textResponse={data.text_response} />
      ) : data.tool_type === "medical_report" && data.report_data ? (
        /* Medical Report summary — matches current MedicalReportData shape */
        <div className="space-y-4">
          <p className="text-foreground leading-relaxed">{data.text_response}</p>

          {/* Stats row */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-muted/50 text-center">
              <p className="text-2xl font-bold text-primary">
                {data.report_data.detailed_logs?.length ?? 0}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">Health Logs</p>
            </div>
            <div className="p-3 rounded-xl bg-muted/50 text-center">
              <p className="text-2xl font-bold text-emerald-400">
                {data.report_data.health_tips?.length ?? 0}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">AI Tips</p>
            </div>
          </div>

          {/* Condition badge */}
          {data.report_data.chronic_disease && (
            <div className="flex items-center gap-2 text-xs">
              <HeartPulse className="w-3.5 h-3.5 text-primary shrink-0" />
              <span className="text-muted-foreground">Condition tracked:</span>
              <span className="font-semibold text-foreground">{data.report_data.chronic_disease}</span>
            </div>
          )}

          {/* Health tips preview */}
          {data.report_data.health_tips && data.report_data.health_tips.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1.5">
                <Lightbulb className="w-3.5 h-3.5 text-amber-400" /> AI Clinical Tips
              </p>
              <ul className="text-sm text-foreground space-y-1.5">
                {data.report_data.health_tips.slice(0, 3).map((tip, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-primary shrink-0">{i + 1}.</span>
                    <span className="line-clamp-2">{tip}</span>
                  </li>
                ))}
              </ul>
              {data.report_data.health_tips.length > 3 && (
                <p className="text-xs text-muted-foreground mt-1">
                  +{data.report_data.health_tips.length - 3} more tips in full report…
                </p>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-foreground leading-relaxed">{data.text_response}</p>
          {data.map_data && (
            <div className="mt-4 bg-card border border-border/50 p-4 rounded-xl shadow-sm space-y-3">
              <div className="flex items-center gap-1.5 text-primary font-medium text-xs mb-1">
                <MapPin className="w-3.5 h-3.5" />
                Nearby Facilities near {data.map_data.search_location || "you"}
              </div>
              <MapComponent mapData={data.map_data} />
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
};

export default ResponseCard;
