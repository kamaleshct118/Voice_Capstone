export interface ApiResponse {
  text_response: string;
  audio_url: string;
  tool_type: string;
  map_data?: MapData;
}

export interface MapData {
  lat: number;
  lng: number;
  name: string;
  contact?: string;
}

export type AppStatus = "idle" | "recording" | "processing" | "error" | "ready";

export const TOOL_LABELS: Record<string, string> = {
  medical_info: "Medical Info",
  nearby_clinic: "Clinic Locator",
  medicine_availability: "Medicine Availability",
  summary: "Summary",
};

export interface ChatMessage {
  id: string;
  query: string;
  response: ApiResponse;
  timestamp: Date;
}
