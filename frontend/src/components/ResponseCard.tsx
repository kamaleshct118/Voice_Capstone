import React from "react";
import { motion } from "framer-motion";
import {
  Stethoscope, Pill, FileText, Activity, Newspaper,
  MessageCircle, ClipboardList,
} from "lucide-react";
import type { ApiResponse } from "@/types/clinical";
import { TOOL_LABELS } from "@/types/clinical";
import MedicineClassifierCard from "./MedicineClassifierCard";

interface ResponseCardProps {
  data: ApiResponse;
}

const toolIcons: Record<string, React.ReactNode> = {
  medicine_info: <Pill className="w-4 h-4" />,
  medical_news: <Newspaper className="w-4 h-4" />,
  medical_report: <ClipboardList className="w-4 h-4" />,
  health_monitoring: <Stethoscope className="w-4 h-4" />,
  general_conversation: <MessageCircle className="w-4 h-4" />,
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
      ) : data.tool_type === "medical_report" && data.report_data ? (
        /* Medical Report summary */
        <div className="space-y-3">
          <p className="text-foreground leading-relaxed">{data.text_response}</p>
          <div className="grid grid-cols-2 gap-3 mt-2">
            <div className="p-3 rounded-xl bg-muted/50 text-center">
              <p className="text-2xl font-bold text-primary">
                {data.report_data.total_interactions}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">Interactions</p>
            </div>
            <div className="p-3 rounded-xl bg-muted/50 text-center">
              <p className="text-2xl font-bold text-emerald-400">
                {data.report_data.health_metrics?.total_entries ?? 0}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">Health Logs</p>
            </div>
          </div>
          {data.report_data.topics_discussed.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                Topics Discussed
              </p>
              <ul className="text-sm text-foreground space-y-1">
                {data.report_data.topics_discussed.slice(0, 5).map((t, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-primary">•</span>
                    <span className="line-clamp-1">{t}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <p className="text-foreground leading-relaxed">{data.text_response}</p>
      )}
    </motion.div>
  );
};

export default ResponseCard;
