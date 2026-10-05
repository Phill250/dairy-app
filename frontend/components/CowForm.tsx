"use client";

import { useState } from "react";
import { createCow, BreedType } from "@/lib/api";

const BREED_OPTIONS: { value: BreedType; label: string }[] = [
  { value: "holstein_friesian", label: "Holstein-Friesian" },
  { value: "ankole", label: "Ankole" },
  { value: "ankole_friesian_cross", label: "Ankole x Holstein-Friesian cross" },
  { value: "other", label: "Other" },
];

export default function CowForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [breed, setBreed] = useState<BreedType>("other");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createCow({ name, breed });
      setName("");
      setBreed("other");
      onCreated();
    } catch {
      setError("Could not add cow.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow p-4 flex flex-wrap gap-3 items-end">
      <label className="flex flex-col gap-1 text-sm">
        Cow name
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="border rounded px-3 py-2"
          placeholder="e.g. Nyota"
          required
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Breed
        <select
          value={breed}
          onChange={(e) => setBreed(e.target.value as BreedType)}
          className="border rounded px-3 py-2"
        >
          {BREED_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </label>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="bg-emerald-600 text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
      >
        {submitting ? "Adding..." : "Add cow"}
      </button>
    </form>
  );
}