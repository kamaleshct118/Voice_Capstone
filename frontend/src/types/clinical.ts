export interface ApiResponse {
  text_response: string;
  audio_url: string;
  tool_type: string;
  map_data?: MapData;
  medicine_data?: MedicineData;
  latency_ms?: number;
  session_id?: string;
}

export interface MapData {
  type?: string;
  search_location?: string;
  center_lat?: number;
  center_lng?: number;
  locations?: ClinicLocation[];
  // Legacy single-location support
  lat?: number;
  lng?: number;
  name?: string;
  contact?: string;
}

export interface ClinicLocation {
  name: string;
  address?: string;
  lat: number;
  lng: number;
  rating?: number;
  open_now?: boolean;
  phone?: string;
}

export interface MedicineData {
  medicine_name: string;
  chemical_composition: string;
  drug_category: string;
  purpose: string;
  basic_safety_notes: string;
  disclaimer: string;
  input_mode: "voice" | "text" | "image";
}

export interface HealthLogEntry {
  session_id: string;
  condition: string;
  systolic_bp?: number;
  diastolic_bp?: number;
  sugar_fasting?: number;
  sugar_postmeal?: number;
  weight_kg?: number;
  mood?: string;
  symptoms?: string[];
  notes?: string;
}

export interface FlaggedReading {
  timestamp: string;
  field: string;
  value: number;
  level: "warning" | "danger";
  note?: string;
}

export interface HealthAnalysis {
  summary: string;
  flagged_readings: FlaggedReading[];
  diet_suggestions: string[];
  lifestyle_recommendations: string[];
  mental_health_guidance: string;
  disclaimer: string;
  audio_url?: string;
  session_id?: string;
}

export type AppStatus = "idle" | "recording" | "processing" | "error" | "ready";

export const TOOL_LABELS: Record<string, string> = {
  medical_info: "Medical Info",
  medical_news: "Medical News",
  nearby_clinic: "Clinic Locator",
  medicine_classifier: "Medicine Classifier",
  health_monitor_analysis: "Health Monitor",
  consolidation_summary: "Session Summary",
};

export interface ChatMessage {
  id: string;
  query: string;
  response: ApiResponse;
  timestamp: Date;
}
