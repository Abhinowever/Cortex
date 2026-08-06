import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "Cortex",
  description: "Cortex review dashboard",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-slate-200 bg-white">
          <nav className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-4" aria-label="Main navigation">
            <Link href="/" className="text-lg font-bold tracking-tight text-slate-900">
              Cortex
            </Link>
            <Link href="/" className="text-sm font-medium text-slate-600 hover:text-slate-950">
              Home
            </Link>
            <Link href="/findings" className="text-sm font-medium text-slate-600 hover:text-slate-950">
              Findings
            </Link>
            <Link href="/disclosures" className="text-sm font-medium text-slate-600 hover:text-slate-950">
              Disclosures
            </Link>
            <Link href="/programs" className="text-sm font-medium text-slate-600 hover:text-slate-950">
              Programs
            </Link>
          </nav>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
