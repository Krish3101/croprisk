import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import { PlotCreateInput } from "../types";
import { PlotCard } from "../components/PlotCard";
import { PlotDialog } from "../components/PlotDialog";

export const Dashboard: React.FC = () => {
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const {
    data: plots = [],
    isLoading: plotsLoading,
    error: plotsError,
    refetch: refetchPlots,
  } = useQuery({
    queryKey: ["plots"],
    queryFn: api.getPlots,
  });

  const { data: crops = [] } = useQuery({
    queryKey: ["crops"],
    queryFn: api.getCrops,
  });

  const createMutation = useMutation({
    mutationFn: (data: PlotCreateInput) => api.createPlot(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plots"] });
    },
  });

  const highRiskCount = plots.filter((p) => p.latest_risk?.severity === "HIGH").length;
  const modRiskCount = plots.filter((p) => p.latest_risk?.severity === "MODERATE").length;
  const lowRiskCount = plots.filter((p) => p.latest_risk?.severity === "LOW").length;

  if (plotsLoading) {
    return (
      <div
        role="status"
        className="min-h-screen bg-stone-100 flex items-center justify-center text-stone-600 text-sm"
      >
        Loading grower dashboard...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-100 pb-12">
      <header className="bg-white border-b border-stone-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl font-black text-emerald-800 tracking-tight">
              CropRisk
            </span>
            <span className="hidden md:inline-block text-xs text-stone-500 font-medium border-l border-stone-200 pl-3">
              Crop &amp; growth-stage aware weather risk engine
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black text-stone-900">Your fields</h1>
            <p className="text-sm text-stone-600 mt-1 max-w-2xl">
              Same weather, different risk: heat, frost, rain, fungal and wind hazards scored per
              crop and growth stage. Next five days, most urgent first.
            </p>
          </div>

          <button
            onClick={() => setIsDialogOpen(true)}
            className="self-start sm:self-auto inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-sm font-bold rounded-lg shadow-sm transition"
          >
            + Add field
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white p-4 rounded-lg border border-stone-200 shadow-sm">
            <span className="text-xs font-semibold text-stone-600 uppercase tracking-wide">
              Total Fields
            </span>
            <p className="text-2xl font-black text-stone-900 mt-1 tabular-nums">
              {plots.length}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-stone-200 shadow-sm">
            <span className="text-xs font-semibold text-rose-700 uppercase tracking-wide flex items-center gap-1">
              <span aria-hidden="true">⚠</span> High Risk
            </span>
            <p className="text-2xl font-black text-rose-700 mt-1 tabular-nums">
              {highRiskCount}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-stone-200 shadow-sm">
            <span className="text-xs font-semibold text-amber-700 uppercase tracking-wide flex items-center gap-1">
              <span aria-hidden="true">▲</span> Moderate Risk
            </span>
            <p className="text-2xl font-black text-amber-700 mt-1 tabular-nums">
              {modRiskCount}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-stone-200 shadow-sm">
            <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wide flex items-center gap-1">
              <span aria-hidden="true">✓</span> Low Risk
            </span>
            <p className="text-2xl font-black text-emerald-700 mt-1 tabular-nums">
              {lowRiskCount}
            </p>
          </div>
        </div>

        {plotsError ? (
          <div
            role="alert"
            className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-800 flex items-center justify-between"
          >
            <span>Failed to load fields. Please check your connection and retry.</span>
            <button
              onClick={() => refetchPlots()}
              className="px-3 py-1 bg-white border border-rose-300 text-rose-800 rounded font-semibold text-xs hover:bg-rose-100 transition"
            >
              Retry
            </button>
          </div>
        ) : plots.length === 0 ? (
          <div className="bg-white rounded-xl border border-stone-200 p-12 text-center shadow-sm space-y-3">
            <h2 className="text-lg font-bold text-stone-900">No fields registered yet</h2>
            <p className="text-sm text-stone-600 max-w-md mx-auto leading-relaxed">
              Add a field with its crop, growth stage and location. The 5-day forecast for that
              location is evaluated against physiological thresholds for that exact growth stage.
            </p>
            <button
              onClick={() => setIsDialogOpen(true)}
              className="mt-2 inline-flex items-center px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-sm font-bold rounded-md shadow-sm transition"
            >
              Add Your First Field
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {plots.map((plot) => (
              <PlotCard key={plot.id} plot={plot} />
            ))}
          </div>
        )}
      </main>

      <PlotDialog
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        onSave={async (data) => {
          await createMutation.mutateAsync(data);
        }}
        crops={crops}
      />
    </div>
  );
};
