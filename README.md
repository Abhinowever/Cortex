# Cortex

Autonomous agent for continuous website vulnerability detection, structured
reporting, and responsible disclosure — built for recurring bug bounty
programs.

- Automated end-to-end scanning (XSS, SQLi, IDOR, SSRF) via headless browser
  automation
- LLM-driven triage: severity classification, PoC generation, structured
  disclosure report drafts
- Tracking dashboard with dedup, CVE tagging, and disclosure-timeline
  management
- A human always reviews before anything is submitted to a program

## Status

Early build. See `docs/specs/` for the phased build plan — start at
`00-overview.md`, then work through `01-backend.md` onward.

## Getting started

```bash
cp .env.example .env      # fill in your values
docker compose up -d       # brings up Postgres (more services added per phase)
```

Each service (`scanner/`, `triage/`, `backend/`, `dashboard/`) gets its own
setup instructions as it's built out — see the corresponding phase spec.

## Repo guide for coding agents

If you're Codex, Antigravity, or another agent working in this repo, read
`AGENTS.md` first — it has architecture, conventions, and the current
build phase.

## Authorized use only

Cortex is built to scan targets you are explicitly authorized to test —
your own systems, or in-scope bug bounty programs. Scope validation is a
hard requirement in the scanner (see `AGENTS.md`), not optional
configuration.
