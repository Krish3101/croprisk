import React from "react";
import { WeatherDigest } from "../types";

interface DigestStripProps {
  digest: WeatherDigest;
}

export const DigestStrip: React.FC<DigestStripProps> = ({ digest }) => {
  const items = [
    { label: "Peak Temp", value: `${digest.peak_temp_c}°C` },
    { label: "Min Temp", value: `${digest.min_temp_c}°C` },
    { label: "Total Rain", value: `${digest.total_rain_mm} mm` },
    { label: "Max Wind", value: `${digest.max_wind_kmh} km/h` },
    { label: "Disease Window", value: `${digest.longest_disease_window_h}h` },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
      {items.map((item, i) => (
        <div
          key={item.label}
          className={`bg-white p-3.5 rounded-lg border border-stone-200 shadow-sm text-center ${
            i === items.length - 1 ? "col-span-2 sm:col-span-1" : ""
          }`}
        >
          <span className="text-[11px] font-semibold text-stone-600 uppercase tracking-wide block">
            {item.label}
          </span>
          <p className="text-lg font-bold text-stone-900 mt-0.5 tabular-nums">{item.value}</p>
        </div>
      ))}
    </div>
  );
};
