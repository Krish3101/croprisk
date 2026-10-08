import {
  CropSummary,
  GeocodeCandidate,
  PlotRequest,
  AssessmentResponse,
  PlotSummary,
} from "./types";

export class ApiError extends Error {
  fields?: Record<string, string>;
  statusCode: number;

  constructor(message: string, statusCode: number, fields?: Record<string, string>) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.fields = fields;
  }
}

// FastAPI sends detail as a string, or as a list of {loc, msg} for validation errors
type ErrorDetail = string | { loc?: (string | number)[]; msg?: string }[];

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const defaultHeaders: Record<string, string> = {};
  if (options.body && typeof options.body === "string") {
    defaultHeaders["Content-Type"] = "application/json";
  }

  const response = await fetch(path, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (response.status === 204) {
    return {} as T;
  }

  let data: unknown;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail = (data as { detail?: ErrorDetail } | null)?.detail;
    if (Array.isArray(detail)) {
      const fields: Record<string, string> = {};
      for (const item of detail) {
        const field = String(item.loc?.[item.loc.length - 1] ?? "body");
        fields[field] = (item.msg ?? "Invalid value.").replace(/^Value error, /, "");
      }
      throw new ApiError(Object.values(fields)[0] ?? "Invalid input.", response.status, fields);
    }
    const message = typeof detail === "string" ? detail : `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status);
  }

  return data as T;
}

export const api = {
  getCrops: () => request<CropSummary[]>("/api/crops"),

  searchGeocode: (q: string) =>
    request<GeocodeCandidate[]>(`/api/geocode?q=${encodeURIComponent(q)}`),

  getPlots: () => request<PlotSummary[]>("/api/plots"),

  createPlot: (data: PlotRequest) =>
    request<PlotSummary>("/api/plots", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updatePlot: (plotId: number, data: PlotRequest) =>
    request<PlotSummary>(`/api/plots/${plotId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deletePlot: (plotId: number) =>
    request<void>(`/api/plots/${plotId}`, {
      method: "DELETE",
    }),

  getAssessment: (plotId: number) => request<AssessmentResponse>(`/api/plots/${plotId}/assessment`),

  refreshAssessment: (plotId: number) =>
    request<AssessmentResponse>(`/api/plots/${plotId}/assessment/refresh`, {
      method: "POST",
    }),
};
