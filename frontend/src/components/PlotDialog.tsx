import React, { useEffect, useRef, useState } from "react";
import { CropSummary, PlotCreateInput, PlotSummary } from "../types";
import { LocationPicker } from "./LocationPicker";
import { ApiError } from "../api";

interface PlotDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: PlotCreateInput) => Promise<void>;
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
  const todayStr = new Date().toISOString().split("T")[0];

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
        setLatitude(initialData.latitude ?? 18.5204);
        setLongitude(initialData.longitude ?? 73.8567);
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
    const crop = crops.find((c) => c.id === newCropId);
    if (!crop || !crop.stages.some((s) => s.id === stageId)) {
      setStageId(crop?.stages[0]?.id || "");
    }
  };

  const selectedCrop = crops.find((c) => c.id === cropId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError(null);
    setFieldErrors({});

    const errors: Record<string, string> = {};
    if (!name.trim()) errors.name = "Field name is required.";
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
      setFieldErrors(errors);
      return;
    }

    setLoading(true);
    try {
      await onSave({
        name: name.trim(),
        crop_id: cropId,
        stage_id: stageId,
        location_name: locationName,
        latitude: latitude as number,
        longitude: longitude as number,
        sowing_date: sowingDate,
      });
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setGeneralError(err.message);
        if (err.fields) {
          setFieldErrors(err.fields);
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
      className="p-0 rounded-xl shadow-2xl backdrop:bg-stone-900/40 w-full max-w-lg border border-stone-200"
    >
      <form onSubmit={handleSubmit} className="p-6 space-y-4 bg-white text-stone-900">
        <div className="flex items-center justify-between border-b border-stone-100 pb-3">
          <h2 className="text-lg font-bold">
            {initialData ? "Edit Field Details" : "Register New Field"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-stone-400 hover:text-stone-600 text-lg font-semibold"
          >
            ✕
          </button>
        </div>

        {generalError && (
          <div className="p-3 text-xs bg-rose-50 text-rose-800 border border-rose-200 rounded-md">
            {generalError}
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wide mb-1">
            Field Name *
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. North Acre"
            className={`w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 ${
              fieldErrors.name
                ? "border-rose-300 focus:ring-rose-400"
                : "border-stone-300 focus:ring-emerald-500"
            }`}
          />
          {fieldErrors.name && (
            <p className="text-xs text-rose-600 mt-1">{fieldErrors.name}</p>
          )}
        </div>

        <div>
          <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wide mb-1">
            Crop *
          </label>
          <select
            value={cropId}
            onChange={handleCropChange}
            data-testid="crop-select"
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
            <p className="text-xs text-rose-600 mt-1">{fieldErrors.crop_id}</p>
          )}
        </div>

        <div>
          <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wide mb-1">
            Current Growth Stage *
          </label>
          <select
            value={stageId}
            onChange={(e) => setStageId(e.target.value)}
            disabled={!cropId}
            data-testid="stage-select"
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
            <p className="text-xs text-rose-600 mt-1">{fieldErrors.stage_id}</p>
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
          <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wide mb-1">
            Sowing Date *
          </label>
          <input
            type="date"
            value={sowingDate}
            max={todayStr}
            onChange={(e) => setSowingDate(e.target.value)}
            className={`w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 ${
              fieldErrors.sowing_date
                ? "border-rose-300 focus:ring-rose-400"
                : "border-stone-300 focus:ring-emerald-500"
            }`}
          />
          {fieldErrors.sowing_date && (
            <p className="text-xs text-rose-600 mt-1">{fieldErrors.sowing_date}</p>
          )}
        </div>

        <div className="flex justify-end gap-3 pt-3 border-t border-stone-100">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-xs font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200 rounded-md transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 text-xs font-semibold text-white bg-emerald-700 hover:bg-emerald-800 rounded-md transition disabled:opacity-50"
          >
            {loading ? "Saving..." : initialData ? "Save Changes" : "Register Plot"}
          </button>
        </div>
      </form>
    </dialog>
  );
};
