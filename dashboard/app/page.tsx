"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { createScan, getPrograms, getScans, Program, Scan } from "../lib/api";

const statusClasses: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800",
  running: "bg-purple-100 text-purple-800",
  completed: "bg-emerald-100 text-emerald-800",
  failed: "bg-rose-100 text-rose-800",
};

export default function HomePage() {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [selectedProgramId, setSelectedProgramId] = useState<number | "">("");
  const [targetUrl, setTargetUrl] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);
  const [backendError, setBackendError] = useState<boolean>(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setBackendError(false);
      const [progs, scanList] = await Promise.all([getPrograms(), getScans()]);
      setPrograms(progs);
      setScans(scanList);
      if (progs.length > 0 && selectedProgramId === "") {
        setSelectedProgramId(progs[0].id);
        if (progs[0].website_url) {
          setTargetUrl(progs[0].website_url);
        }
      }
    } catch {
      setBackendError(true);
    }
  }

  function handleProgramChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const pId = Number(e.target.value);
    setSelectedProgramId(pId);
    const prog = programs.find((p) => p.id === pId);
    if (prog && prog.website_url) {
      setTargetUrl(prog.website_url);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg(null);
    setInfoMsg(null);

    if (!selectedProgramId) {
      setErrorMsg("Please select a target program.");
      return;
    }
    if (!targetUrl.trim()) {
      setErrorMsg("Please enter a target URL.");
      return;
    }

    setLoading(true);

    try {
      // 1. POST /scans on backend (enforces scope check server-side)
      const createdScan = await createScan(Number(selectedProgramId), targetUrl.trim());

      // Refresh recent scans table immediately
      const updatedScans = await getScans();
      setScans(updatedScans);

      // 2. Call scanner service POST /scan (gracefully handle if scanner is not running)
      try {
        const scannerUrl = process.env.NEXT_PUBLIC_SCANNER_URL ?? "http://localhost:8002";
        const resp = await fetch(`${scannerUrl}/scan`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ program_id: Number(selectedProgramId), target_url: targetUrl.trim() }),
        });
        if (resp.ok) {
          setInfoMsg(`Scan #${createdScan.id} successfully queued and scanner started!`);
        } else {
          setInfoMsg(`Scan #${createdScan.id} created (pending). Scanner not available yet.`);
        }
      } catch {
        setInfoMsg(`Scan #${createdScan.id} created (pending). Scanner not available yet.`);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create scan.");
    } finally {
      setLoading(false);
    }
  }

  if (backendError) {
    return (
      <section className="rounded-lg border border-amber-200 bg-amber-50 p-5">
        <h1 className="text-lg font-semibold text-amber-950">Unable to load data</h1>
        <p className="mt-1 text-sm text-amber-900">
          Start the backend and set NEXT_PUBLIC_API_URL if it is not running at http://localhost:8000.
        </p>
      </section>
    );
  }

  const programNames: Record<number, string> = {};
  for (const prog of programs) {
    programNames[prog.id] = prog.name;
  }

  return (
    <section className="space-y-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Home</h1>
        <p className="mt-1 text-sm text-slate-600">
          Trigger vulnerability scans and view recent scan activity.
        </p>
      </div>

      {/* Feedback Alerts */}
      {errorMsg && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          <strong className="font-semibold">Scope / Validation Error:</strong> {errorMsg}
        </div>
      )}

      {infoMsg && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          {infoMsg}
        </div>
      )}

      {/* Scan Trigger Form */}
      <form onSubmit={handleSubmit} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">New Scan Request</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">
              Program
            </label>
            <select
              value={selectedProgramId}
              onChange={handleProgramChange}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            >
              {programs.map((prog) => (
                <option key={prog.id} value={prog.id}>
                  {prog.name}
                </option>
              ))}
              {programs.length === 0 && <option value="">No programs available</option>}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">
              Target URL
            </label>
            <input
              type="text"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              placeholder="http://example.com/target"
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={loading || programs.length === 0}
            className="rounded-md bg-sky-700 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-600 disabled:opacity-50"
          >
            {loading ? "Submitting..." : "Start Scan"}
          </button>
        </div>
      </form>

      {/* Recent Scans Table */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-slate-900">Recent Scans</h2>
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-semibold">Scan ID</th>
                <th className="px-4 py-3 font-semibold">Program</th>
                <th className="px-4 py-3 font-semibold">Target URL</th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="px-4 py-3 font-semibold">Started At</th>
                <th className="px-4 py-3 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {scans.map((scan) => {
                const status = scan.status?.toLowerCase() ?? "pending";
                return (
                  <tr key={scan.id}>
                    <td className="whitespace-nowrap px-4 py-3 font-medium text-slate-900">#{scan.id}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                      {programNames[scan.program_id] ?? `Prog #${scan.program_id}`}
                    </td>
                    <td className="max-w-md truncate px-4 py-3 text-slate-600" title={scan.target_url}>
                      {scan.target_url}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${statusClasses[status] ?? "bg-slate-100 text-slate-700"}`}>
                        {scan.status}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-500">
                      {new Date(scan.started_at).toLocaleString()}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <Link
                        href="/findings"
                        className="text-xs font-medium text-sky-700 hover:underline"
                      >
                        View Findings →
                      </Link>
                    </td>
                  </tr>
                );
              })}
              {scans.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                    No scans recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
