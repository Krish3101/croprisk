import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { PlotDetail } from "../pages/PlotDetail";
import { api, ApiError } from "../api";
import { PlotRiskResponse, PlotSummary } from "../types";

function riskResponse(fetchedMinutesAgo: number, refreshed: boolean): PlotRiskResponse {
  const fetchedAt = new Date(Date.now() - fetchedMinutesAgo * 60_000).toISOString();
  return {
    plot: {
      id: 1,
      name: "North Field",
      crop: "Wheat",
      crop_id: "wheat",
      scientific_name: "Triticum aestivum",
      stage: "Flowering / Anthesis",
      stage_id: "wheat.anthesis",
      bbch: "61–69",
      location_name: "Ludhiana, Punjab, IN",
      sowing_date: "2026-01-15",
      days_after_sowing: 100,
    },
    risk: {
      score: 33,
      severity: "MODERATE",
      primary_threat: "Extreme Heat",
      hazard_indices: { heat: 40, frost: 0, precip: 0, disease: 0, wind: 0 },
      created_at: fetchedAt,
      forecast_fetched_at: fetchedAt,
      is_stale: false,
    },
    advisory: {
      headline: "Heat stress risk for Wheat at Flowering / Anthesis",
      impact_analysis: "Over the next five days the peak temperature is 31 °C.",
      actions: [{ timeframe: "immediate_24h", directive: "Irrigate lightly in the evening." }],
      monitoring_focus: "Watch the peak temperature.",
      source: "fallback",
    },
    weather: {
      digest: {
        peak_temp_c: 31,
        min_temp_c: 18,
        total_rain_mm: 0,
        max_wind_kmh: 12,
        peak_humidity_pct: 70,
        longest_disease_window_h: 0,
      },
      intervals: [],
    },
    refreshed,
  };
}

function renderDetail(plots: PlotSummary[] = []) {
  vi.spyOn(api, "getCrops").mockResolvedValue([]);
  vi.spyOn(api, "getPlots").mockResolvedValue(plots);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/plots/1"]}>
        <Routes>
          <Route path="/plots/:id" element={<PlotDetail />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("PlotDetail", () => {
  afterEach(() => vi.restoreAllMocks());

  it("disables Recalculate and says when it last updated after refreshed:false", async () => {
    vi.spyOn(api, "getPlotRisk").mockResolvedValue(riskResponse(30, false));
    // Another tab fetched a forecast 2 minutes ago, so the server is in its cooldown.
    const refresh = vi.spyOn(api, "refreshPlotRisk").mockResolvedValue(riskResponse(2, false));
    renderDetail();

    const button = await screen.findByRole("button", { name: /Recalculate/ });
    expect(button).toBeEnabled();
    fireEvent.click(button);

    await waitFor(() => expect(screen.getByText("Updated 2 min ago")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /Recalculate/ })).toBeDisabled();
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("offers Edit on a direct page load", async () => {
    vi.spyOn(api, "getPlotRisk").mockResolvedValue(riskResponse(30, false));
    renderDetail([
      {
        id: 1,
        name: "North Field",
        crop: { id: "wheat", common_name: "Wheat" },
        stage: { id: "wheat.anthesis", name: "Flowering / Anthesis", bbch: "61–69" },
        location_name: "Ludhiana, Punjab, IN",
        latitude: 30.9,
        longitude: 75.85,
        sowing_date: "2026-01-15",
        days_after_sowing: 100,
        latest_risk: null,
      },
    ]);

    expect(await screen.findByRole("button", { name: "Edit field" })).toBeInTheDocument();
  });

  it("offers only Back on a 404", async () => {
    vi.spyOn(api, "getPlotRisk").mockRejectedValue(new ApiError("not_found", "Plot 1 not found.", 404));
    renderDetail();

    expect(await screen.findByRole("heading", { name: "Field not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Back to Dashboard/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
  });

  it("explains a 503 in plain words", { timeout: 8000 }, async () => {
    vi.spyOn(api, "getPlotRisk").mockRejectedValue(
      new ApiError("upstream_unavailable", "Weather provider unavailable.", 503)
    );
    renderDetail();

    expect(
      await screen.findByText(
        "We couldn't get a forecast for this field. This usually clears in a few minutes.",
        {},
        { timeout: 4000 } // the page retries a 5xx once before showing the error
      )
    ).toBeInTheDocument();
  });
});
