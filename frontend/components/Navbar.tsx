"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import ConfirmDialog from "@/components/ConfirmDialog";

export default function Navbar() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleConfirmLogout() {
    setLoggingOut(true);
    await logout();
    setConfirmOpen(false);
    router.push("/login");
  }

  if (!user) return null;

  return (
    <>
      <nav className="bg-white border-b px-6 py-3 flex items-center justify-between">
        <div className="font-semibold">Smart Dairy Manager</div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-slate-500">
            {user.first_name} {user.last_name} ({user.role})
          </span>
          {user.role === "farmer" && (
            <Link href="/dashboard" className="text-emerald-700 hover:underline">
              Dashboard
            </Link>
          )}
          {user.role === "admin" && (
            <Link href="/admin" className="text-emerald-700 hover:underline">
              Metrics
            </Link>
          )}
          <button onClick={() => setConfirmOpen(true)} className="text-red-600 hover:underline">
            Log out
          </button>
        </div>
      </nav>

      <ConfirmDialog
        open={confirmOpen}
        title="Log out?"
        message="You'll need to sign in again to access your farm."
        confirmLabel="Log out"
        loading={loggingOut}
        onConfirm={handleConfirmLogout}
        onCancel={() => setConfirmOpen(false)}
      />
    </>
  );
}