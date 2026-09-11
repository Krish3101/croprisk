import React from "react";
import { Link } from "react-router-dom";
import { PlotSummary } from "../types";
import { ScoreBadge } from "./ScoreBadge";

interface PlotCardProps {
  plot: PlotSummary;
}

export const PlotCard: React.FC<PlotCardProps> = ({ plot }) => {
  return (
    <Link
      to={`/plots/${plot.id}`}
      className="block bg-white rounded-lg border border-stone-200 p-5 shadow-sm hover:border-emerald-500 hover:shadow-md transition group"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h3 className="text-base font-bold text-stone-900 group-hover:text-emerald-700 transition">
            {plot.name}
          </h3>
          <p className="text-xs text-stone-500 mt-0.5">
            {plot.crop.common_name} · Stage: {plot.stage.name} (BBCH {plot.stage.bbch})
          </p>
        </div>
        <div>
          {plot.latest_risk ? (
            <ScoreBadge
              score={plot.latest_risk.score}
              severity={plot.latest_risk.severity}
              size="sm"
            />
          ) : (
            <span className="text-xs font-medium px-2.5 py-1 rounded bg-stone-100 text-stone-600 border border-stone-200">
              Unassessed
            </span>
          )}
        </div>
      </div>

      <div className="text-xs text-stone-600 space-y-1 border-t border-stone-100 pt-3">
        <div className="flex justify-between">
          <span className="text-stone-500">Location:</span>
          <span className="font-medium text-stone-800 truncate max-w-[220px]">
            {plot.location_name}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-stone-500">Days after sowing:</span>
          <span className="font-medium text-stone-800">
            {plot.days_after_sowing} days (sown {plot.sowing_date})
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-stone-500">Primary Threat:</span>
          <span className="font-semibold text-stone-900">
            {plot.latest_risk ? plot.latest_risk.primary_threat : "None calculated"}
          </span>
        </div>
      </div>
    </Link>
  );
};
