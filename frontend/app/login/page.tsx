"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { AuthError } from "@/lib/api";
import AuthShell from "@/components/AuthShell";
import PasswordInput from "@/components/PasswordInput";

function messageFor(err: unknown, fallback: string): string {
  if (err instanceof AuthError) {
    if (err.status === 423)
      return "This account is temporarily locked after too many failed attempts. Please try again in a few minutes.";
    if (err.status === 429) return "Too many attempts. Please wait a minute and try again.";
  }
  return fallback;
}

export default function LoginPage() {
  const { login, completeTwoFactor } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [useRecovery, setUseRecovery] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const result = await login(email, password);
      if (result.status === "mfa_required") {
        setMfaToken(result.mfaToken);
        setPassword("");
      } else {
        router.push("/");
      }
    } catch (err) {
      setError(messageFor(err, "Incorrect email or password."));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCode(e: React.FormEvent) {
    e.preventDefault();
    if (!mfaToken) return;
    setSubmitting(true);
    setError(null);
    try {
      const cleaned = useRecovery ? code.trim() : code.replace(/\s/g, "");
      await completeTwoFactor(mfaToken, cleaned);
      router.push("/");
    } catch (err) {
      setError(
        messageFor(
          err,
          useRecovery
            ? "That recovery code didn't work."
            : "That code didn't work, or it expired. Wait for a fresh code and try again, or start over."
        )
      );
    } finally {
      setSubmitting(false);
    }
  }

  function startOver() {
    setMfaToken(null);
    setCode("");
    setUseRecovery(false);
    setError(null);
  }

  if (mfaToken) {
    return (
      <AuthShell>
        <h1 className="text-xl font-bold mb-2">Two-factor authentication</h1>
        <p className="text-sm text-slate-500 mb-6">
          {useRecovery
            ? "Enter one of your saved recovery codes. Each one works only once."
            : "Enter the 6-digit code from your authenticator app."}
        </p>
        <form onSubmit={handleCode} className="space-y-4">
          <label className="flex flex-col gap-1 text-sm">
            {useRecovery ? "Recovery code" : "Authentication code"}
            <input
              type="text"
              inputMode={useRecovery ? "text" : "numeric"}
              autoComplete="one-time-code"
              maxLength={useRecovery ? 20 : 7}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="border rounded px-3 py-2 tracking-widest"
              autoFocus
              required
            />
          </label>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={submitting || code.trim() === ""}
            className="w-full bg-emerald-600 text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {submitting ? "Checking..." : "Verify"}
          </button>
        </form>
        <p className="text-sm mt-4">
          <button
            type="button"
            onClick={() => { setUseRecovery(!useRecovery); setCode(""); setError(null); }}
            className="text-emerald-700 hover:underline"
          >
            {useRecovery ? "Use my authenticator app instead" : "Use a recovery code instead"}
          </button>
        </p>
        <p className="text-sm mt-2">
          <button type="button" onClick={startOver} className="text-slate-500 hover:underline">
            Start over
          </button>
        </p>
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <h1 className="text-xl font-bold mb-6">Log in</h1>
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
        <PasswordInput
          label="Password"
          value={password}
          onChange={setPassword}
          autoComplete="current-password"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-emerald-600 text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {submitting ? "Logging in..." : "Log in"}
        </button>
      </form>
      <p className="text-sm text-slate-500 mt-4">
        <Link href="/forgot-password" className="text-emerald-700 hover:underline">
          Forgot your password?
        </Link>
      </p>
      <p className="text-sm text-slate-500 mt-2">
        No account?{" "}
        <Link href="/register" className="text-emerald-700 hover:underline">
          Register as a farmer
        </Link>
      </p>
    </AuthShell>
  );
}