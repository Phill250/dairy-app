"use client";

import { MetricsRead } from "@/lib/api";
import StatCard from "@/components/StatCard";

const STATUS_COLORS: Record<string, string> = {
  "Good Condition": "bg-emerald-500",
  "Warning / Low": "bg-amber-500",
  "Critical Alert": "bg-red-500",
};

export default function AdminMetrics({ metrics }: { metrics: MetricsRead }) {
  const totalStatusLogs = Object.values(metrics.status_breakdown).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <StatCard label="Total Farmers" value={metrics.total_farmers} />
        <StatCard label="Total Cows" value={metrics.total_cows} />
        <StatCard label="Total Logs" value={metrics.total_logs} />
        <StatCard label="Avg Yield (L)" value={metrics.average_total_milk?.toFixed(1) ?? "—"} accent="emerald" />
        <StatCard label="Avg Feed (kg)" value={metrics.average_feed?.toFixed(1) ?? "—"} />
        <StatCard
          label="ML Model Usage"
          value={`${(metrics.ml_model_usage_rate * 100).toFixed(0)}%`}
          accent="emerald"
        />
      </div>

      <div className="bg-white rounded-xl shadow p-4">
        <p className="text-sm font-medium mb-3">Herd status across all farms</p>
        {totalStatusLogs === 0 ? (
          <p className="text-sm text-slate-400">No logs yet.</p>
        ) : (
          <div className="space-y-3">
            <div className="flex h-3 rounded-full overflow-hidden">
              {Object.entries(metrics.status_breakdown).map(([status, count]) => (
                <div
                  key={status}
                  className={STATUS_COLORS[status] ?? "bg-slate-400"}
                  style={{ width: `${(count / totalStatusLogs) * 100}%` }}
                  title={`${status}: ${count}`}
                />
              ))}
            </div>
            <div className="flex flex-wrap gap-4 text-sm">
              {Object.entries(metrics.status_breakdown).map(([status, count]) => (
                <div key={status} className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${STATUS_COLORS[status] ?? "bg-slate-400"}`} />
                  <span>{status}: <strong>{count}</strong></span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}