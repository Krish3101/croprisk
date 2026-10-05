import React, { useState, useEffect, useRef } from "react";
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

export const LocationPicker: React.FC<LocationPickerProps> = ({
  value,
  onChange,
  error,
}) => {
  const [query, setQuery] = useState(value.location_name || "");
  const [candidates, setCandidates] = useState<GeocodeCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(Boolean(value.latitude && value.longitude));
  const [searchError, setSearchError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState<number>(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setQuery(value.location_name || "");
    setSelected(Boolean(value.latitude && value.longitude));
  }, [value.location_name, value.latitude, value.longitude]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (selected) return;
    if (!query.trim() || query.length < 2) {
      setCandidates([]);
      setOpen(false);
      setActiveIndex(-1);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      setSearchError(null);
      try {
        const results = await api.searchGeocode(query);
        setCandidates(results);
        setOpen(true);
        setActiveIndex(-1);
      } catch {
        setCandidates([]);
        setSearchError("Location search is unavailable right now. Try again in a minute.");
      } finally {
        setLoading(false);
      }
    }, 350);

    return () => clearTimeout(timer);
  }, [query, selected]);

  const handleSelect = (candidate: GeocodeCandidate) => {
    onChange({
      location_name: candidate.display_name,
      latitude: candidate.latitude,
      longitude: candidate.longitude,
    });
    setQuery(candidate.display_name);
    setSelected(true);
    setOpen(false);
    setSearchError(null);
    setActiveIndex(-1);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setSelected(false);
    setSearchError(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open || candidates.length === 0) {
      if (e.key === "ArrowDown" && candidates.length > 0) {
        setOpen(true);
      }
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((prev) => (prev < candidates.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((prev) => (prev > 0 ? prev - 1 : candidates.length - 1));
    } else if (e.key === "Enter") {
      if (activeIndex >= 0 && activeIndex < candidates.length) {
        e.preventDefault();
        handleSelect(candidates[activeIndex]);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
      setActiveIndex(-1);
    }
  };

  return (
    <div className="relative" ref={wrapperRef}>
      <label
        htmlFor="plot-location"
        className="block text-sm font-semibold text-stone-700 mb-1"
      >
        Location <span className="text-rose-600">*</span>
      </label>
      <p className="text-xs text-stone-500 mb-1.5">
        Search for a town or village, then choose a result from the list.
      </p>
      <div className="relative">
        <input
          ref={inputRef}
          id="plot-location"
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-controls="loc-list"
          aria-autocomplete="list"
          aria-invalid={Boolean(error)}
          aria-activedescendant={
            activeIndex >= 0 ? `loc-opt-${activeIndex}` : undefined
          }
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (candidates.length > 0) setOpen(true);
          }}
          placeholder="e.g. Ludhiana, Punjab or Pune, Maharashtra"
          className={`w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 ${
            error
              ? "border-rose-300 focus:ring-rose-400"
              : "border-stone-300 focus:ring-emerald-500"
          }`}
        />
        {loading && (
          <span className="absolute right-3 top-2.5 text-xs text-stone-400">
            Searching...
          </span>
        )}
      </div>

      {selected && value.latitude !== null && (
        <p className="text-xs text-emerald-700 mt-1 font-medium">
          ✓ Coordinates confirmed: ({value.latitude.toFixed(4)}, {value.longitude?.toFixed(4)})
        </p>
      )}

      {error && <p role="alert" className="text-xs text-rose-600 mt-1">{error}</p>}
      {searchError && (
        <p role="alert" className="text-xs text-rose-600 mt-1">
          {searchError}
        </p>
      )}

      {open && candidates.length > 0 && (
        <ul
          id="loc-list"
          role="listbox"
          className="absolute z-20 w-full mt-1 bg-white border border-stone-200 rounded-md shadow-lg max-h-56 overflow-auto divide-y divide-stone-100"
        >
          {candidates.map((c, index) => {
            const isHighlighted = activeIndex === index;
            return (
              <li
                key={index}
                id={`loc-opt-${index}`}
                role="option"
                aria-selected={isHighlighted}
                onClick={() => handleSelect(c)}
                onMouseEnter={() => setActiveIndex(index)}
                className={`px-3 py-2 text-xs cursor-pointer flex flex-col transition ${
                  isHighlighted ? "bg-emerald-50 text-emerald-950" : "hover:bg-stone-50 text-stone-900"
                }`}
              >
                <span className="font-medium">{c.display_name}</span>
                <span className="text-stone-500 text-[11px]">
                  Lat: {c.latitude.toFixed(4)}, Lon: {c.longitude.toFixed(4)}
                </span>
              </li>
            );
          })}
        </ul>
      )}

      {open && !loading && candidates.length === 0 && query.length >= 2 && !searchError && (
        <div className="absolute z-20 w-full mt-1 bg-white border border-stone-200 rounded-md shadow-lg p-3 text-xs text-stone-500">
          No matching locations found.
        </div>
      )}
    </div>
  );
};
