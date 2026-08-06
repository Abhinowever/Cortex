# Phase 2 — Dashboard shell

## Goal

A Next.js app that reads real data from the Phase 1 backend and displays it.
Validates the data model visually before any scanning logic exists.

## Deliverables

- `dashboard/app/findings/page.tsx` — table of findings (vuln_type, url,
  severity, status), pulling from `GET /findings` on the backend
- `dashboard/app/programs/page.tsx` — list of programs
- Basic nav between the two pages
- `.env.local.example` with `NEXT_PUBLIC_API_URL`
- Tailwind for styling — keep it plain, this is a functional shell, not a
  polished UI yet

## Out of scope for this phase

- Editing/creating records from the UI (read-only for now)
- CVE tagging, disclosure timeline UI (Phase 7)
- Auth

## Done when

- `npm run dev` in `dashboard/` shows real seeded findings from the backend
  in a table
- Switching between findings and programs pages works
