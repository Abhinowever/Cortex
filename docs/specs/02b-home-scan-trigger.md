# 02b — Home page + scan trigger (backend fix + new page)

This is a small addendum, not a full phase — it closes the gap between the
dashboard shell (Phase 2) and the scanner engine (Phase 3) by adding the
entry point: a home page where a scan gets kicked off.

## Part A — backend fix: add the missing `scans` router

Phase 1's spec omitted this even though `scans` is in the data model
(`00-overview.md`). Add it now.

- `backend/routers/scans.py`:
  - `POST /scans` — body: `{ program_id, target_url }`. Validates
    `target_url` falls within the program's `in_scope` domains (reject with
    a clear error if not — this is the scope check surfaced to the UI, not
    just the scanner's internal one). Creates a `scans` row with
    `status = pending`. Returns the created scan.
  - `GET /scans` — list scans, filterable by `program_id` and `status`.
  - `GET /scans/{id}` — single scan detail (status, target, timestamps).
- Wire the router into `backend/main.py`.
- pytest: one test for a valid in-scope submission, one for an
  out-of-scope rejection.

## Part B — home page

- `dashboard/app/page.tsx` (the actual home route — `/`) becomes the scan
  trigger, not a redirect to `/findings`.
- Form: a program selector (dropdown, populated from `GET /programs`) and
  a target URL text input. On submit:
  1. `POST /scans` on the backend (records intent, enforces scope
     server-side per Part A).
  2. If that succeeds, call the scanner service's `POST /scan` (from
     `03-scanner-xss.md`) with the same `program_id` / `target_url`. Until
     Phase 3 exists, this call will fail — that's expected; catch it and
     show "Scanner not available yet" rather than a raw error.
- Show a simple list of recent scans below the form (`GET /scans`), each
  linking through to its findings once there are any.
- Add "Home" to the nav, before Findings.

## Done when

- Submitting an out-of-scope URL is rejected with a clear message, before
  anything is queued
- Submitting an in-scope URL creates a visible `scans` row, and the UI
  degrades gracefully (clear "not available yet" state) since the scanner
  isn't built yet
- Once Phase 3 lands, this page needs no changes — it already calls the
  right endpoint