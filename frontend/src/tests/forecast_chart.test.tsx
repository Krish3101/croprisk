import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ForecastChart } from "../components/ForecastChart";

// jsdom has no layout, so give the chart a fixed size instead of measuring its parent.
vi.mock("recharts", async (importOriginal) => {
  const original = await importOriginal<typeof import("recharts")>();
  return {
    ...original,
    ResponsiveContainer: ({ children }: { children: React.ReactElement }) =>
      React.cloneElement(children, { width: 800, height: 300 }),
  };
});

describe("ForecastChart", () => {
  it("draws both threshold lines even when the forecast never reaches frost", () => {
    const intervals = Array.from({ length: 16 }, (_, i) => ({
      timestamp: new Date(Date.UTC(2026, 8, 10, i * 3)).toISOString(),
      temperature_c: 24 + (i % 4),
      relative_humidity: 60,
      wind_kmh: 10,
      rain_mm: 0,
    }));

    const { container } = render(
      <ForecastChart intervals={intervals} tCritHeat={30} tCritFrost={-2} />
    );

    expect(screen.getByText("Heat Critical (30°C)")).toBeInTheDocument();
    expect(screen.getByText("Frost Critical (-2°C)")).toBeInTheDocument();
    expect(container.querySelectorAll(".recharts-reference-line")).toHaveLength(2);
  });
});
