import { getFindings } from "../../lib/api";

const severityClasses: Record<string, string> = {
  critical: "bg-rose-100 text-rose-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-amber-100 text-amber-800",
  low: "bg-sky-100 text-sky-800",
};

function label(value: string) {
  return value.replaceAll("_", " ");
}

export default async function FindingsPage() {
  try {
    const findings = await getFindings();

    return (
      <section>
        <div className="mb-6">
          <h1 className="text-2xl font-bold tracking-tight">Findings</h1>
          <p className="mt-1 text-sm text-slate-600">Findings awaiting human review.</p>
        </div>

        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-semibold">Type</th>
                <th className="px-4 py-3 font-semibold">URL</th>
                <th className="px-4 py-3 font-semibold">Severity</th>
                <th className="px-4 py-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {findings.map((finding) => {
                const severity = finding.severity?.toLowerCase() ?? "unrated";
                const isDuplicate = finding.status === "duplicate";
                return (
                  <tr key={finding.id} className={isDuplicate ? "bg-slate-50 opacity-75" : ""}>
                    <td className="whitespace-nowrap px-4 py-3 font-medium text-slate-900">
                      {label(finding.vuln_type)}
                    </td>
                    <td className="max-w-xl truncate px-4 py-3 text-slate-600" title={finding.url}>
                      {finding.url}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${severityClasses[severity] ?? "bg-slate-100 text-slate-700"}`}>
                        {label(severity)}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${isDuplicate ? "bg-purple-100 text-purple-800" : "bg-emerald-100 text-emerald-800"}`}>
                        {label(finding.status)}
                      </span>
                    </td>
                  </tr>
                );
              })}
              {findings.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-500">No findings yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    );
  } catch {
    return <BackendUnavailable resource="findings" />;
  }
}

function BackendUnavailable({ resource }: { resource: string }) {
  return (
    <section className="rounded-lg border border-amber-200 bg-amber-50 p-5">
      <h1 className="text-lg font-semibold text-amber-950">Unable to load {resource}</h1>
      <p className="mt-1 text-sm text-amber-900">Start the backend and set NEXT_PUBLIC_API_URL if it is not running at http://localhost:8000.</p>
    </section>
  );
}
