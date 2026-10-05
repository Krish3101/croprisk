import React from "react";
import { Link } from "react-router-dom";
import { PlotSummary } from "../types";
import { ScoreBadge } from "./ScoreBadge";

interface PlotCardProps {
  plot: PlotSummary;
}

export const PlotCard: React.FC<PlotCardProps> = ({ plot }) => {
  const displayThreat = () => {
    if (!plot.latest_risk) return "Open to run first assessment";
    if (plot.latest_risk.primary_threat === "None") return "No significant hazard";
    return plot.latest_risk.primary_threat;
  };

  return (
    <Link
      to={`/plots/${plot.id}`}
      className="block bg-white rounded-lg border border-stone-200 p-5 shadow-sm hover:border-emerald-500 hover:shadow-md transition group"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <h2 className="text-base font-bold text-stone-900 group-hover:text-emerald-700 transition truncate">
            {plot.name}
          </h2>
          <p className="text-xs text-stone-600 mt-0.5 truncate">
            {plot.crop.common_name} · {plot.stage.name}
          </p>
        </div>
        <div className="shrink-0">
          {plot.latest_risk ? (
            <ScoreBadge
              score={plot.latest_risk.score}
              severity={plot.latest_risk.severity}
              size="sm"
            />
          ) : (
            <span className="text-xs font-medium px-2.5 py-1 rounded bg-stone-100 text-stone-600 border border-stone-200">
              Not assessed yet
            </span>
          )}
        </div>
      </div>

      <div className="text-xs text-stone-600 space-y-1.5 border-t border-stone-100 pt-3">
        <div className="flex justify-between gap-2">
          <span className="text-stone-500 shrink-0">Location:</span>
          <span className="font-medium text-stone-800 min-w-0 truncate">
            {plot.location_name}
          </span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-stone-500 shrink-0">Days after sowing:</span>
          <span className="font-medium text-stone-800">
            {plot.days_after_sowing} days (sown {plot.sowing_date})
          </span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-stone-500 shrink-0">Primary Threat:</span>
          <span className="font-semibold text-stone-900 truncate">
            {displayThreat()}
          </span>
        </div>
      </div>
    </Link>
  );
};
