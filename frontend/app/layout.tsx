import "./globals.css";
import type { Metadata } from "next";
import { AuthProvider } from "@/lib/auth-context";

export const metadata: Metadata = {
  title: "Smart Dairy Manager",
  description: "Track milk yield, feeding schedules, and get ML-based advice.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen text-slate-900">
        
        <div
          aria-hidden="true"
          className="fixed inset-0 -z-10 bg-slate-900 bg-cover bg-center"
          style={{
            backgroundImage:
              "linear-gradient(rgba(15,23,42,0.65), rgba(15,23,42,0.65)), url('/farm-bg.jpg')",
          }}
        />
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}