export type SeverityBand = "LOW" | "MODERATE" | "HIGH";
export type AdvisorySource = "bypass" | "llm" | "fallback";
export type Hazard =
  | "Extreme Heat"
  | "Frost Damage"
  | "Excess Precipitation"
  | "Wind Lodging"
  | "Fungal Disease Pressure"
  | "None";

export interface StageSummary {
  id: string;
  name: string;
  bbch: string;
  order: number;
  t_crit_heat: number;
  t_crit_frost: number;
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
  latitude: number;
  longitude: number;
}

export interface LatestAssessment {
  score: number;
  severity: SeverityBand;
  primary_hazard: Hazard | string;
  created_at: string;
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
  latitude: number;
  longitude: number;
  sowing_date: string;
  days_after_sowing: number;
  latest_assessment: LatestAssessment | null;
}

// Mirrors PlotRequest: the body for adding a plot and for replacing one
export interface PlotRequest {
  name: string;
  crop_id: string;
  stage_id: string;
  location_name: string;
  latitude: number;
  longitude: number;
  sowing_date: string;
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
  crop_id: string;
  scientific_name: string;
  stage: string;
  stage_id: string;
  bbch: string;
  location_name: string;
  latitude?: number;
  longitude?: number;
  sowing_date: string;
  days_after_sowing: number;
}

export interface AssessmentDetail {
  score: number;
  severity: SeverityBand;
  primary_hazard: Hazard | string;
  hazard_indices: {
    heat: number;
    frost: number;
    precip: number;
    disease: number;
    wind: number;
  };
  created_at: string;
  forecast_fetched_at: string;
}

export interface AssessmentResponse {
  plot: PlotDetailInfo;
  assessment: AssessmentDetail;
  advisory: AdvisoryData;
  weather: {
    digest: WeatherDigest;
    intervals: ForecastInterval[];
  };
  // True when this response fetched a new forecast.
}

