import type { ReactNode } from "react";

export default function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <main className="w-full max-w-sm p-6 bg-white/95 rounded-xl shadow-lg">{children}</main>
    </div>
  );
}