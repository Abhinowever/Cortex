"""Seed local development data. Run with: python backend/seed.py."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.database import Base, SessionLocal, engine
from backend.models import Finding, Program


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Program).first() is not None:
            print("Database already contains programs; skipping seed.")
            return

        acme = Program(
            name="Acme Security Program",
            website_url="https://acme.example",
            in_scope_domains=["app.acme.example", "api.acme.example"],
            out_of_scope_domains=["status.acme.example"],
            rules="Use test accounts only. Do not impact availability.",
        )
        demo = Program(
            name="Demo Marketplace",
            website_url="https://market.example",
            in_scope_domains=["market.example"],
            rules="Production testing is permitted within the stated scope.",
        )
        db.add_all([acme, demo])
        db.flush()
        db.add_all(
            [
                Finding(
                    vuln_type="xss",
                    url="https://app.acme.example/search?q=test",
                    evidence="Reflected marker observed in the search response.",
                    severity="medium",
                    fingerprint_hash="demo-acme-xss-001",
                    status="new",
                ),
                Finding(
                    vuln_type="idor",
                    url="https://market.example/api/orders/1001",
                    evidence="A test account could access another test order.",
                    severity="high",
                    fingerprint_hash="demo-market-idor-001",
                    status="triaged",
                ),
            ]
        )
        db.commit()
        print("Seeded 2 programs and 2 findings.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
