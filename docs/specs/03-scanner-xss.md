# Phase 3 — Scanner engine v1 (XSS only)

## Goal

A Playwright-based crawler that walks a target and detects reflected/DOM
XSS, writing findings into the backend via its API. This is the phase that
proves the scanner → backend pipeline end to end, for one vuln class.

## Deliverables

- `scanner/crawler.py` — Playwright-based site walker. Takes a base URL and
  a scope config (allowed domains/paths), returns a list of visited pages
  and their forms/params.
- `scanner/detectors/xss.py` — injects test markers into discovered
  params/forms, uses Playwright to observe whether they land unescaped in
  the DOM (reflected) or trigger in a script sink (DOM-based).
- `scanner/engine.py` — orchestrates: validate scope → crawl → run XSS
  detector → POST findings to backend.
- `scanner/main.py` — FastAPI entrypoint exposing `POST /scan` (target url,
  program_id) that kicks off the above synchronously for now (no queue yet).
- **Scope validation must run before the crawler makes any request.**
  Reject and log if the target isn't within the program's configured scope.
- pytest against a local fixture app (a tiny intentionally-vulnerable
  Flask/Express app in `scanner/tests/fixtures/`) — do not test against any
  live external site.

## Out of scope for this phase

- SQLi, IDOR, SSRF (Phase 5)
- Triage/severity classification (Phase 4 consumes these findings, but this
  phase just writes raw findings to the backend)
- Scheduling (Phase 8)

## Done when

- `POST /scan` against the local fixture app produces at least one XSS
  finding, visible via `GET /findings` on the backend
- Scope validation demonstrably blocks a URL outside the configured domain
