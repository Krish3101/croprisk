import React from "react";
import { AdvisoryData } from "../types";

interface AdvisoryProps {
  advisory: AdvisoryData;
}

export const Advisory: React.FC<AdvisoryProps> = ({ advisory }) => {
  const sourceBadges = {
    llm: {
      label: "Written by AI",
      badgeClass: "bg-purple-100 text-purple-800 border-purple-200",
    },
    fallback: {
      label: "Rule-based summary",
      badgeClass: "bg-blue-100 text-blue-800 border-blue-200",
    },
    bypass: {
      label: "No risk this week",
      badgeClass: "bg-emerald-100 text-emerald-800 border-emerald-200",
    },
  };

  const badgeInfo = sourceBadges[advisory.source] || sourceBadges.fallback;

  return (
    <div className="bg-white rounded-lg border border-stone-200 p-6 shadow-sm space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stone-100 pb-3">
        <h2 className="text-lg font-bold text-stone-900 leading-snug">
          {advisory.headline}
        </h2>
        <span
          className={`inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full border ${badgeInfo.badgeClass}`}
        >
          {badgeInfo.label}
        </span>
      </div>

      <div>
        <h3 className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1">
          What the forecast shows
        </h3>
        <p className="text-sm text-stone-700 leading-relaxed">
          {advisory.impact_analysis}
        </p>
      </div>

      <div>
        <h3 className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">
          What to do
        </h3>
        <div className="space-y-2">
          {advisory.actions.map((act, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-3 bg-stone-50 rounded-md border border-stone-200"
            >
              {advisory.source !== "bypass" && (
                <span
                  className={`text-xs font-semibold uppercase px-2 py-0.5 rounded whitespace-nowrap shrink-0 ${
                    act.timeframe === "immediate_24h"
                      ? "bg-rose-100 text-rose-800 border border-rose-200"
                      : "bg-amber-100 text-amber-800 border border-amber-200"
                  }`}
                >
                  {act.timeframe === "immediate_24h" ? "Immediate (24h)" : "Preventative (72h)"}
                </span>
              )}
              <p className="text-xs sm:text-sm text-stone-800 font-medium">
                {act.directive}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-amber-50/60 p-3.5 rounded-md border border-amber-200/60">
        <h3 className="text-xs font-semibold text-amber-900 uppercase tracking-wider mb-0.5">
          What to watch
        </h3>
        <p className="text-xs sm:text-sm text-amber-950 font-medium">
          {advisory.monitoring_focus}
        </p>
      </div>

      <p className="text-[11px] text-stone-500 pt-1 border-t border-stone-100">
        Indicative only. Thresholds are general crop guidelines, not a substitute for local agronomic advice.
      </p>
    </div>
  );
};
