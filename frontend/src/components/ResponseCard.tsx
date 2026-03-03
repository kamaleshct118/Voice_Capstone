import { motion } from "framer-motion";
import { MapPin, Stethoscope, Pill, FileText, Activity } from "lucide-react";
import type { ApiResponse } from "@/types/clinical";
import { TOOL_LABELS } from "@/types/clinical";

interface ResponseCardProps {
  data: ApiResponse;
  onShowMap: () => void;
}

const toolIcons: Record<string, React.ReactNode> = {
  medical_info: <Stethoscope className="w-4 h-4" />,
  nearby_clinic: <MapPin className="w-4 h-4" />,
  medicine_availability: <Pill className="w-4 h-4" />,
  summary: <FileText className="w-4 h-4" />,
};

const ResponseCard = ({ data, onShowMap }: ResponseCardProps) => {
  const icon = toolIcons[data.tool_type] || <Activity className="w-4 h-4" />;
  const label = TOOL_LABELS[data.tool_type] || data.tool_type;

  return (
    <motion.div
      className="clinical-card-elevated p-6 space-y-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-center justify-between">
        <span className="inline-flex items-center gap-2 px-3 py-1 text-xs font-semibold rounded-full bg-primary/10 text-primary">
          {icon}
          {label}
        </span>
        {data.map_data && (
          <button
            onClick={onShowMap}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-clinical-green text-clinical-green-foreground hover:brightness-110 transition"
          >
            <MapPin className="w-3.5 h-3.5" />
            View on Map
          </button>
        )}
      </div>

      <p className="text-foreground leading-relaxed">{data.text_response}</p>

      {data.map_data && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground p-3 rounded-lg bg-muted">
          <MapPin className="w-4 h-4 text-clinical-green shrink-0" />
          <span>
            <strong className="text-foreground">{data.map_data.name}</strong>
            {data.map_data.contact && <> · {data.map_data.contact}</>}
          </span>
        </div>
      )}
    </motion.div>
  );
};

export default ResponseCard;
