"use client";

import { useState, useEffect } from "react";
import { createLog, predictYield, CowRead } from "@/lib/api";

export default function LogForm({
  cows,
  selectedCowId,
  onCowChange,
  onCreated,
}: {
  cows: CowRead[];
  selectedCowId: string;
  onCowChange: (id: string) => void;
  onCreated: () => void;
}) {
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [feed, setFeed] = useState(10);
  const [milkingTimes, setMilkingTimes] = useState(2);
  const [milkings, setMilkings] = useState<number[]>([0, 0]);
  const [expectedYield, setExpectedYield] = useState<number | null>(null);
  const [modelUsed, setModelUsed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setMilkings((prev) => {
      const next = [...prev];
      while (next.length < milkingTimes) next.push(0);
      return next.slice(0, milkingTimes);
    });
  }, [milkingTimes]);

  useEffect(() => {
    if (!selectedCowId) return;
    const timeout = setTimeout(() => {
      predictYield(selectedCowId, feed, milkingTimes)
        .then((res) => {
          setExpectedYield(res.expected_yield);
          setModelUsed(res.model_used);
        })
        .catch(() => setExpectedYield(null));
    }, 300);
    return () => clearTimeout(timeout);
  }, [selectedCowId, feed, milkingTimes]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCowId) {
      setError("Add a cow first.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await createLog({ cow_id: selectedCowId, date, feed, milkingTimes, milkings });
      onCreated();
      setMilkings(new Array(milkingTimes).fill(0));
    } catch {
      setError("Could not save log.");
    } finally {
      setSubmitting(false);
    }
  }

  if (cows.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow p-6 text-slate-500 text-sm">
        Add a cow above before logging a milking.
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow p-6 space-y-4">
      <h2 className="text-lg font-semibold">Log today&apos;s milking</h2>

      <div className="grid grid-cols-2 gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Cow
          <select
            value={selectedCowId}
            onChange={(e) => onCowChange(e.target.value)}
            className="border rounded px-3 py-2"
          >
            {cows.map((cow) => (
              <option key={cow.id} value={cow.id}>{cow.name}</option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Date
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="border rounded px-3 py-2"
            required
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Feed (kg)
          <input
            type="number"
            step="0.1"
            min="0"
            value={feed}
            onChange={(e) => setFeed(parseFloat(e.target.value) || 0)}
            className="border rounded px-3 py-2"
            required
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Milkings per day
          <input
            type="number"
            min={1}
            max={10}
            value={milkingTimes}
            onChange={(e) => setMilkingTimes(parseInt(e.target.value) || 1)}
            className="border rounded px-3 py-2"
            required
          />
        </label>
      </div>

      <div>
        <p className="text-sm font-medium mb-2">Liters per milking</p>
        <div className="flex gap-2 flex-wrap">
          {milkings.map((val, idx) => (
            <input
              key={idx}
              type="number"
              step="0.1"
              min="0"
              value={val}
              onChange={(e) => {
                const next = [...milkings];
                next[idx] = parseFloat(e.target.value) || 0;
                setMilkings(next);
              }}
              className="border rounded px-3 py-2 w-24"
              placeholder={`#${idx + 1}`}
              required
            />
          ))}
        </div>
      </div>

      {expectedYield !== null && (
        <p className="text-sm text-slate-600">
          Expected yield for this cow: <strong>{expectedYield.toFixed(1)}L</strong>{" "}
          {!modelUsed && <span className="text-amber-600">(fallback estimate)</span>}
        </p>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="bg-emerald-600 text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
      >
        {submitting ? "Saving..." : "Save log"}
      </button>
    </form>
  );
}