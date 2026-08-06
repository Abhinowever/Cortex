# Phase 1 — Backend + DB schema

## Goal

A working FastAPI backend with the core data model, CRUD endpoints, and
seed data. No scanner or triage integration yet — just prove the data model
is right and the API is usable.

## Deliverables

- `backend/models.py` — SQLAlchemy models for `programs`, `scans`,
  `findings`, `poc_steps`, `disclosures` (see `00-overview.md` for fields)
- `backend/routers/programs.py` — CRUD for programs
- `backend/routers/findings.py` — CRUD for findings, filterable by
  `status` and `vuln_type`
- `backend/routers/disclosures.py` — CRUD for disclosures
- `backend/main.py` — FastAPI app wiring routers together
- `backend/seed.py` — script that inserts a handful of fake programs and
  findings for local dev/demo purposes
- `docker-compose.yml` entry for Postgres (add to the root compose file)
- One pytest per endpoint (happy path at minimum)

## Out of scope for this phase

- Auth (add later)
- Any connection to the scanner or triage services
- Dashboard

## Done when

- `docker compose up` brings up Postgres + backend
- `python backend/seed.py` populates fake data
- `pytest backend/` passes
- You can hit `GET /findings` and get seeded data back
