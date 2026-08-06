# Cortex — agent instructions

Read this file before starting any task in this repo.

## What this project is

Cortex is an autonomous agent for continuous website vulnerability detection,
structured reporting, and responsible disclosure, built for recurring bug
bounty programs. It scans in-scope targets, detects common web
vulnerabilities, uses an LLM to triage and write up findings, and surfaces
everything in a review dashboard. A human always approves before anything is
submitted to a program — nothing in this system auto-submits.

## Architecture

Four services, one repo (monorepo for now):

- `scanner/` — Python + Playwright. Crawls a target and runs detection
  modules (XSS, SQLi, IDOR, SSRF to start). Emits raw findings.
- `triage/` — Python. Calls an LLM to classify severity, dedupe near-matches,
  generate PoC steps, and draft disclosure reports from raw findings.
- `backend/` — FastAPI + Postgres. Source of truth: programs, scans,
  findings, disclosures. Everything else reads/writes through this API.
- `dashboard/` — Next.js. Review queue, CVE tagging, disclosure timeline.

Full data flow and data model: see `docs/specs/00-overview.md`.

## Working conventions

- **Scope discipline is non-negotiable.** The scanner must never send a
  request to a target that hasn't been explicitly validated against a
  program's defined scope. If you're implementing anything in `scanner/`,
  the scope check runs *before* any request goes out, not after.
- **The LLM's job is classification and writing, not discovery.** `triage/`
  turns findings the scanner already produced into severity ratings, PoC
  steps, and report drafts. It does not generate new attack payloads or
  probe targets itself.
- **LLM provider is not hardcoded.** `triage/llm_client.py` defines an
  abstract `LLMClient` interface; concrete providers (Anthropic, OpenAI,
  etc.) implement it. Which provider is active is a config value
  (`LLM_PROVIDER` env var), never imported directly by pipeline logic.
- **Python:** FastAPI for services, Pydantic for schemas, SQLAlchemy for the
  DB layer, pytest for tests. Type hints throughout.
- **One phase at a time.** This repo is being built in the phases listed in
  `docs/specs/`. Only work within the current phase's spec unless told
  otherwise — don't reach ahead into later phases' functionality.
- **Every phase ships with a test.** At minimum one pytest (backend/scanner/
  triage) or a basic render check (dashboard) per feature added.
- **Commit at the end of each working phase**, not mid-phase.

## Current phase

Check `docs/specs/` for the numbered spec files. Work through them in order
(00 is the overview/reference, 01+ are build phases). If asked to "start
Phase N," open `docs/specs/0N-*.md` and implement only what's described
there.

## Do not

- Do not run the scanner against any target that isn't explicitly configured
  as an authorized test target in local dev/test fixtures.
- Do not add auto-submission of disclosures — the human review gate in the
  dashboard is a permanent design requirement, not a placeholder.
- Do not hardcode API keys or secrets anywhere in the repo. Use `.env`
  (gitignored) and `.env.example` as the template.
