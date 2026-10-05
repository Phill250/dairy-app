"use client";

import { LogRead, CowRead } from "@/lib/api";

export default function CriticalAlertsBanner({ logs, cows }: { logs: LogRead[]; cows: CowRead[] }) {
  const latestByCowId = new Map<string, LogRead>();
  for (const log of logs) {
    const existing = latestByCowId.get(log.cow_id);
    if (!existing || log.date > existing.date) {
      latestByCowId.set(log.cow_id, log);
    }
  }

  const critical = Array.from(latestByCowId.values()).filter((log) => log.status === "Critical Alert");
  if (critical.length === 0) return null;

  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-4">
      <p className="font-semibold text-red-800 mb-2">
        ⚠️ {critical.length} cow{critical.length > 1 ? "s need" : " needs"} attention
      </p>
      <ul className="space-y-1">
        {critical.map((log) => {
          const cow = cows.find((c) => c.id === log.cow_id);
          return (
            <li key={log.id} className="text-sm text-red-700">
              <strong>{cow?.name ?? "A cow"}</strong>: {log.advice}
            </li>
          );
        })}
      </ul>
    </div>
  );
}