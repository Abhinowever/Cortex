# Cortex dashboard

Read-only Next.js shell for reviewing data from the Cortex backend.

```bash
cp .env.local.example .env.local
npm install
npm run dev
```

Start and seed the backend first (`docker compose up -d` then `docker compose
exec backend python -m backend.seed`). The dashboard is available at
`http://localhost:3000/findings`.
