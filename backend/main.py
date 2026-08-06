"""Cortex Phase 1 FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import Base, engine
from backend.routers import disclosures, findings, programs, scans

# Import models before create_all so SQLAlchemy has every table registered.
from backend import models  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cortex API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(programs.router)
app.include_router(scans.router)
app.include_router(findings.router)
app.include_router(disclosures.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
