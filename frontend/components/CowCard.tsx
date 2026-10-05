"use client";

import { CowRead, LogRead } from "@/lib/api";

const BREED_LABELS: Record<string, string> = {
  holstein_friesian: "Holstein-Friesian",
  ankole: "Ankole",
  ankole_friesian_cross: "Ankole × Holstein-Friesian",
  other: "Other",
};

export default function CowCard({
  cow,
  latestLog,
  selected,
  onSelect,
}: {
  cow: CowRead;
  latestLog: LogRead | undefined;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className={`text-left bg-white rounded-xl shadow p-4 border-2 transition-colors ${
        selected ? "border-emerald-500" : "border-transparent hover:border-slate-200"
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="font-semibold">{cow.name}</p>
          <p className="text-xs text-slate-500">{BREED_LABELS[cow.breed] ?? cow.breed}</p>
        </div>
        {latestLog && (
          <span
            className="px-2 py-1 rounded text-white text-xs font-medium whitespace-nowrap"
            style={{ backgroundColor: latestLog.color }}
          >
            {latestLog.status}
          </span>
        )}
      </div>
      {latestLog ? (
        <p className="text-sm text-slate-600 mt-3">
          Last logged: <strong>{latestLog.total_milk}L</strong> on {latestLog.date}
        </p>
      ) : (
        <p className="text-sm text-slate-400 mt-3">No milking logged yet</p>
      )}
    </button>
  );
}