# Phase 5 — Scanner: SQLi, SSRF, IDOR detectors

## Goal

Extend the scanner with the remaining three vuln classes.

## Deliverables

- `scanner/detectors/sqli.py` — shell out to `sqlmap` in scan mode against
  discovered params, parse its output into the findings schema. Don't
  reimplement SQLi detection from scratch.
- `scanner/detectors/ssrf.py` — test discovered params that accept
  URLs/hostnames by pointing them at a controlled callback (e.g. a local
  listener in the fixture/test setup) and checking for a hit.
- `scanner/detectors/idor.py` — this one is genuinely custom: with two
  authenticated sessions (different roles/users) available in scope config,
  diff responses to the same resource ID across sessions to detect
  authorization bypass.
- Wire all three into `scanner/engine.py` alongside the existing XSS
  detector.
- Extend the fixture app (`scanner/tests/fixtures/`) with intentionally
  vulnerable endpoints for each class, and add pytest coverage per detector.

## Out of scope for this phase

- Any vuln class beyond these four for now (see project doubts doc / your
  own notes on what's next — CSRF, open redirect, security misconfig, etc.
  are good v1.5 candidates once this phase is solid)

## Done when

- Running a full scan against the fixture app produces findings across all
  four vuln classes
- Each detector has fixture-based test coverage, not just XSS
