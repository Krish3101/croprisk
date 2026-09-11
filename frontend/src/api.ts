import {
  ApiErrorEnvelope,
  CropSummary,
  GeocodeCandidate,
  PlotCreateInput,
  PlotRiskResponse,
  PlotSummary,
  PlotUpdateInput,
  User,
} from "./types";

export class ApiError extends Error {
  code: string;
  fields?: Record<string, string>;
  statusCode: number;

  constructor(code: string, message: string, statusCode: number, fields?: Record<string, string>) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.statusCode = statusCode;
    this.fields = fields;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const defaultHeaders: Record<string, string> = {};
  if (options.body && typeof options.body === "string") {
    defaultHeaders["Content-Type"] = "application/json";
  }

  const response = await fetch(path, {
    credentials: "include",
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
    const errorEnv = data as ApiErrorEnvelope | null;
    if (errorEnv && errorEnv.error) {
      throw new ApiError(
        errorEnv.error.code || "unknown_error",
        errorEnv.error.message || "An unexpected error occurred.",
        response.status,
        errorEnv.error.fields
      );
    }
    throw new ApiError("http_error", `Request failed with status ${response.status}`, response.status);
  }

  return data as T;
}

export const api = {
  register: (email: string, password: string) =>
    request<User>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<User>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  logout: () =>
    request<void>("/api/auth/logout", {
      method: "POST",
    }),

  getMe: () => request<User>("/api/auth/me"),

  getCrops: () => request<CropSummary[]>("/api/crops"),

  searchGeocode: (q: string) =>
    request<GeocodeCandidate[]>(`/api/geocode?q=${encodeURIComponent(q)}`),

  getPlots: () => request<PlotSummary[]>("/api/plots"),

  createPlot: (data: PlotCreateInput) =>
    request<PlotSummary>("/api/plots", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updatePlot: (plotId: number, data: PlotUpdateInput) =>
    request<PlotSummary>(`/api/plots/${plotId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deletePlot: (plotId: number) =>
    request<void>(`/api/plots/${plotId}`, {
      method: "DELETE",
    }),

  getPlotRisk: (plotId: number, refresh: boolean = false) =>
    request<PlotRiskResponse>(`/api/plots/${plotId}/risk${refresh ? "?refresh=true" : ""}`),
};
