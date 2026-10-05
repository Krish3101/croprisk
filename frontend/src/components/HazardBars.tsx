import React from "react";

interface HazardBarsProps {
  indices: {
    heat: number;
    frost: number;
    precip: number;
    disease: number;
    wind: number;
  };
}

const HAZARD_CONFIG = [
  { key: "heat", label: "Extreme Heat", color: "bg-orange-500" },
  { key: "frost", label: "Frost Damage", color: "bg-sky-500" },
  { key: "precip", label: "Excess Precipitation", color: "bg-blue-600" },
  { key: "disease", label: "Fungal Disease Pressure", color: "bg-teal-600" },
  { key: "wind", label: "Wind Lodging", color: "bg-stone-600" },
] as const;

export const HazardBars: React.FC<HazardBarsProps> = ({ indices }) => {
  return (
    <div className="space-y-3 bg-white p-5 rounded-lg border border-stone-200 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-stone-900 uppercase tracking-wide">
          Hazard Stress Breakdown
        </h2>
      </div>
      <p className="text-xs text-stone-500">
        Each bar shows how close the 5-day forecast gets to this stage's critical physiological threshold.
      </p>
      <div className="space-y-2.5 pt-1">
        {HAZARD_CONFIG.map(({ key, label, color }) => {
          const value = indices[key] ?? 0;
          const rounded = Math.round(value * 10) / 10;
          const isZero = rounded === 0;
          return (
            <div key={key} className="text-xs">
              <div className="flex justify-between items-center mb-1">
                <span className="font-medium text-stone-700">{label}</span>
                <span
                  className={`font-semibold tabular-nums ${
                    isZero ? "text-stone-600" : "text-stone-900"
                  }`}
                >
                  {rounded} / 100
                </span>
              </div>
              <div className="h-2 w-full bg-stone-100 rounded-full overflow-hidden">
                <div
                  className={`h-full ${color} rounded-full transition-all duration-300`}
                  style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
