"use client";

import { useState } from "react";
import type { AvailabilityRequestPayload } from "@/types";

interface AvailabilityFormProps {
  onSubmit: (payload: AvailabilityRequestPayload) => void;
  onCancel: () => void;
  loading?: boolean;
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function AvailabilityForm({ onSubmit, onCancel, loading }: AvailabilityFormProps) {
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [adults, setAdults] = useState(2);
  const [validationError, setValidationError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!checkIn || !checkOut) {
      setValidationError("Please choose both a check-in and check-out date.");
      return;
    }
    if (checkOut <= checkIn) {
      setValidationError("Check-out date must be after the check-in date.");
      return;
    }
    if (adults < 1 || adults > 8) {
      setValidationError("Number of guests must be between 1 and 8.");
      return;
    }

    setValidationError(null);
    onSubmit({ checkIn, checkOut, adults });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-3 rounded-xl border border-brass/30 bg-brass/[0.05] p-4"
    >
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm font-medium text-teal-dark">Check availability</p>
        <button
          type="button"
          onClick={onCancel}
          className="text-sm text-ink/50 hover:text-ink/80"
        >
          Cancel
        </button>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <label className="text-sm text-ink/70">
          Check-in
          <input
            type="date"
            value={checkIn}
            min={todayIso()}
            onChange={(e) => setCheckIn(e.target.value)}
            className="mt-1 w-full rounded-lg border border-teal/15 bg-white px-3 py-2 text-sm text-ink
                       focus-visible:outline focus-visible:outline-2 focus-visible:outline-brass"
            required
          />
        </label>

        <label className="text-sm text-ink/70">
          Check-out
          <input
            type="date"
            value={checkOut}
            min={checkIn || todayIso()}
            onChange={(e) => setCheckOut(e.target.value)}
            className="mt-1 w-full rounded-lg border border-teal/15 bg-white px-3 py-2 text-sm text-ink
                       focus-visible:outline focus-visible:outline-2 focus-visible:outline-brass"
            required
          />
        </label>

        <label className="text-sm text-ink/70">
          Guests
          <input
            type="number"
            min={1}
            max={8}
            value={adults}
            onChange={(e) => setAdults(Number(e.target.value))}
            className="mt-1 w-full rounded-lg border border-teal/15 bg-white px-3 py-2 text-sm text-ink
                       focus-visible:outline focus-visible:outline-2 focus-visible:outline-brass"
            required
          />
        </label>
      </div>

      {validationError && (
        <p className="mt-2 text-sm text-rust">{validationError}</p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="mt-3 w-full rounded-lg bg-teal px-4 py-2 text-sm font-medium text-ivory
                   transition-colors hover:bg-teal-light disabled:cursor-not-allowed disabled:opacity-60
                   sm:w-auto"
      >
        {loading ? "Checking…" : "Check availability"}
      </button>
    </form>
  );
}
