"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { QRCodeSVG } from "qrcode.react";
import { useAuth } from "@/lib/auth-context";
import { startTwoFactorSetup, enableTwoFactor, TwoFactorSetup } from "@/lib/api";
import Navbar from "@/components/Navbar";

type Step = "intro" | "scan" | "codes";

export default function AdminSecurityPage() {
  const { user, loading, refreshUser } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState<Step>("intro");
  const [setup, setSetup] = useState<TwoFactorSetup | null>(null);
  const [code, setCode] = useState("");
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (loading) return;
    if (!user) router.push("/login");
    else if (user.role !== "admin") router.push("/dashboard");
  }, [user, loading, router]);

  if (loading || !user || user.role !== "admin") {
    return <div className="p-6 text-slate-300">Loading...</div>;
  }

  const alreadyOn = user.totp_enabled === true && step !== "codes";

  async function begin() {
    setBusy(true);
    setError(null);
    try {
      setSetup(await startTwoFactorSetup());
      setStep("scan");
    } catch {
      setError("Couldn't start setup. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  async function confirm(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const codes = await enableTwoFactor(code.replace(/\s/g, ""));
      setRecoveryCodes(codes);
      setSetup(null);
      setCode("");
      setStep("codes");
    } catch {
      setError(
        "That code didn't work. Check that your phone's clock is set automatically, wait for a fresh code, and try again."
      );
    } finally {
      setBusy(false);
    }
  }

  function downloadCodes() {
    const blob = new Blob(
      [`Smart Dairy Manager recovery codes\n\n${recoveryCodes.join("\n")}\n\nEach code works once.\n`],
      { type: "text/plain" }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "smart-dairy-recovery-codes.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function finish() {
    await refreshUser();
    router.push("/admin");
  }

  return (
    <>
      <Navbar />
      <main className="max-w-xl mx-auto p-6 space-y-6">
        <h1 className="text-2xl font-bold text-white">Account security</h1>

        <div className="bg-white text-slate-900 rounded-lg shadow p-6 space-y-4">
          {alreadyOn && (
            <>
              <h2 className="text-lg font-semibold">Two-factor authentication is on</h2>
              <p className="text-sm text-slate-600">
                Logging in needs your password and a code from your authenticator app. If you lose your
                phone, use one of your saved recovery codes.
              </p>
            </>
          )}

          {!alreadyOn && step === "intro" && (
            <>
              <h2 className="text-lg font-semibold">Turn on two-factor authentication</h2>
              <p className="text-sm text-slate-600">
                You&apos;ll scan a QR code with an authenticator app (such as Google Authenticator,
                Microsoft Authenticator or Authy), then save a set of one-time recovery codes.
              </p>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <button
                onClick={begin}
                disabled={busy}
                className="bg-emerald-600 text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                {busy ? "Starting..." : "Start setup"}
              </button>
            </>
          )}

          {step === "scan" && setup && (
            <form onSubmit={confirm} className="space-y-4">
              <h2 className="text-lg font-semibold">1. Scan this QR code</h2>
              <div className="inline-block bg-white p-3 border rounded">
                <QRCodeSVG value={setup.otpauth_uri} size={176} />
              </div>
              <p className="text-xs text-slate-500">
                Can&apos;t scan? Enter this key by hand:{" "}
                <span className="font-mono break-all">{setup.secret}</span>
              </p>
              <p className="text-xs text-slate-500">
                Don&apos;t screenshot or share this code. It&apos;s the key to your account.
              </p>
              <h2 className="text-lg font-semibold">2. Enter the 6-digit code</h2>
              <input
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={7}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="border rounded px-3 py-2 tracking-widest"
                required
              />
              {error && <p className="text-sm text-red-600">{error}</p>}
              <div>
                <button
                  type="submit"
                  disabled={busy || code.trim() === ""}
                  className="bg-emerald-600 text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
                >
                  {busy ? "Checking..." : "Turn on"}
                </button>
              </div>
            </form>
          )}

          {step === "codes" && (
            <>
              <h2 className="text-lg font-semibold">Save your recovery codes</h2>
              <p className="text-sm text-slate-600">
                These are shown <strong>only once</strong>. Each works one time if you lose access to your
                authenticator app. Store them somewhere safe, away from this device.
              </p>
              <ul className="grid grid-cols-2 gap-2 font-mono text-sm bg-slate-100 rounded p-3">
                {recoveryCodes.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
              <div className="flex gap-3">
                <button
                  onClick={() => navigator.clipboard.writeText(recoveryCodes.join("\n"))}
                  className="border rounded px-3 py-1.5 text-sm"
                >
                  Copy
                </button>
                <button onClick={downloadCodes} className="border rounded px-3 py-1.5 text-sm">
                  Download
                </button>
              </div>
              <p className="text-sm text-slate-600">
                Your authenticator codes work only once, so after this, wait for the next 6-digit code
                before logging in again.
              </p>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={saved} onChange={(e) => setSaved(e.target.checked)} />
                I&apos;ve saved these codes somewhere safe
              </label>
              <button
                onClick={finish}
                disabled={!saved}
                className="bg-emerald-600 text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                Done
              </button>
            </>
          )}
        </div>
      </main>
    </>
  );
}