import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { PlotCreateInput } from "../types";
import { PlotCard } from "../components/PlotCard";
import { PlotDialog } from "../components/PlotDialog";

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const { data: currentUser, isError: authError } = useQuery({
    queryKey: ["authMe"],
    queryFn: api.getMe,
    retry: false,
  });

  React.useEffect(() => {
    if (authError) {
      navigate("/login");
    }
  }, [authError, navigate]);

  const { data: plots = [], isLoading: plotsLoading, error: plotsError } = useQuery({
    queryKey: ["plots"],
    queryFn: api.getPlots,
    enabled: Boolean(currentUser),
  });

  const { data: crops = [] } = useQuery({
    queryKey: ["crops"],
    queryFn: api.getCrops,
    enabled: Boolean(currentUser),
  });

  const createMutation = useMutation({
    mutationFn: (data: PlotCreateInput) => api.createPlot(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plots"] });
    },
  });

  const handleLogout = async () => {
    try {
      await api.logout();
    } finally {
      queryClient.clear();
      navigate("/login");
    }
  };

  const highRiskCount = plots.filter((p) => p.latest_risk?.severity === "HIGH").length;
  const modRiskCount = plots.filter((p) => p.latest_risk?.severity === "MODERATE").length;
  const lowRiskCount = plots.filter((p) => p.latest_risk?.severity === "LOW").length;

  if (plotsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-stone-500 text-sm">
        Loading grower dashboard...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-100 pb-12">
      <header className="bg-white border-b border-stone-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-black text-emerald-800 tracking-tight">
              CropRisk
            </span>
            <span className="hidden sm:inline text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
              Grower Triage
            </span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-xs sm:text-sm text-stone-600 font-medium">
              {currentUser?.email}
            </span>
            <button
              onClick={handleLogout}
              className="text-xs font-semibold px-3 py-1.5 rounded border border-stone-300 text-stone-700 hover:bg-stone-50 transition"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-black text-stone-900">Field Risk Triage</h1>
            <p className="text-xs text-stone-500">
              Deterministic 5-day weather hazard evaluations ordered by urgency
            </p>
          </div>

          <button
            onClick={() => setIsDialogOpen(true)}
            className="self-start sm:self-auto inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold rounded-lg shadow-sm transition"
          >
            + Register Field
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white p-4 rounded-lg border border-stone-200 shadow-sm">
            <span className="text-xs font-semibold text-stone-500 uppercase tracking-wide">
              Total Fields
            </span>
            <p className="text-2xl font-black text-stone-900 mt-1 tabular-nums">
              {plots.length}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-stone-200 shadow-sm">
            <span className="text-xs font-semibold text-rose-700 uppercase tracking-wide flex items-center gap-1">
              <span>⚠</span> High Risk
            </span>
            <p className="text-2xl font-black text-rose-700 mt-1 tabular-nums">
              {highRiskCount}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-stone-200 shadow-sm">
            <span className="text-xs font-semibold text-amber-700 uppercase tracking-wide flex items-center gap-1">
              <span>▲</span> Moderate Risk
            </span>
            <p className="text-2xl font-black text-amber-700 mt-1 tabular-nums">
              {modRiskCount}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-stone-200 shadow-sm">
            <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wide flex items-center gap-1">
              <span>✓</span> Low Risk
            </span>
            <p className="text-2xl font-black text-emerald-700 mt-1 tabular-nums">
              {lowRiskCount}
            </p>
          </div>
        </div>

        {plotsError ? (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800">
            Failed to load fields. Please refresh the page.
          </div>
        ) : plots.length === 0 ? (
          <div className="bg-white rounded-xl border border-stone-200 p-12 text-center shadow-sm space-y-3">
            <h2 className="text-base font-bold text-stone-800">No fields registered yet</h2>
            <p className="text-xs text-stone-500 max-w-md mx-auto leading-relaxed">
              Add a plot with its crop, growth stage and location. The forecast for that
              location is then scored against thresholds for that crop at that stage.
            </p>
            <button
              onClick={() => setIsDialogOpen(true)}
              className="mt-2 inline-flex items-center px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold rounded-md shadow-sm transition"
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
