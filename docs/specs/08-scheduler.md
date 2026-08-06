# Phase 8 — Scheduler

## Goal

Wire up recurring scans so Cortex actually runs continuously against
in-scope programs, rather than only being triggered manually.

## Deliverables

- `scanner/scheduler.py` — APScheduler (or similar) job that, per program,
  triggers `POST /scan` on a configured interval.
- Schedule config lives on the `programs` table (e.g. `scan_interval_hours`)
  — extend the backend model/router from Phase 1.
- After a scheduled scan completes, automatically trigger triage
  (Phase 4/6 endpoints) on any new findings — this is the one place
  automatic chaining is appropriate, since the human review gate in the
  dashboard still sits between triage and any submission.
- Basic logging/alerting on scan failures (just log to stdout/file is fine
  for a student project — no need for a full alerting stack).

## Done when

- A program with a configured interval gets scanned automatically without
  manual triggering, and new findings show up triaged in the dashboard
  review queue without any manual API calls in between
