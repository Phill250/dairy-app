"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { fetchAdminMetrics, fetchAdminUsers, MetricsRead, AdminUserSummary } from "@/lib/api";
import Navbar from "@/components/Navbar";
import AdminMetrics from "@/components/AdminMetrics";
import AdminUsersTable from "@/components/AdminUsersTable";

export default function AdminPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [metrics, setMetrics] = useState<MetricsRead | null>(null);
  const [users, setUsers] = useState<AdminUserSummary[] | null>(null);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.push("/login");
      return;
    }
    if (user.role !== "admin") {
      router.push("/dashboard");
      return;
    }
    fetchAdminMetrics().then(setMetrics);
    fetchAdminUsers().then(setUsers);
  }, [user, loading, router]);

  if (loading || !user || user.role !== "admin") {
    return <div className="p-6 text-slate-300">Loading...</div>;
  }

  return (
    <>
      <Navbar />
      <main className="max-w-4xl mx-auto p-6 space-y-8">
        <h1 className="text-2xl font-bold text-white">Platform Metrics</h1>
        {metrics ? <AdminMetrics metrics={metrics} /> : <p className="text-slate-300">Loading...</p>}

        <div>
          <h2 className="text-xl font-bold text-white mb-4">Farmer Accounts</h2>
          {users ? <AdminUsersTable users={users} /> : <p className="text-slate-300">Loading...</p>}
        </div>
      </main>
    </>
  );
}