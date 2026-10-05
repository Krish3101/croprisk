import { render, screen, fireEvent, cleanup, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { PlotDialog } from "../components/PlotDialog";
import { CropSummary, PlotSummary } from "../types";

const mockCrops: CropSummary[] = [
  {
    id: "wheat",
    common_name: "Wheat",
    scientific_name: "Triticum aestivum",
    stages: [
      { id: "wheat.emergence", name: "Emergence", bbch: "00-19", order: 1, t_crit_heat: 30, t_crit_frost: 2 },
      { id: "wheat.anthesis", name: "Flowering", bbch: "61-69", order: 3, t_crit_heat: 30, t_crit_frost: 2 },
    ],
  },
  {
    id: "rice",
    common_name: "Rice",
    scientific_name: "Oryza sativa",
    stages: [
      { id: "rice.seedling", name: "Seedling", bbch: "00-19", order: 1, t_crit_heat: 30, t_crit_frost: 2 },
      { id: "rice.tillering", name: "Tillering", bbch: "20-39", order: 2, t_crit_heat: 30, t_crit_frost: 2 },
    ],
  },
];

const oldPlot: PlotSummary = {
  id: 1,
  name: "North Acre",
  crop: { id: "wheat", common_name: "Wheat" },
  stage: { id: "wheat.anthesis", name: "Flowering", bbch: "61-69" },
  location_name: "Ludhiana, Punjab",
  latitude: 30.9,
  longitude: 75.85,
  sowing_date: "2020-01-01",
  days_after_sowing: 2000,
  latest_risk: null,
};

describe("PlotDialog Component", () => {
  afterEach(() => cleanup());

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

  it("focuses the first invalid field after a failed submit", () => {
    render(<PlotDialog isOpen={true} onClose={vi.fn()} onSave={vi.fn()} crops={mockCrops} />);

    fireEvent.change(screen.getByLabelText(/Field name/), { target: { value: "North" } });
    fireEvent.click(screen.getByRole("button", { name: "Add Field" }));

    expect(screen.getByTestId("crop-select")).toHaveFocus();
    expect(screen.getByTestId("crop-select")).toHaveAttribute("aria-invalid", "true");
  });

  it("leaves sowing_date out of an edit when it was not changed", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <PlotDialog isOpen={true} onClose={vi.fn()} onSave={onSave} crops={mockCrops} initialData={oldPlot} />
    );

    fireEvent.change(screen.getByLabelText(/Field name/), { target: { value: "South Acre" } });
    fireEvent.click(screen.getByRole("button", { name: "Save Changes" }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    const sent = onSave.mock.calls[0][0];
    expect(sent.name).toBe("South Acre");
    expect(sent).not.toHaveProperty("sowing_date");
  });

  it("sends sowing_date on an edit when it was changed", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    const recent = new Date().toLocaleDateString("en-CA");
    render(
      <PlotDialog isOpen={true} onClose={vi.fn()} onSave={onSave} crops={mockCrops} initialData={oldPlot} />
    );

    fireEvent.change(screen.getByLabelText(/Sowing date/), { target: { value: recent } });
    fireEvent.click(screen.getByRole("button", { name: "Save Changes" }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0].sowing_date).toBe(recent);
  });
});
