import React, { useState, useEffect } from "react";
import { api } from "../api";
import { GeocodeCandidate } from "../types";

interface LocationPickerProps {
  value: {
    location_name: string;
    latitude: number | null;
    longitude: number | null;
  };
  onChange: (selected: { location_name: string; latitude: number; longitude: number }) => void;
  error?: string;
}

export const LocationPicker: React.FC<LocationPickerProps> = ({ value, onChange, error }) => {
  const [query, setQuery] = useState(value.location_name || "");
  const [candidates, setCandidates] = useState<GeocodeCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(value.latitude != null && value.longitude != null);
  const [searchError, setSearchError] = useState<string | null>(null);
  // The text the last finished search was for, so "no matches" only shows for real results
  const [searchedFor, setSearchedFor] = useState("");

  useEffect(() => {
    setQuery(value.location_name || "");
    setSelected(value.latitude != null && value.longitude != null);
  }, [value.location_name, value.latitude, value.longitude]);

  useEffect(() => {
    if (selected || query.trim().length < 2) {
      setCandidates([]);
      return;
    }

    let cancelled = false;
    const timer = setTimeout(async () => {
      setLoading(true);
      setSearchError(null);
      try {
        const results = await api.searchGeocode(query);
        if (!cancelled) {
          setCandidates(results);
          setSearchedFor(query);
        }
      } catch {
        if (!cancelled) {
          setCandidates([]);
          setSearchError("Location search is unavailable right now. Try again in a minute.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 350);

    // A reply that lands after the user typed again or picked a result is ignored
    return () => {
      cancelled = true;
      setLoading(false);
      clearTimeout(timer);
    };
  }, [query, selected]);

  const choose = (candidate: GeocodeCandidate) => {
    onChange({
      location_name: candidate.display_name,
      latitude: candidate.latitude,
      longitude: candidate.longitude,
    });
    setQuery(candidate.display_name);
    setSelected(true);
    setCandidates([]);
  };

  return (
    <div>
      <label htmlFor="plot-location" className="block text-sm font-semibold text-stone-700 mb-1">
        Location <span className="text-rose-600">*</span>
      </label>
      <p className="text-xs text-stone-500 mb-1.5">
        Search for a town or village, then choose a result from the list.
      </p>
      <div className="relative">
        <input
          id="plot-location"
          type="text"
          autoComplete="off"
          aria-invalid={Boolean(error)}
          aria-autocomplete="list"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setSelected(false);
            setSearchError(null);
          }}
          placeholder="e.g. Ludhiana, Punjab or Pune, Maharashtra"
          className={`w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 ${
            error ? "border-rose-300 focus:ring-rose-400" : "border-stone-300 focus:ring-emerald-500"
          }`}
        />
        {loading && (
          <span className="absolute right-3 top-2.5 text-xs text-stone-400">Searching...</span>
        )}
      </div>

      {selected && value.latitude != null && (
        <p className="text-xs text-emerald-700 mt-1 font-medium">
          ✓ Coordinates confirmed: ({value.latitude.toFixed(4)}, {value.longitude?.toFixed(4)})
        </p>
      )}

      {error && <p role="alert" className="text-xs text-rose-600 mt-1">{error}</p>}
      {searchError && <p role="alert" className="text-xs text-rose-600 mt-1">{searchError}</p>}

      {candidates.length > 0 && (
        <ul
          role="listbox"
          aria-label="Location search suggestions"
          className="mt-1 bg-white border border-stone-200 rounded-md shadow-lg max-h-56 overflow-auto divide-y divide-stone-100"
        >
          {candidates.map((c) => (
            <li key={`${c.latitude},${c.longitude}`} role="option" aria-selected={false}>
              <button
                type="button"
                onClick={() => choose(c)}
                className="w-full px-3 py-2 text-xs text-left flex flex-col hover:bg-emerald-50 focus:bg-emerald-50 text-stone-900"
              >
                <span className="font-medium">{c.display_name}</span>
                <span className="text-stone-500 text-[11px]">
                  Lat: {c.latitude.toFixed(4)}, Lon: {c.longitude.toFixed(4)}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {!selected && searchedFor === query && candidates.length === 0 && (
        <p className="text-xs text-stone-500 mt-1">No matching locations found.</p>
      )}
    </div>
  );
};
