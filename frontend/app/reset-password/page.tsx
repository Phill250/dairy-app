"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { resetPassword } from "@/lib/api";
import AuthShell from "@/components/AuthShell";
import PasswordInput from "@/components/PasswordInput";

function ResetPasswordForm() {
  const router = useRouter();
  const token = useSearchParams().get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setError("Passwords don't match.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await resetPassword(token, password);
      setDone(true);
      setTimeout(() => router.push("/login"), 2000);
    } catch {
      setError("This reset link is invalid or has expired. Please request a new one.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!token) {
    return (
      <p className="text-sm text-slate-600">
        This link is missing its reset code.{" "}
        <Link href="/forgot-password" className="text-emerald-700 hover:underline">
          Request a new one
        </Link>
        .
      </p>
    );
  }

  if (done) {
    return <p className="text-sm text-emerald-700">Password updated. Taking you to log in...</p>;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <PasswordInput
        label="New password (min 8 characters)"
        value={password}
        onChange={setPassword}
        autoComplete="new-password"
        minLength={8}
        maxLength={72}
      />
      <PasswordInput
        label="Confirm new password"
        value={confirm}
        onChange={setConfirm}
        autoComplete="new-password"
        maxLength={72}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="w-full bg-emerald-600 text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
      >
        {submitting ? "Saving..." : "Set new password"}
      </button>
      <p className="text-sm text-slate-500">
        Link not working?{" "}
        <Link href="/forgot-password" className="text-emerald-700 hover:underline">
          Request a new one
        </Link>
      </p>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <AuthShell>
      <h1 className="text-xl font-bold mb-6">Choose a new password</h1>
      <Suspense fallback={<p className="text-sm text-slate-500">Loading...</p>}>
        <ResetPasswordForm />
      </Suspense>
    </AuthShell>
  );
}