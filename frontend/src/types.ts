export type SeverityBand = "LOW" | "MODERATE" | "HIGH";
export type AdvisorySource = "bypass" | "llm" | "fallback";

export interface User {
  id: number;
  email: string;
}

export interface StageSummary {
  id: string;
  name: string;
  bbch: string;
  order: number;
}

export interface CropSummary {
  id: string;
  common_name: string;
  scientific_name: string;
  stages: StageSummary[];
}

export interface GeocodeCandidate {
  display_name: string;
  city: string | null;
  state: string | null;
  country: string | null;
  country_code: string | null;
  latitude: number;
  longitude: number;
}

export interface LatestRiskSummary {
  score: number;
  severity: SeverityBand;
  primary_threat: string;
  created_at: string;
  is_stale: boolean;
}

export interface PlotSummary {
  id: number;
  name: string;
  crop: {
    id: string;
    common_name: string;
  };
  stage: {
    id: string;
    name: string;
    bbch: string;
  };
  location_name: string;
  latitude?: number;
  longitude?: number;
  sowing_date: string;
  days_after_sowing: number;
  latest_risk: LatestRiskSummary | null;
}

export interface PlotCreateInput {
  name: string;
  crop_id: string;
  stage_id: string;
  location_name: string;
  latitude: number;
  longitude: number;
  sowing_date: string;
}

export interface PlotUpdateInput {
  name?: string;
  crop_id?: string;
  stage_id?: string;
  location_name?: string;
  latitude?: number;
  longitude?: number;
  sowing_date?: string;
}

export interface ActionItem {
  timeframe: "immediate_24h" | "preventative_72h";
  directive: string;
}

export interface AdvisoryData {
  headline: string;
  impact_analysis: string;
  actions: ActionItem[];
  monitoring_focus: string;
  source: AdvisorySource;
}

export interface WeatherDigest {
  peak_temp_c: number;
  min_temp_c: number;
  total_rain_mm: number;
  max_wind_kmh: number;
  peak_humidity_pct: number;
  longest_disease_window_h: number;
}

export interface ForecastInterval {
  timestamp: string;
  temperature_c: number;
  relative_humidity: number;
  wind_kmh: number;
  rain_mm: number;
}

export interface PlotDetailInfo {
  id: number;
  name: string;
  crop: string;
  crop_id?: string;
  scientific_name: string;
  stage: string;
  stage_id?: string;
  bbch: string;
  location_name: string;
  latitude?: number;
  longitude?: number;
  sowing_date: string;
  days_after_sowing: number;
}

export interface RiskDetailInfo {
  score: number;
  severity: SeverityBand;
  primary_threat: string;
  hazard_indices: {
    heat: number;
    frost: number;
    precip: number;
    disease: number;
    wind: number;
  };
  created_at: string;
  is_stale: boolean;
}

export interface PlotRiskResponse {
  plot: PlotDetailInfo;
  risk: RiskDetailInfo;
  advisory: AdvisoryData;
  weather: {
    digest: WeatherDigest;
    intervals: ForecastInterval[];
  };
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    fields?: Record<string, string>;
  };
}
