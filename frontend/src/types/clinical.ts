// frontend/src/types/clinical.ts
// ── TypeScript type definitions for the Voice AI Healthcare Assistant ──

// ── Main API response from /api/process ───────────────────────────
export interface ApiResponse {
  text_response: string;
  audio_url: string;
  tool_type: string;
  medicine_data?: MedicineData;
  report_data?: MedicalReportData;
  news_data?: NewsData;
  map_data?: any;
  latency_ms?: number;
  session_id?: string;
}

// ── Medical News Tool output ───────────────────────────────────────
export interface NewsArticle {
  title: string;
  source: string;
  date: string;
  url: string;
  summary: string;
  valid: boolean;
}

export interface NewsData {
  topic: string;
  articles: NewsArticle[];
  count: number;
  source?: string;
  success: boolean;
  message?: string;
}

// ── Medicine Classifier Tool output ───────────────────────────────
export interface MedicineData {
  medicine_name: string;
  chemical_composition: string;
  drug_category: string;
  purpose: string;
  basic_safety_notes: string;
  disclaimer: string;
  input_mode: "voice" | "text" | "image";
}

// ── Medical Report Tool output ────────────────────────────────────
export interface MedicalReportData {
  session_id: string;
  generated_at: string;
  total_interactions: number;
  topics_discussed: string[];
  health_metrics: {
    total_entries?: number;
    condition?: string;
    latest_systolic_bp?: number;
    latest_diastolic_bp?: number;
    latest_fasting_sugar?: number;
    latest_postmeal_sugar?: number;
    latest_weight_kg?: number;
    mood?: string;
    symptoms?: string[];
    notes?: string;
  };
  has_health_data: boolean;
  has_conversation_data: boolean;
  disclaimer: string;
  audio_url?: string;
}

// ── Health Log Entry ──────────────────────────────────────────────
export interface HealthLogEntry {
  session_id: string;
  condition: string;
  chronic_disease?: string;
  systolic_bp?: number;
  diastolic_bp?: number;
  sugar_fasting?: number;
  sugar_postmeal?: number;
  weight_kg?: number;
  mood?: string;
  symptoms?: string[];
  notes?: string;
}

// ── Flagged health threshold reading ─────────────────────────────
export interface FlaggedReading {
  timestamp: string;
  field: string;
  value: number;
  level: "warning" | "danger";
  note?: string;
}

// ── Full health analysis result from /api/health-summary ─────────
export interface HealthAnalysis {
  summary: string;
  flagged_readings: FlaggedReading[];
  diet_suggestions: string[];
  lifestyle_recommendations: string[];
  mental_health_guidance: string;
  daily_checklist: string[];
  disclaimer: string;
  audio_url?: string;
  session_id?: string;
}

// ── App status for UI state machine ──────────────────────────────
export type AppStatus = "idle" | "recording" | "processing" | "error" | "ready";

// ── Intent display labels ─────────────────────────────────────────
export const TOOL_LABELS: Record<string, string> = {
  medicine_info: "Medicine Info",
  medical_news: "Medical News",
  medical_report: "Medical Report",
  health_monitoring: "Health Monitoring",
  general_conversation: "General Chat",
  nearby_clinic: "Nearby Facility",
};

// ── Chat message in session history ──────────────────────────────
export interface ChatMessage {
  id: string;
  query: string;
  response: ApiResponse;
  timestamp: Date;
}
