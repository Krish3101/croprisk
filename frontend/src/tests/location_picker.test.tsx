import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { LocationPicker } from "../components/LocationPicker";
import { api, ApiError } from "../api";

const candidates = [
  { display_name: "Ludhiana, Punjab, IN", city: "Ludhiana", state: "Punjab", country: "IN", latitude: 30.9, longitude: 75.85 },
  { display_name: "Ludhiana, Haryana, IN", city: "Ludhiana", state: "Haryana", country: "IN", latitude: 29.1, longitude: 76.2 },
];

const empty = { location_name: "", latitude: null, longitude: null };

describe("LocationPicker", () => {
  afterEach(() => vi.restoreAllMocks());

  it("selects a result with ArrowDown and Enter", async () => {
    vi.spyOn(api, "searchGeocode").mockResolvedValue(candidates);
    const onChange = vi.fn();
    render(<LocationPicker value={empty} onChange={onChange} />);

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "Ludh" } });
    await screen.findByRole("listbox");

    fireEvent.keyDown(input, { key: "ArrowDown" });
    expect(input).toHaveAttribute("aria-activedescendant", "loc-opt-0");
    fireEvent.keyDown(input, { key: "Enter" });

    expect(onChange).toHaveBeenCalledWith({
      location_name: "Ludhiana, Punjab, IN",
      latitude: 30.9,
      longitude: 75.85,
    });
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("shows an alert when geocoding returns 503", async () => {
    vi.spyOn(api, "searchGeocode").mockRejectedValue(
      new ApiError("upstream_unavailable", "Weather service unavailable.", 503)
    );
    render(<LocationPicker value={empty} onChange={vi.fn()} />);

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Pune" } });

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Location search is unavailable right now. Try again in a minute."
      )
    );
  });
});
