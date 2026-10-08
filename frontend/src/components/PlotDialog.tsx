import React, { useEffect, useRef, useState } from "react";
import { CropSummary, PlotRequest, PlotSummary } from "../types";
import { LocationPicker } from "./LocationPicker";
import { ApiError } from "../api";

interface PlotDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: PlotRequest) => Promise<void>;
  crops: CropSummary[];
  initialData?: PlotSummary | null;
}

export const PlotDialog: React.FC<PlotDialogProps> = ({
  isOpen,
  onClose,
  onSave,
  crops,
  initialData,
}) => {
  const dialogRef = useRef<HTMLDialogElement>(null);
  // Use farm-local ISO date (YYYY-MM-DD) via en-CA format
  const todayStr = new Date().toLocaleDateString("en-CA");
  const minDateStr = new Date(Date.now() - 400 * 24 * 60 * 60 * 1000).toLocaleDateString("en-CA");

  const [name, setName] = useState("");
  const [cropId, setCropId] = useState("");
  const [stageId, setStageId] = useState("");
  const [locationName, setLocationName] = useState("");
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [sowingDate, setSowingDate] = useState(todayStr);

  const [loading, setLoading] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isOpen) {
      setGeneralError(null);
      setFieldErrors({});
      if (initialData) {
        setName(initialData.name);
        setCropId(initialData.crop.id);
        setStageId(initialData.stage.id);
        setLocationName(initialData.location_name);
        setSowingDate(initialData.sowing_date);
        setLatitude(initialData.latitude);
        setLongitude(initialData.longitude);
      } else {
        setName("");
        setCropId("");
        setStageId("");
        setLocationName("");
        setLatitude(null);
        setLongitude(null);
        setSowingDate(todayStr);
      }

      if (dialogRef.current && !dialogRef.current.open) {
        dialogRef.current.showModal();
      }
    } else if (dialogRef.current && dialogRef.current.open) {
      dialogRef.current.close();
    }
  }, [isOpen, initialData, todayStr]);

  const handleCropChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newCropId = e.target.value;
    setCropId(newCropId);
    // Reset stageId to empty so the grower intentionally chooses the correct stage
    setStageId("");
  };

  // Editing keeps an old date as is; the min attribute would otherwise block the native submit.

  const selectedCrop = crops.find((c) => c.id === cropId);

  // Input order in the form, so focus lands on the first problem.
  const fieldInputIds: [string, string][] = [
    ["name", "plot-name"],
    ["crop_id", "plot-crop"],
    ["stage_id", "plot-stage"],
    ["location_name", "plot-location"],
    ["latitude", "plot-location"],
    ["longitude", "plot-location"],
    ["sowing_date", "plot-sowing-date"],
  ];

  const showFieldErrors = (errors: Record<string, string>) => {
    setFieldErrors(errors);
    const first = fieldInputIds.find(([field]) => errors[field]);
    if (first) dialogRef.current?.querySelector<HTMLElement>(`#${first[1]}`)?.focus();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError(null);
    setFieldErrors({});

    const errors: Record<string, string> = {};
    if (!name.trim()) errors.name = "Name is required.";
    if (!cropId) errors.crop_id = "Please select a crop.";
    if (!stageId) errors.stage_id = "Please select a growth stage.";
    if (!locationName || latitude === null || longitude === null) {
      errors.location_name = "Please search and pick a location.";
    }
    if (!sowingDate) {
      errors.sowing_date = "Sowing date is required.";
    } else if (sowingDate > todayStr) {
      errors.sowing_date = "Sowing date cannot be in the future.";
    }

    if (Object.keys(errors).length > 0) {
      showFieldErrors(errors);
      return;
    }

    setLoading(true);
    try {
      const payload: PlotRequest = {
        name: name.trim(),
        crop_id: cropId,
        stage_id: stageId,
        location_name: locationName,
        latitude: latitude as number,
        longitude: longitude as number,
        sowing_date: sowingDate,
      };
      await onSave(payload);
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setGeneralError(err.message);
        if (err.fields) {
          showFieldErrors(err.fields);
        }
      } else {
        setGeneralError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      onClick={(e) => {
        // Light dismiss: close when clicking the backdrop outside the dialog bounds
        if (e.target === dialogRef.current) {
          onClose();
        }
      }}
      aria-labelledby="plot-dialog-title"
      className="p-0 rounded-xl shadow-2xl backdrop:bg-stone-900/40 w-full max-w-lg border border-stone-200"
    >
      <form onSubmit={handleSubmit} className="p-6 space-y-4 bg-white text-stone-900">
        <div className="flex items-center justify-between border-b border-stone-100 pb-3">
          <h2 id="plot-dialog-title" className="text-lg font-bold">
            {initialData ? "Edit plot" : "Add a plot"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-stone-400 hover:text-stone-600 text-lg font-semibold px-2 py-1 rounded"
          >
            ✕
          </button>
        </div>

        {generalError && (
          <div role="alert" className="p-3 text-xs bg-rose-50 text-rose-800 border border-rose-200 rounded-md">
            {generalError}
          </div>
        )}

        <div>
          <label htmlFor="plot-name" className="block text-sm font-semibold text-stone-700 mb-1">
            Name <span className="text-rose-600">*</span>
          </label>
          <input
            id="plot-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            aria-invalid={Boolean(fieldErrors.name)}
            aria-describedby={fieldErrors.name ? "plot-name-err" : undefined}
            placeholder="e.g. North Acre or Tubewell Plot"
            className={`w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 ${
              fieldErrors.name
                ? "border-rose-300 focus:ring-rose-400"
                : "border-stone-300 focus:ring-emerald-500"
            }`}
          />
          {fieldErrors.name && (
            <p id="plot-name-err" role="alert" className="text-xs text-rose-600 mt-1">
              {fieldErrors.name}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="plot-crop" className="block text-sm font-semibold text-stone-700 mb-1">
            Crop <span className="text-rose-600">*</span>
          </label>
          <select
            id="plot-crop"
            value={cropId}
            onChange={handleCropChange}
            data-testid="crop-select"
            aria-invalid={Boolean(fieldErrors.crop_id)}
            aria-describedby={fieldErrors.crop_id ? "plot-crop-err" : undefined}
            className={`w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 bg-white ${
              fieldErrors.crop_id
                ? "border-rose-300 focus:ring-rose-400"
                : "border-stone-300 focus:ring-emerald-500"
            }`}
          >
            <option value="">Select a crop...</option>
            {crops.map((c) => (
              <option key={c.id} value={c.id}>
                {c.common_name} ({c.scientific_name})
              </option>
            ))}
          </select>
          {fieldErrors.crop_id && (
            <p id="plot-crop-err" role="alert" className="text-xs text-rose-600 mt-1">
              {fieldErrors.crop_id}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="plot-stage" className="block text-sm font-semibold text-stone-700 mb-1">
            Growth stage <span className="text-rose-600">*</span>
          </label>
          <select
            id="plot-stage"
            value={stageId}
            onChange={(e) => setStageId(e.target.value)}
            disabled={!cropId}
            data-testid="stage-select"
            aria-invalid={Boolean(fieldErrors.stage_id)}
            aria-describedby={fieldErrors.stage_id ? "plot-stage-err" : undefined}
            className={`w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 bg-white disabled:bg-stone-100 disabled:text-stone-400 ${
              fieldErrors.stage_id
                ? "border-rose-300 focus:ring-rose-400"
                : "border-stone-300 focus:ring-emerald-500"
            }`}
          >
            <option value="">
              {!cropId ? "Select a crop first..." : "Select growth stage..."}
            </option>
            {selectedCrop?.stages.map((s) => (
              <option key={s.id} value={s.id}>
                Stage {s.order}: {s.name} (BBCH {s.bbch})
              </option>
            ))}
          </select>
          {fieldErrors.stage_id && (
            <p id="plot-stage-err" role="alert" className="text-xs text-rose-600 mt-1">
              {fieldErrors.stage_id}
            </p>
          )}
        </div>

        <LocationPicker
          value={{
            location_name: locationName,
            latitude,
            longitude,
          }}
          onChange={({ location_name, latitude: lat, longitude: lon }) => {
            setLocationName(location_name);
            setLatitude(lat);
            setLongitude(lon);
          }}
          error={fieldErrors.location_name}
        />

        <div>
          <label htmlFor="plot-sowing-date" className="block text-sm font-semibold text-stone-700 mb-1">
            Sowing date <span className="text-rose-600">*</span>
          </label>
          <input
            id="plot-sowing-date"
            type="date"
            value={sowingDate}
            min={minDateStr}
            max={todayStr}
            onChange={(e) => setSowingDate(e.target.value)}
            aria-invalid={Boolean(fieldErrors.sowing_date)}
            aria-describedby={fieldErrors.sowing_date ? "plot-sowing-err" : undefined}
            className={`w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 ${
              fieldErrors.sowing_date
                ? "border-rose-300 focus:ring-rose-400"
                : "border-stone-300 focus:ring-emerald-500"
            }`}
          />
          {fieldErrors.sowing_date && (
            <p id="plot-sowing-err" role="alert" className="text-xs text-rose-600 mt-1">
              {fieldErrors.sowing_date}
            </p>
          )}
        </div>

        <div className="flex justify-end gap-3 pt-3 border-t border-stone-100">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200 rounded-md transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 text-sm font-semibold text-white bg-emerald-700 hover:bg-emerald-800 rounded-md transition disabled:opacity-50"
          >
            {loading ? "Saving..." : "Save"}
          </button>
        </div>
      </form>
    </dialog>
  );
};
