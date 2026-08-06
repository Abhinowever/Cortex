# backend

FastAPI + Postgres. Source of truth for programs, scans, findings, and disclosures.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
docker compose up -d postgres
DATABASE_URL=postgresql://cortex:cortex@localhost:5432/cortex .venv/bin/python -m backend.seed
DATABASE_URL=postgresql://cortex:cortex@localhost:5432/cortex .venv/bin/uvicorn backend.main:app --reload
```

Or run the complete stack with `docker compose up --build`. Seed demo data with
`docker compose exec backend python -m backend.seed`.

Run tests with `.venv/bin/pytest backend/tests`.
