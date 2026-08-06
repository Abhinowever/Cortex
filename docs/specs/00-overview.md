# 00 — Overview & reference

This file is reference material, not a build phase. Point an agent here for
context on the whole system; point it to a numbered phase file for actual
work.

## Data flow

1. Target URL submitted (manually, or by scheduler) → validated against the
   program's defined scope.
2. Scanner crawls the target (Playwright) and runs detection modules
   (XSS, SQLi, IDOR, SSRF).
3. Raw findings are deduplicated against finding history (fingerprint hash
   first pass, LLM semantic pass for near-duplicates).
4. Triage pipeline classifies severity, generates PoC steps, drafts a
   disclosure report.
5. Everything lands in the dashboard review queue.
6. A human reviews and manually submits to the program. Disclosure timeline
   starts from that point.

## Data model (core tables)

- **programs** — bug bounty program metadata, in/out-of-scope domains, rules
- **scans** — run history: target, timestamp, status
- **findings** — vuln_type, url, evidence, severity, fingerprint_hash,
  status (new / triaged / reported / duplicate)
- **poc_steps** — linked to a finding, ordered reproduction steps
- **disclosures** — finding_id, submission status, program deadline,
  cve_id (nullable), timeline events

## Repo layout

```
cortex/
├── AGENTS.md
├── docs/specs/           # this folder
├── scanner/               # Phase 3, 5
├── triage/                # Phase 4, 6, 7 (partial)
├── backend/               # Phase 1
├── dashboard/             # Phase 2, 7 (partial)
└── shared/                # Pydantic schemas shared across services
```

## Build order

| Phase | File | What it delivers |
|---|---|---|
| 1 | `01-backend.md` | DB schema + CRUD API, seeded with fake data |
| 2 | `02-dashboard-shell.md` | Next.js app reading real data from backend |
| 3 | `03-scanner-xss.md` | Playwright crawler + XSS detector only |
| 4 | `04-triage-severity.md` | Severity classification on real findings |
| 5 | `05-scanner-remaining.md` | Add SQLi, SSRF, IDOR detectors |
| 6 | `06-poc-report.md` | PoC generation + report drafting |
| 7 | `07-dedup-cve-timeline.md` | Dedup logic, CVE tagging, disclosure timeline UI |
| 8 | `08-scheduler.md` | Recurring scans |
