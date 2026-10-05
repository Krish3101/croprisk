import React, { useEffect, useRef, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../api";
import { PlotCreateInput } from "../types";
import { ScoreBadge } from "../components/ScoreBadge";
import { HazardBars } from "../components/HazardBars";
import { Advisory } from "../components/Advisory";
import { ForecastChart } from "../components/ForecastChart";
import { PlotDialog } from "../components/PlotDialog";
import { DeleteDialog } from "../components/DeleteDialog";
import { DigestStrip } from "../components/DigestStrip";

// Matches the backend: a new forecast can be fetched 10 minutes after the last one.
const REFRESH_COOLDOWN_MS = 10 * 60 * 1000;

function formatDate(iso: string): string {
  const date = new Date(iso);
  if (isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

export const PlotDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const plotId = Number(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [isEditOpen, setIsEditOpen] = useState(false);
  const deleteDialogRef = useRef<HTMLDialogElement>(null);
  const [now, setNow] = useState(() => Date.now());

  // The plot list gives the edit form its initial values, also after a direct page load.
  const { data: plots } = useQuery({ queryKey: ["plots"], queryFn: api.getPlots });
  const initialPlot = plots?.find((p) => p.id === plotId);

  const { data: riskData, isPending, isRefetching, fetchStatus, error, refetch } = useQuery({
    queryKey: ["plotRisk", plotId],
    queryFn: () => api.getPlotRisk(plotId),
    enabled: !isNaN(plotId),
    retry: (failureCount, err) => {
      if (err instanceof ApiError && err.statusCode < 500) return false;
      return failureCount < 1;
    },
  });

  const { data: crops = [] } = useQuery({ queryKey: ["crops"], queryFn: api.getCrops });

  const refreshMutation = useMutation({
    mutationFn: () => api.refreshPlotRisk(plotId),
    onSuccess: (updated) => {
      queryClient.setQueryData(["plotRisk", plotId], updated);
      queryClient.invalidateQueries({ queryKey: ["plots"] });
    },
  });

  const editMutation = useMutation({
    mutationFn: (data: PlotCreateInput) => api.updatePlot(plotId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plotRisk", plotId] });
      queryClient.invalidateQueries({ queryKey: ["plots"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deletePlot(plotId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plots"] });
      navigate("/");
    },
  });

  // Re-enable Recalculate when the cooldown ends.
  useEffect(() => setNow(Date.now()), [riskData]);
  const fetchedAt = riskData ? Date.parse(riskData.risk.forecast_fetched_at) : NaN;
  const cooldownLeft = fetchedAt + REFRESH_COOLDOWN_MS - now;
  useEffect(() => {
    if (!(cooldownLeft > 0)) return;
    const timer = setTimeout(() => setNow(Date.now()), cooldownLeft);
    return () => clearTimeout(timer);
  }, [cooldownLeft]);

  const isNotFound = error instanceof ApiError && error.statusCode === 404;
  const plotName = riskData?.plot.name || initialPlot?.name || `Field #${plotId}`;

  const page = (content: React.ReactNode) => (
    <div className="min-h-screen bg-stone-100 pb-16">
      <header className="bg-white border-b border-stone-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link
            to="/"
            className="text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 flex items-center gap-1.5 transition"
          >
            ← Back to Dashboard
          </Link>
          {!isNotFound && (
            <div className="flex items-center gap-2">
              {initialPlot && (
                <button
                  onClick={() => setIsEditOpen(true)}
                  className="px-3 py-1.5 text-xs font-semibold rounded border border-stone-300 text-stone-700 hover:bg-stone-50 transition"
                >
                  Edit field
                </button>
              )}
              <button
                onClick={() => deleteDialogRef.current?.showModal()}
                className="px-3 py-1.5 text-xs font-semibold rounded border border-rose-200 text-rose-700 hover:bg-rose-50 transition"
              >
                Delete
              </button>
            </div>
          )}
        </div>
      </header>
      {content}
      <DeleteDialog
        ref={deleteDialogRef}
        plotName={plotName}
        onConfirm={() => deleteMutation.mutateAsync()}
      />
    </div>
  );

  if (isPending && fetchStatus === "paused") {
    return page(
      <main className="max-w-4xl mx-auto p-6 mt-12">
        <div className="bg-stone-50 border border-stone-300 rounded-xl p-6 text-center space-y-3">
          <h1 className="text-lg font-bold text-stone-900">Waiting for a connection</h1>
          <p className="text-sm text-stone-600 max-w-md mx-auto">
            The risk assessment needs the network. It will evaluate as soon as your device reconnects.
          </p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-stone-800 hover:bg-stone-900 text-white text-xs font-semibold rounded-md transition"
          >
            Try again
          </button>
        </div>
      </main>
    );
  }

  if (isPending) {
    return page(
      <main className="max-w-4xl mx-auto p-6 mt-12">
        <div role="status" className="flex items-center justify-center text-stone-600 text-sm">
          Computing agronomic risk against current 5-day weather...
        </div>
      </main>
    );
  }

  if (error || !riskData) {
    let message = "We couldn't get a forecast for this field. This usually clears in a few minutes.";
    if (isNotFound) message = "This field was not found or has been deleted.";
    else if (error instanceof ApiError && error.statusCode !== 503) message = error.message;

    return page(
      <main className="max-w-4xl mx-auto p-6 mt-12">
        <div className="bg-rose-50 border border-rose-300 rounded-xl p-8 text-center space-y-4">
          <span className="text-3xl" aria-hidden="true">⚠</span>
          <h1 className="text-xl font-bold text-rose-900">
            {isNotFound ? "Field not found" : "Unable to assess field risk"}
          </h1>
          <p className="text-sm text-rose-800 max-w-md mx-auto">{message}</p>
          {!isNotFound && (
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-rose-700 hover:bg-rose-800 text-white text-xs font-semibold rounded-md transition"
            >
              Retry assessment
            </button>
          )}
        </div>
      </main>
    );
  }

  const { plot, risk, advisory, weather } = riskData;
  const currentStage = crops
    .find((c) => c.id === plot.crop_id)
    ?.stages.find((s) => s.id === plot.stage_id);
  const inCooldown = cooldownLeft > 0;
  const minutesAgo = Math.max(0, Math.floor((now - fetchedAt) / 60000));
  const refreshing = refreshMutation.isPending || isRefetching;

  return page(
    <>
      <main className="max-w-5xl mx-auto px-4 sm:px-6 pt-6 space-y-6">
        {risk.is_stale && (
          <div
            role="status"
            className="p-4 bg-amber-50 border border-amber-300 rounded-lg flex items-start gap-3 text-amber-900 text-sm"
          >
            <span className="text-base font-bold" aria-hidden="true">▲</span>
            <div>
              <p className="font-bold">Showing cached assessment</p>
              <p className="text-amber-800 text-xs mt-0.5">
                Showing the assessment saved on {formatDate(risk.forecast_fetched_at)}. The live
                weather provider is unreachable right now.
              </p>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg border border-stone-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1">
            <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider">
              Field Assessment
            </span>
            <h1 className="text-2xl font-black text-stone-900">{plot.name}</h1>
            <p className="text-sm text-stone-700">
              <span className="font-semibold">{plot.crop}</span> (<em>{plot.scientific_name}</em>)
              {" · "}
              Growth Stage: <span className="font-semibold">{plot.stage}</span> (BBCH {plot.bbch})
            </p>
            <p className="text-xs text-stone-600">
              {plot.location_name} · Sown {plot.sowing_date} ({plot.days_after_sowing} days ago)
            </p>
            <p className="text-[11px] text-stone-600 pt-1">
              Updated {formatDate(risk.forecast_fetched_at)} · Forecast: OpenWeather
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 border-t md:border-t-0 md:border-l border-stone-100 pt-4 md:pt-0 md:pl-6">
            <div className="space-y-1">
              <span className="text-xs text-stone-600 font-medium block">Aggregated Risk</span>
              <ScoreBadge score={risk.score} severity={risk.severity} size="lg" />
              <p className="text-xs text-stone-600 mt-1">
                Primary Threat:{" "}
                <strong className="text-stone-900">
                  {risk.primary_threat === "None" ? "No significant hazard" : risk.primary_threat}
                </strong>
              </p>
            </div>

            <div className="flex flex-col items-start gap-1">
              <button
                onClick={() => refreshMutation.mutate()}
                disabled={refreshing || inCooldown}
                title={inCooldown ? "A new forecast can be fetched 10 minutes after the last one." : undefined}
                className="px-3 py-2 bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-semibold rounded-md border border-stone-300 transition flex items-center gap-1.5 whitespace-nowrap disabled:opacity-50"
              >
                {refreshing ? "Refreshing..." : "↻ Recalculate"}
              </button>
              {riskData.refreshed === false && refreshMutation.isSuccess && (
                <p role="status" className="text-xs text-stone-600">
                  Updated {minutesAgo} min ago
                </p>
              )}
              {refreshMutation.error && (
                <p role="alert" className="text-xs text-rose-700 mt-1 max-w-[180px]">
                  {(refreshMutation.error as ApiError).message || "Refresh failed"}
                </p>
              )}
            </div>
          </div>
        </div>

        <DigestStrip digest={weather.digest} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <HazardBars indices={risk.hazard_indices} />
          </div>
          <div className="lg:col-span-2">
            <Advisory advisory={advisory} />
          </div>
        </div>

        {currentStage && (
          <ForecastChart
            intervals={weather.intervals}
            tCritHeat={currentStage.t_crit_heat}
            tCritFrost={currentStage.t_crit_frost}
          />
        )}
      </main>

      <PlotDialog
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        onSave={async (data) => {
          await editMutation.mutateAsync(data);
          setIsEditOpen(false);
          await refetch();
        }}
        crops={crops}
        initialData={initialPlot}
      />
    </>
  );
};
