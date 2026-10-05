"use client";

import { useState } from "react";
import { LogRead, CowRead, deleteLog } from "@/lib/api";
import ConfirmDialog from "@/components/ConfirmDialog";

export default function LogsTable({
  logs,
  cows,
  onChanged,
}: {
  logs: LogRead[];
  cows: CowRead[];
  onChanged: () => void;
}) {
  const [pendingDelete, setPendingDelete] = useState<LogRead | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const cowName = (cowId: string) => cows.find((c) => c.id === cowId)?.name ?? "Unknown";

  async function handleConfirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteLog(pendingDelete.id);
      setPendingDelete(null);
      onChanged();
    } catch {
      setPendingDelete(null);
      setDeleteError("Could not delete that log. Please try again.");
    } finally {
      setDeleting(false);
    }
  }

  if (logs.length === 0) {
    return <p className="text-sm text-slate-500">No logs yet. Add your first entry above.</p>;
  }

  return (
    <>
      {deleteError && <p className="text-sm text-red-600 mb-2">{deleteError}</p>}

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-4 py-2">Cow</th>
              <th className="px-4 py-2">Date</th>
              <th className="px-4 py-2">Feed (kg)</th>
              <th className="px-4 py-2">Total Milk (L)</th>
              <th className="px-4 py-2">Expected (L)</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Advice</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} className="border-t">
                <td className="px-4 py-2">{cowName(log.cow_id)}</td>
                <td className="px-4 py-2">{log.date}</td>
                <td className="px-4 py-2">{log.feed}</td>
                <td className="px-4 py-2">{log.total_milk}</td>
                <td className="px-4 py-2">{log.predicted_yield?.toFixed(1) ?? "—"}</td>
                <td className="px-4 py-2">
                  <span
                    className="px-2 py-1 rounded text-white text-xs font-medium"
                    style={{ backgroundColor: log.color }}
                  >
                    {log.status}
                  </span>
                </td>
                <td className="px-4 py-2 text-slate-600">{log.advice}</td>
                <td className="px-4 py-2">
                  <button
                    onClick={() => setPendingDelete(log)}
                    className="text-red-500 hover:underline text-xs"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete this log?"
        message={
          pendingDelete
            ? `This will permanently delete ${cowName(pendingDelete.cow_id)}'s log from ${pendingDelete.date}. This can't be undone.`
            : ""
        }
        confirmLabel="Delete"
        destructive
        loading={deleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setPendingDelete(null)}
      />
    </>
  );
}