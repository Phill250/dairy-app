"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { registerFarmer } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import AuthShell from "@/components/AuthShell";
import PasswordInput from "@/components/PasswordInput";

export default function RegisterPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await registerFarmer({ first_name: firstName, last_name: lastName, email, password });
    } catch {
      setError("Could not register. That email may already be in use.");
      setSubmitting(false);
      return;
    }

    try {
      await login(email, password);
      router.push("/dashboard");
    } catch {
      // The account exists; only the automatic sign-in failed
      setError("Your account was created, but we couldn't sign you in automatically. Please log in.");
      setSubmitting(false);
    }
  }

  return (
    <AuthShell>
      <h1 className="text-xl font-bold mb-6">Register as a farmer</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <label className="flex flex-col gap-1 text-sm">
            First name
            <input
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="border rounded px-3 py-2"
              maxLength={100}
              required
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Last name
            <input
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              className="border rounded px-3 py-2"
              maxLength={100}
              required
            />
          </label>
        </div>
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
          label="Password (min 8 characters)"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
          minLength={8}
          maxLength={72}
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-emerald-600 text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {submitting ? "Registering..." : "Register"}
        </button>
      </form>
      <p className="text-sm text-slate-500 mt-4">
        Already have an account?{" "}
        <Link href="/login" className="text-emerald-700 hover:underline">
          Log in
        </Link>
      </p>
    </AuthShell>
  );
}