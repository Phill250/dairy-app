"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { forgotPassword } from "@/lib/api";
import AuthShell from "@/components/AuthShell";

const RESEND_SECONDS = 60;

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [resent, setResent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(0);

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const timer = setTimeout(() => setSecondsLeft((s) => s - 1), 1000);
    return () => clearTimeout(timer);
  }, [secondsLeft]);

  async function send(isResend: boolean) {
    setSubmitting(true);
    setError(null);
    try {
      await forgotPassword(email);
      setSent(true);
      setResent(isResend);
      setSecondsLeft(RESEND_SECONDS);
    } catch (err) {
      if (err instanceof Error && err.message === "rate_limited") {
        setError("Too many requests from this connection. Please wait a while and try again.");
      } else {
        setError("We couldn't send the request. Check your connection and try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    send(false);
  }

  function useDifferentEmail() {
    setSent(false);
    setResent(false);
    setError(null);
    setSecondsLeft(0);
  }

  return (
    <AuthShell>
      <h1 className="text-xl font-bold mb-6">Forgot your password?</h1>

      {sent ? (
        <div className="space-y-4 text-sm text-slate-600">
          <p role="status">
            If <strong>{email}</strong> is registered, we&apos;ve sent a link to reset your password. It can
            take a few minutes, so check your spam folder too.
          </p>
          {resent && <p className="text-emerald-700">Sent again. Only the newest link will work.</p>}
          {error && <p className="text-red-600">{error}</p>}

          <button
            type="button"
            onClick={() => send(true)}
            disabled={submitting || secondsLeft > 0}
            className="w-full border border-emerald-600 text-emerald-700 rounded px-4 py-2 font-medium disabled:opacity-50"
          >
            {submitting ? "Sending..." : secondsLeft > 0 ? `Resend email in ${secondsLeft}s` : "Resend email"}
          </button>
          <button type="button" onClick={useDifferentEmail} className="text-emerald-700 hover:underline">
            Use a different email
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="flex flex-col gap-1 text-sm">
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="border rounded px-3 py-2"
              required
            />
          </label>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-emerald-600 text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {submitting ? "Sending..." : "Send reset link"}
          </button>
        </form>
      )}

      <p className="text-sm text-slate-500 mt-6">
        <Link href="/login" className="text-emerald-700 hover:underline">
          Back to log in
        </Link>
      </p>
    </AuthShell>
  );
}