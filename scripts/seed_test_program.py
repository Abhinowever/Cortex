"""Seed script to register the known-vulnerable test fixture program in Cortex Backend."""

import os
import sys
import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

TEST_PROGRAM = {
    "name": "Vulnerable Test Target",
    "website_url": "http://127.0.0.1:5001",
    "in_scope_domains": ["127.0.0.1", "localhost"],
    "out_of_scope_domains": [],
    "scan_interval_hours": 24,
    "scope_notes": "Authorized local test target application exposing XSS, SQLi, SSRF, and IDOR test endpoints."
}


def register_test_program() -> dict:
    """Register fixture app test program with Cortex backend API."""
    with httpx.Client() as client:
        # Check existing programs
        resp = client.get(f"{BACKEND_URL}/programs")
        if resp.status_code == 200:
            existing = resp.json()
            for prog in existing:
                if prog.get("website_url") == TEST_PROGRAM["website_url"] or prog.get("name") == TEST_PROGRAM["name"]:
                    print(f"Test program already registered with ID {prog.get('id')}")
                    return prog

        # Register new program
        res = client.post(f"{BACKEND_URL}/programs", json=TEST_PROGRAM)
        if res.status_code in (200, 201):
            prog = res.json()
            print(f"Successfully registered test program: ID {prog.get('id')} ({prog.get('name')})")
            return prog
        else:
            print(f"Failed to register test program: HTTP {res.status_code} {res.text}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    register_test_program()
