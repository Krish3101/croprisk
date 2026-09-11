import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { PlotDialog } from "../components/PlotDialog";
import { ApiError } from "../api";
import { CropSummary } from "../types";

const mockCrops: CropSummary[] = [
  {
    id: "wheat",
    common_name: "Wheat",
    scientific_name: "Triticum aestivum",
    stages: [{ id: "wheat.anthesis", name: "Flowering", bbch: "61-69", order: 3 }],
  },
];

describe("Error Envelope Handling in UI", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders API validation error fields without crashing", async () => {
    const mockSave = vi.fn().mockRejectedValue(
      new ApiError("validation_error", "Stage does not belong to the selected crop.", 422, {
        stage_id: "Stage does not belong to the selected crop.",
      })
    );

    render(
      <PlotDialog
        isOpen={true}
        onClose={vi.fn()}
        onSave={mockSave}
        crops={mockCrops}
        initialData={{
          id: 1,
          name: "North Plot",
          crop: { id: "wheat", common_name: "Wheat" },
          stage: { id: "wheat.anthesis", name: "Flowering", bbch: "61-69" },
          location_name: "Pune, India",
          sowing_date: "2026-01-01",
          days_after_sowing: 50,
          latest_risk: null,
        }}
      />
    );

    const submitBtn = screen.getByText("Save Changes");
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockSave).toHaveBeenCalled();
      const errNodes = screen.getAllByText("Stage does not belong to the selected crop.");
      expect(errNodes.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("renders API general error message banner when fields are absent", async () => {
    const mockSave = vi.fn().mockRejectedValue(
      new ApiError("upstream_unavailable", "Weather provider is down.", 503)
    );

    render(
      <PlotDialog
        isOpen={true}
        onClose={vi.fn()}
        onSave={mockSave}
        crops={mockCrops}
        initialData={{
          id: 1,
          name: "North Plot",
          crop: { id: "wheat", common_name: "Wheat" },
          stage: { id: "wheat.anthesis", name: "Flowering", bbch: "61-69" },
          location_name: "Pune, India",
          sowing_date: "2026-01-01",
          days_after_sowing: 50,
          latest_risk: null,
        }}
      />
    );

    const submitBtn = screen.getByText("Save Changes");
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Weather provider is down.")).toBeInTheDocument();
    });
  });
});
