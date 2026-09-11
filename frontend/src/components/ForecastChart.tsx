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
          <h3 className="text-base font-bold text-stone-900">
            5-Day Forecast & Crop Thresholds
          </h3>
          <p className="text-xs text-stone-500">
            3-hour intervals with stage heat ({tCritHeat} °C) and frost ({tCritFrost} °C) thresholds
          </p>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 11, fill: "#78716c" }}
              angle={-25}
              textAnchor="end"
              interval={3}
            />
            <YAxis
              unit="°C"
              tick={{ fontSize: 11, fill: "#78716c" }}
              domain={["auto", "auto"]}
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
            <Legend verticalAlign="top" height={36} />
            <ReferenceLine
              y={tCritHeat}
              stroke="#ea580c"
              strokeDasharray="4 4"
              strokeWidth={1.5}
              label={{
                value: `Heat Critical (${tCritHeat}°C)`,
                fill: "#ea580c",
                position: "insideTopRight",
                fontSize: 10,
              }}
            />
            <ReferenceLine
              y={tCritFrost}
              stroke="#0284c7"
              strokeDasharray="4 4"
              strokeWidth={1.5}
              label={{
                value: `Frost Critical (${tCritFrost}°C)`,
                fill: "#0284c7",
                position: "insideBottomRight",
                fontSize: 10,
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
