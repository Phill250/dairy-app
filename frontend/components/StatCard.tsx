export default function StatCard({
    label,
    value,
    accent = "slate",
  }: {
    label: string;
    value: string | number;
    accent?: "slate" | "emerald" | "amber" | "red";
  }) {
    const accentClasses: Record<string, string> = {
      slate: "text-slate-900",
      emerald: "text-emerald-600",
      amber: "text-amber-600",
      red: "text-red-600",
    };
  
    return (
      <div className="bg-white rounded-xl shadow p-4">
        <p className="text-xs text-slate-800 uppercase tracking-wide">{label}</p>
        <p className={`text-3xl font-bold mt-1 ${accentClasses[accent]}`}>{value}</p>
      </div>
    );
  }