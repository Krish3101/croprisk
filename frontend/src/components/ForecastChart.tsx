import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
  Legend,
} from "recharts";
import { ForecastInterval } from "../types";

interface ForecastChartProps {
  intervals: ForecastInterval[];
  tCritHeat: number;
  tCritFrost: number;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  intervals,
  tCritHeat,
  tCritFrost,
}) => {
  const chartData = intervals.map((item) => {
    const d = new Date(item.timestamp);
    const timeLabel = isNaN(d.getTime())
      ? item.timestamp
      : d.toLocaleDateString("en-US", {
          weekday: "short",
          hour: "numeric",
          hour12: true,
        });

    return {
      time: timeLabel,
      temp: item.temperature_c,
      rain: item.rain_mm,
      wind: Math.round(item.wind_kmh),
      humidity: Math.round(item.relative_humidity),
    };
  });

  return (
    <div className="bg-white rounded-lg border border-stone-200 p-5 shadow-sm space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stone-100 pb-3">
        <div>
          <h2 className="text-base font-bold text-stone-900">
            5-Day Forecast &amp; Crop Thresholds
          </h2>
          <p className="text-sm text-stone-600">
            3-hour intervals with stage heat ({tCritHeat} °C) and frost ({tCritFrost} °C) thresholds (times in your local timezone)
          </p>
        </div>
      </div>

      <div
        className="h-72 w-full"
        role="img"
        aria-label={`Forecast temperature line chart. Critical heat threshold ${tCritHeat}°C, critical frost threshold ${tCritFrost}°C.`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 11, fill: "#78716c" }}
              angle={-25}
              textAnchor="end"
              minTickGap={24}
            />
            {/* Widen the axis to include both thresholds so their lines are never clipped */}
            <YAxis
              tick={{ fontSize: 11, fill: "#78716c" }}
              tickFormatter={(v) => `${v}°`}
              domain={[
                (dMin: number) => Math.floor(Math.min(dMin, tCritFrost) - 2),
                (dMax: number) => Math.ceil(Math.max(dMax, tCritHeat) + 2),
              ]}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload.length) return null;
                const data = payload[0].payload;
                return (
                  <div className="bg-stone-900 text-white text-xs p-3 rounded shadow-lg space-y-1">
                    <p className="font-semibold border-b border-stone-700 pb-1">{data.time}</p>
                    <p className="text-orange-300">Temperature: {data.temp} °C</p>
                    <p className="text-blue-300">Precipitation: {data.rain} mm/3h</p>
                    <p className="text-stone-300">Wind Gust: {data.wind} km/h</p>
                    <p className="text-stone-300">Relative Humidity: {data.humidity}%</p>
                  </div>
                );
              }}
            />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: 12 }} />
            <ReferenceLine
              y={tCritHeat}
              stroke="#c2410c"
              strokeDasharray="6 3"
              strokeWidth={1.5}
              label={{
                value: `Heat Critical (${tCritHeat}°C)`,
                fill: "#c2410c",
                position: "insideTopRight",
                fontSize: 12,
              }}
            />
            <ReferenceLine
              y={tCritFrost}
              stroke="#0369a1"
              strokeDasharray="2 4"
              strokeWidth={1.5}
              label={{
                value: `Frost Critical (${tCritFrost}°C)`,
                fill: "#0369a1",
                position: "insideBottomRight",
                fontSize: 12,
              }}
            />
            <Line
              type="monotone"
              dataKey="temp"
              name="Temperature (°C)"
              stroke="#0f766e"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
