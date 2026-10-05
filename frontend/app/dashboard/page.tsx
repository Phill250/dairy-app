"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { fetchCows, fetchLogs, CowRead, LogRead } from "@/lib/api";
import Navbar from "@/components/Navbar";
import CowForm from "@/components/CowForm";
import CowCard from "@/components/CowCard";
import CriticalAlertsBanner from "@/components/CriticalAlertsBanner";
import LogForm from "@/components/LogForm";
import LogsTable from "@/components/LogsTable";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [cows, setCows] = useState<CowRead[]>([]);
  const [logs, setLogs] = useState<LogRead[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [selectedCowId, setSelectedCowId] = useState<string | null>(null);
  const [showAddCow, setShowAddCow] = useState(false);

  const loadData = useCallback(async () => {
    setDataLoading(true);
    const [cowsData, logsData] = await Promise.all([fetchCows(), fetchLogs()]);
    setCows(cowsData);
    setLogs(logsData);
    setDataLoading(false);
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.push("/login");
      return;
    }
    if (user.role !== "farmer") {
      router.push("/admin");
      return;
    }
    loadData();
  }, [user, loading, router, loadData]);

  useEffect(() => {
    if (!selectedCowId && cows.length > 0) setSelectedCowId(cows[0].id);
  }, [cows, selectedCowId]);

  const latestLogByCowId = useMemo(() => {
    const map = new Map<string, LogRead>();
    for (const log of logs) {
      const existing = map.get(log.cow_id);
      if (!existing || log.date > existing.date) map.set(log.cow_id, log);
    }
    return map;
  }, [logs]);

  const selectedCowLogs = useMemo(
    () => logs.filter((l) => l.cow_id === selectedCowId),
    [logs, selectedCowId]
  );
  const selectedCow = cows.find((c) => c.id === selectedCowId);

  if (loading || !user || user.role !== "farmer") {
    return <div className="p-6 text-slate-300">Loading...</div>;
  }

  return (
    <>
      <Navbar />
      <main className="max-w-5xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">My Farm</h1>
          <button
            onClick={() => setShowAddCow((v) => !v)}
            className="text-sm text-emerald-300 font-medium hover:underline"
          >
            {showAddCow ? "Cancel" : "+ Add a cow"}
          </button>
        </div>

        {dataLoading ? (
          <p className="text-slate-300">Loading your farm...</p>
        ) : (
          <>
            <CriticalAlertsBanner logs={logs} cows={cows} />

            {showAddCow && (
              <CowForm
                onCreated={() => {
                  loadData();
                  setShowAddCow(false);
                }}
              />
            )}

            {cows.length === 0 ? (
              <div className="bg-white rounded-xl shadow p-8 text-center">
                <p className="text-slate-500 mb-3">You haven&apos;t added any cows yet.</p>
                <button
                  onClick={() => setShowAddCow(true)}
                  className="bg-emerald-600 text-white rounded px-4 py-2 text-sm font-medium"
                >
                  Add your first cow
                </button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {cows.map((cow) => (
                    <CowCard
                      key={cow.id}
                      cow={cow}
                      latestLog={latestLogByCowId.get(cow.id)}
                      selected={cow.id === selectedCowId}
                      onSelect={() => setSelectedCowId(cow.id)}
                    />
                  ))}
                </div>

                {selectedCow && (
                  <div className="space-y-6">
                    <h2 className="text-lg font-semibold text-white">{selectedCow.name}&apos;s records</h2>
                    <LogForm
                      cows={cows}
                      selectedCowId={selectedCow.id}
                      onCowChange={setSelectedCowId}
                      onCreated={loadData}
                    />
                    <LogsTable logs={selectedCowLogs} cows={cows} onChanged={loadData} />
                  </div>
                )}
              </>
            )}
          </>
        )}
      </main>
    </>
  );
}