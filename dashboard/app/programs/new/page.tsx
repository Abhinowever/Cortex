"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createProgram } from "../../../lib/api";

export default function NewProgramPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [domains, setDomains] = useState<string[]>([""]);
  const [scopeNotes, setScopeNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  function handleAddDomain() {
    setDomains([...domains, ""]);
  }

  function handleRemoveDomain(index: number) {
    if (domains.length === 1) {
      setDomains([""]);
    } else {
      setDomains(domains.filter((_, i) => i !== index));
    }
  }

  function handleDomainChange(index: number, value: string) {
    const updated = [...domains];
    updated[index] = value;
    setDomains(updated);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg(null);

    const trimmedName = name.trim();
    const trimmedBaseUrl = baseUrl.trim();

    if (!trimmedName) {
      setErrorMsg("Program Name is required.");
      return;
    }
    if (!trimmedBaseUrl) {
      setErrorMsg("Base URL (Website URL) is required.");
      return;
    }

    // Filter out blank domains
    const cleanedDomains = domains
      .map((d) => d.trim())
      .filter((d) => d.length > 0);

    setLoading(true);

    try {
      await createProgram({
        name: trimmedName,
        website_url: trimmedBaseUrl,
        in_scope_domains: cleanedDomains,
        rules: scopeNotes.trim() || null,
      });

      router.push("/programs");
      router.refresh();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create program.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="max-w-2xl mx-auto space-y-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Add New Program</h1>
          <p className="mt-1 text-sm text-slate-600">
            Define an authorized target and its explicitly approved testing scope.
          </p>
        </div>
        <Link
          href="/programs"
          className="text-sm font-medium text-slate-600 hover:text-slate-900"
        >
          ← Back to Programs
        </Link>
      </div>

      {/* Warning Notice */}
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <strong className="font-semibold">Authorization Requirement:</strong> Only add domains you are explicitly authorized to test under an active bug bounty or vulnerability disclosure program.
      </div>

      {/* Validation Error Alert */}
      {errorMsg && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          <strong className="font-semibold">Error:</strong> {errorMsg}
        </div>
      )}

      {/* Program Form */}
      <form onSubmit={handleSubmit} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm space-y-5">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">
            Program Name <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Acme Security Program"
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">
            Base URL <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="e.g. https://acme.example"
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
              In-Scope Domains
            </label>
            <button
              type="button"
              onClick={handleAddDomain}
              className="text-xs font-semibold text-sky-700 hover:text-sky-800"
            >
              + Add another domain
            </button>
          </div>
          <div className="space-y-2">
            {domains.map((domain, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  value={domain}
                  onChange={(e) => handleDomainChange(index, e.target.value)}
                  placeholder="e.g. app.acme.example"
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                />
                {domains.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveDomain(index)}
                    className="px-3 py-2 text-xs font-semibold text-rose-600 hover:text-rose-800 rounded-md border border-slate-200 bg-slate-50 hover:bg-slate-100"
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Specify domain names allowed for crawling and payload testing.
          </p>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">
            Scope Notes / Rules (Optional)
          </label>
          <textarea
            rows={3}
            value={scopeNotes}
            onChange={(e) => setScopeNotes(e.target.value)}
            placeholder="e.g. Use test accounts only, do not impact service availability."
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <Link
            href="/programs"
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-sky-700 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-600 disabled:opacity-50"
          >
            {loading ? "Creating..." : "Save Program"}
          </button>
        </div>
      </form>
    </section>
  );
}
