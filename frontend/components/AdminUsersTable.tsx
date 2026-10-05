"use client";

import { AdminUserSummary } from "@/lib/api";

export default function AdminUsersTable({ users }: { users: AdminUserSummary[] }) {
  function formatDate(dateStr: string | null): string {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: "numeric", month: "short", day: "numeric",
    });
  }

  if (users.length === 0) {
    return <p className="text-sm text-slate-500">No farmer accounts yet.</p>;
  }

  return (
    <div className="bg-white rounded-xl shadow overflow-hidden">
      <div className="px-4 py-3 border-b">
        <p className="text-sm font-medium">Farmer accounts</p>
        <p className="text-xs text-slate-500 mt-1">
          Non-identifying view only, names and emails are never shown here, consistent with
          the platform&apos;s privacy design.
        </p>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-slate-100 text-left">
          <tr>
            <th className="px-4 py-2">Account ID</th>
            <th className="px-4 py-2">Joined</th>
            <th className="px-4 py-2">Cows</th>
            <th className="px-4 py-2">Logs</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id} className="border-t">
              <td className="px-4 py-2 font-mono text-xs text-slate-500">
                {user.id.slice(0, 8)}…
              </td>
              <td className="px-4 py-2">{formatDate(user.created_at)}</td>
              <td className="px-4 py-2">{user.cow_count}</td>
              <td className="px-4 py-2">{user.log_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}