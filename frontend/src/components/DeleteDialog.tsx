import { forwardRef, useState } from "react";
import { ApiError } from "../api";

interface DeleteDialogProps {
  plotName: string;
  onConfirm: () => Promise<void>;
}

// The parent opens it with ref.current.showModal().
export const DeleteDialog = forwardRef<HTMLDialogElement, DeleteDialogProps>(
  ({ plotName, onConfirm }, ref) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const close = () => {
      setError(null);
      if (ref && "current" in ref) ref.current?.close();
    };

    const handleDelete = async () => {
      setLoading(true);
      setError(null);
      try {
        await onConfirm();
        close();
      } catch (err: unknown) {
        // Keep the dialog open so the user sees why it failed.
        setError(err instanceof ApiError ? err.message : "Failed to delete field. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    return (
      <dialog
        ref={ref}
        onClose={() => setError(null)}
        aria-labelledby="delete-dialog-title"
        className="p-0 rounded-xl shadow-2xl backdrop:bg-stone-900/40 w-full max-w-sm border border-stone-200"
      >
        <div className="p-6 space-y-4 bg-white text-stone-900">
          <h3 id="delete-dialog-title" className="text-base font-bold text-stone-900">
            Delete {plotName}?
          </h3>
          <p className="text-xs text-stone-600">
            This permanently removes the field and its stored assessment. This action cannot be undone.
          </p>
          {error && (
            <p role="alert" className="text-xs text-rose-700 bg-rose-50 p-2 rounded border border-rose-200">
              {error}
            </p>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={close}
              className="px-3 py-1.5 text-xs font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200 rounded-md transition"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDelete}
              disabled={loading}
              className="px-3 py-1.5 text-xs font-semibold text-white bg-rose-700 hover:bg-rose-800 rounded-md transition disabled:opacity-50"
            >
              {loading ? "Deleting..." : "Delete field"}
            </button>
          </div>
        </div>
      </dialog>
    );
  }
);
DeleteDialog.displayName = "DeleteDialog";
