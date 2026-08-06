import Link from "next/link";
import { getPrograms } from "../../lib/api";

export default async function ProgramsPage() {
  try {
    const programs = await getPrograms();

    return (
      <section>
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Programs</h1>
            <p className="mt-1 text-sm text-slate-600">Authorized programs and their defined testing scope.</p>
          </div>
          <Link
            href="/programs/new"
            className="rounded-md bg-sky-700 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-600"
          >
            + Add Program
          </Link>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {programs.map((program) => (
            <article key={program.id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">{program.name}</h2>
              {program.website_url && <a className="mt-1 block text-sm text-sky-700 hover:underline" href={program.website_url}>{program.website_url}</a>}
              <h3 className="mt-5 text-xs font-semibold uppercase tracking-wide text-slate-500">In scope</h3>
              {program.in_scope_domains.length ? (
                <ul className="mt-2 space-y-1 text-sm text-slate-700">
                  {program.in_scope_domains.map((domain) => <li key={domain}>{domain}</li>)}
                </ul>
              ) : <p className="mt-2 text-sm text-slate-500">No domains defined.</p>}
              {program.rules && <p className="mt-5 border-t border-slate-100 pt-4 text-sm text-slate-600">{program.rules}</p>}
            </article>
          ))}
          {programs.length === 0 && <p className="text-sm text-slate-500">No programs yet.</p>}
        </div>
      </section>
    );
  } catch {
    return (
      <section className="rounded-lg border border-amber-200 bg-amber-50 p-5">
        <h1 className="text-lg font-semibold text-amber-950">Unable to load programs</h1>
        <p className="mt-1 text-sm text-amber-900">Start the backend and set NEXT_PUBLIC_API_URL if it is not running at http://localhost:8000.</p>
      </section>
    );
  }
}
