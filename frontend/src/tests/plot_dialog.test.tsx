import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { PlotDialog } from "../components/PlotDialog";
import { CropSummary } from "../types";

const mockCrops: CropSummary[] = [
  {
    id: "wheat",
    common_name: "Wheat",
    scientific_name: "Triticum aestivum",
    stages: [
      { id: "wheat.emergence", name: "Emergence", bbch: "00-19", order: 1 },
      { id: "wheat.anthesis", name: "Flowering", bbch: "61-69", order: 3 },
    ],
  },
  {
    id: "rice",
    common_name: "Rice",
    scientific_name: "Oryza sativa",
    stages: [
      { id: "rice.seedling", name: "Seedling", bbch: "00-19", order: 1 },
      { id: "rice.tillering", name: "Tillering", bbch: "20-39", order: 2 },
    ],
  },
];

describe("PlotDialog Component", () => {
  it("disables stage select until crop is chosen, then populates corresponding stages", () => {
    render(
      <PlotDialog
        isOpen={true}
        onClose={vi.fn()}
        onSave={vi.fn()}
        crops={mockCrops}
      />
    );

    const cropSelect = screen.getByTestId("crop-select");
    const stageSelect = screen.getByTestId("stage-select");

    expect(stageSelect).toBeDisabled();

    fireEvent.change(cropSelect, { target: { value: "wheat" } });
    expect(stageSelect).not.toBeDisabled();
    expect(screen.getByText(/Emergence/)).toBeInTheDocument();
    expect(screen.getByText(/Flowering/)).toBeInTheDocument();

    fireEvent.change(cropSelect, { target: { value: "rice" } });
    expect(screen.getByText(/Seedling/)).toBeInTheDocument();
    expect(screen.getByText(/Tillering/)).toBeInTheDocument();
    expect(screen.queryByText(/Emergence/)).not.toBeInTheDocument();
  });
});
