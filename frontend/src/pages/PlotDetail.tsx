import React, { useRef, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../api";
import { PlotCreateInput } from "../types";
import { ScoreBadge } from "../components/ScoreBadge";
import { HazardBars } from "../components/HazardBars";
import { Advisory } from "../components/Advisory";
import { ForecastChart } from "../components/ForecastChart";
import { PlotDialog } from "../components/PlotDialog";

export const PlotDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const plotId = Number(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [isEditOpen, setIsEditOpen] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const deleteDialogRef = useRef<HTMLDialogElement>(null);

  const {
    data: riskData,
    isPending,
    isRefetching,
    fetchStatus,
    error,
    refetch,
  } = useQuery({
    queryKey: ["plotRisk", plotId],
    queryFn: () => api.getPlotRisk(plotId, false),
    enabled: !isNaN(plotId),
    retry: 1,
  });

  const { data: crops = [] } = useQuery({
    queryKey: ["crops"],
    queryFn: api.getCrops,
  });

  const refreshMutation = useMutation({
    mutationFn: () => api.getPlotRisk(plotId, true),
    onSuccess: (updated) => {
      queryClient.setQueryData(["plotRisk", plotId], updated);
      queryClient.invalidateQueries({ queryKey: ["plots"] });
    },
  });

  const editMutation = useMutation({
    mutationFn: (data: PlotCreateInput) => api.updatePlot(plotId, data),
    onSuccess: () => {
      // Editing invalidates the assessment; refetch will recompute against the new stage
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

  const handleDelete = async () => {
    setDeleteLoading(true);
    try {
      await deleteMutation.mutateAsync();
    } finally {
      setDeleteLoading(false);
      if (deleteDialogRef.current?.open) {
        deleteDialogRef.current.close();
      }
    }
  };

  const openDeleteModal = () => {
    deleteDialogRef.current?.showModal();
  };

  const closeDeleteModal = () => {
    deleteDialogRef.current?.close();
  };

  // A paused query is pending with nothing in flight and no error, so without this branch
  // the component would fall through to the null return below and render a blank page.
  if (isPending && fetchStatus === "paused") {
    return (
      <div className="max-w-4xl mx-auto p-6 mt-12">
        <div className="bg-stone-50 border border-stone-300 rounded-xl p-6 text-center space-y-3">
          <h2 className="text-base font-bold text-stone-900">Waiting for a connection</h2>
          <p className="text-xs text-stone-600 max-w-md mx-auto">
            The risk assessment needs the network. It will run as soon as you are back online.
          </p>
          <div className="pt-2 flex justify-center gap-3">
            <Link
              to="/"
              className="px-4 py-2 bg-stone-200 hover:bg-stone-300 text-stone-800 text-xs font-semibold rounded-md transition"
            >
              ← Back to Dashboard
            </Link>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-stone-700 hover:bg-stone-800 text-white text-xs font-semibold rounded-md transition"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isPending) {
    return (
      <div className="min-h-screen flex items-center justify-center text-stone-500 text-sm">
        Computing agronomic risk against current 5-day weather...
      </div>
    );
  }

  if (error) {
    const errorMsg =
      error instanceof ApiError
        ? error.message
        : "Failed to evaluate field risk. Weather service may be unreachable.";
    return (
      <div className="max-w-4xl mx-auto p-6 mt-12">
        <div className="bg-rose-50 border border-rose-300 rounded-xl p-6 text-center space-y-3">
          <span className="text-3xl">⚠</span>
          <h2 className="text-base font-bold text-rose-900">Unable to assess field risk</h2>
          <p className="text-xs text-rose-700 max-w-md mx-auto">{errorMsg}</p>
          <div className="pt-2 flex justify-center gap-3">
            <Link
              to="/"
              className="px-4 py-2 bg-stone-200 hover:bg-stone-300 text-stone-800 text-xs font-semibold rounded-md transition"
            >
              ← Back to Dashboard
            </Link>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-rose-700 hover:bg-rose-800 text-white text-xs font-semibold rounded-md transition"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!riskData) return null;

  const { plot, risk, advisory, weather } = riskData;

  const currentCrop = crops.find((c) => c.common_name === plot.crop || c.scientific_name === plot.scientific_name);
  // Default thresholds if not yet matched (wheat anthesis default: 27 / 1)
  const tCritHeat = 27.0;
  const tCritFrost = 1.0;

  return (
    <div className="min-h-screen bg-stone-100 pb-16">
      <header className="bg-white border-b border-stone-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link
            to="/"
            className="text-xs font-semibold text-stone-600 hover:text-stone-900 flex items-center gap-1.5 transition"
          >
            ← Back to Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsEditOpen(true)}
              className="px-3 py-1.5 text-xs font-semibold rounded border border-stone-300 text-stone-700 hover:bg-stone-50 transition"
            >
              Edit Field / Stage
            </button>
            <button
              onClick={openDeleteModal}
              className="px-3 py-1.5 text-xs font-semibold rounded border border-rose-200 text-rose-700 hover:bg-rose-50 transition"
            >
              Delete
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 pt-6 space-y-6">
        {risk.is_stale && (
          <div className="p-4 bg-amber-50 border border-amber-300 rounded-lg flex items-start gap-3 text-amber-900 text-xs sm:text-sm">
            <span className="text-base font-bold">▲</span>
            <div>
              <p className="font-bold">Live weather provider is currently unreachable</p>
              <p className="text-amber-800 text-xs mt-0.5">
                Serving stored risk assessment calculated on {new Date(risk.created_at).toLocaleString()}.
                Freshness rules guarantee this answers the current growth stage.
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
            <p className="text-xs sm:text-sm text-stone-600">
              <span className="font-semibold text-stone-800">{plot.crop}</span> (<em>{plot.scientific_name}</em>)
              {" · "}
              Growth Stage: <span className="font-semibold text-stone-800">{plot.stage}</span> (BBCH {plot.bbch})
            </p>
            <p className="text-xs text-stone-500">
              {plot.location_name} · Sown {plot.sowing_date} ({plot.days_after_sowing} days ago)
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 border-t md:border-t-0 md:border-l border-stone-100 pt-4 md:pt-0 md:pl-6">
            <div className="space-y-1">
              <span className="text-xs text-stone-500 font-medium block">Aggregated Risk</span>
              <ScoreBadge score={risk.score} severity={risk.severity} size="lg" />
              <p className="text-xs text-stone-500 mt-1">
                Primary Threat: <strong className="text-stone-900">{risk.primary_threat}</strong>
              </p>
            </div>

            <button
              onClick={() => refreshMutation.mutate()}
              disabled={refreshMutation.isPending || isRefetching}
              className="px-3 py-2 bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-semibold rounded-md border border-stone-300 transition flex items-center gap-1.5 self-stretch sm:self-auto justify-center disabled:opacity-50"
            >
              {refreshMutation.isPending || isRefetching ? "Refreshing..." : "↻ Recalculate Now"}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <HazardBars indices={risk.hazard_indices} />
          </div>
          <div className="lg:col-span-2">
            <Advisory advisory={advisory} />
          </div>
        </div>

        <ForecastChart
          intervals={weather.intervals}
          tCritHeat={tCritHeat}
          tCritFrost={tCritFrost}
        />
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
        initialData={{
          id: plot.id,
          name: plot.name,
          crop: { id: plot.crop_id || currentCrop?.id || "wheat", common_name: plot.crop },
          stage: { id: plot.stage_id || "wheat.tillering", name: plot.stage, bbch: plot.bbch },
          location_name: plot.location_name,
          latitude: plot.latitude,
          longitude: plot.longitude,
          sowing_date: plot.sowing_date,
          days_after_sowing: plot.days_after_sowing,
          latest_risk: null,
        }}
      />

      <dialog
        ref={deleteDialogRef}
        onClose={closeDeleteModal}
        className="p-0 rounded-xl shadow-2xl backdrop:bg-stone-900/40 w-full max-w-sm border border-stone-200"
      >
        <div className="p-6 space-y-4 bg-white text-stone-900">
          <h3 className="text-base font-bold text-rose-900">Delete {plot.name}?</h3>
          <p className="text-xs text-stone-600 leading-relaxed">
            Are you sure you want to delete this field? Its historical assessments and data will be permanently removed.
          </p>
          <div className="flex justify-end gap-2 pt-2 border-t border-stone-100">
            <button
              type="button"
              onClick={closeDeleteModal}
              disabled={deleteLoading}
              className="px-3 py-1.5 text-xs font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200 rounded-md transition"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDelete}
              disabled={deleteLoading}
              className="px-3 py-1.5 text-xs font-semibold text-white bg-rose-700 hover:bg-rose-800 rounded-md transition disabled:opacity-50"
            >
              {deleteLoading ? "Deleting..." : "Confirm Delete"}
            </button>
          </div>
        </div>
      </dialog>
    </div>
  );
};
