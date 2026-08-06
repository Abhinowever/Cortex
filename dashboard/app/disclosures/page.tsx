import { getDisclosures } from "../../lib/api";

export default async function DisclosuresPage() {
  try {
    const disclosures = await getDisclosures();

    return (
      <section>
        <div className="mb-6">
          <h1 className="text-2xl font-bold tracking-tight">Disclosures & Timeline</h1>
          <p className="mt-1 text-sm text-slate-600">Track submission status, timeline events, and CVE tags.</p>
        </div>

        <div className="space-y-4">
          {disclosures.map((disclosure) => (
            <div key={disclosure.id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-slate-900">
                    Disclosure #{disclosure.id} (Finding #{disclosure.finding_id})
                  </h2>
                  <p className="mt-1 text-xs text-slate-500">
                    Created: {new Date(disclosure.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  {disclosure.cve_id && (
                    <span className="rounded bg-indigo-100 px-2.5 py-1 text-xs font-mono font-semibold text-indigo-800">
                      {disclosure.cve_id}
                    </span>
                  )}
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold capitalize text-slate-700">
                    {disclosure.status}
                  </span>
                </div>
              </div>

              {/* Disclosure Timeline Events */}
              <div className="mt-4 border-t border-slate-100 pt-4">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Timeline Events</h3>
                {disclosure.timeline_events && disclosure.timeline_events.length > 0 ? (
                  <ul className="mt-2 space-y-2">
                    {disclosure.timeline_events.map((event, idx) => (
                      <li key={idx} className="flex items-start text-xs text-slate-600">
                        <span className="mr-2 h-2 w-2 rounded-full bg-indigo-500 mt-1"></span>
                        <div>
                          <strong className="capitalize text-slate-800">{event.event}</strong> - {event.timestamp}
                          {event.notes && <p className="text-slate-500">{event.notes}</p>}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-1 text-xs text-slate-400">No timeline events recorded yet.</p>
                )}
              </div>
            </div>
          ))}

          {disclosures.length === 0 && (
            <div className="rounded-lg border border-slate-200 bg-white p-8 text-center text-slate-500">
              No disclosures found.
            </div>
          )}
        </div>
      </section>
    );
  } catch {
    return <BackendUnavailable resource="disclosures" />;
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
