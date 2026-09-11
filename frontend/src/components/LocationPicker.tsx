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
  const wrapperRef = useRef<HTMLDivElement>(null);

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
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const results = await api.searchGeocode(query);
        setCandidates(results);
        setOpen(true);
      } catch {
        setCandidates([]);
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
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setSelected(false);
  };

  return (
    <div className="relative" ref={wrapperRef}>
      <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wide mb-1">
        Location (Search & Pick) *
      </label>
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => {
            if (candidates.length > 0) setOpen(true);
          }}
          placeholder="e.g. Pune, Maharashtra, India"
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

      {error && <p className="text-xs text-rose-600 mt-1">{error}</p>}

      {open && candidates.length > 0 && (
        <ul className="absolute z-20 w-full mt-1 bg-white border border-stone-200 rounded-md shadow-lg max-h-56 overflow-auto divide-y divide-stone-100">
          {candidates.map((c, index) => (
            <li
              key={index}
              onClick={() => handleSelect(c)}
              className="px-3 py-2 text-xs hover:bg-stone-50 cursor-pointer flex flex-col"
            >
              <span className="font-medium text-stone-900">{c.display_name}</span>
              <span className="text-stone-500 text-[11px]">
                Lat: {c.latitude.toFixed(4)}, Lon: {c.longitude.toFixed(4)}
              </span>
            </li>
          ))}
        </ul>
      )}

      {open && !loading && candidates.length === 0 && query.length >= 2 && (
        <div className="absolute z-20 w-full mt-1 bg-white border border-stone-200 rounded-md shadow-lg p-3 text-xs text-stone-500">
          No matching locations found.
        </div>
      )}
    </div>
  );
};
