import asyncio
from collections.abc import AsyncGenerator, Generator

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app


class ApiClient:
    """Small synchronous facade over HTTPX's in-process ASGI transport."""

    def request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        async def send() -> httpx.Response:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                return await client.request(method, url, **kwargs)

        return asyncio.run(send())

    def get(self, url: str, **kwargs: object) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: object) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def patch(self, url: str, **kwargs: object) -> httpx.Response:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: object) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)


@pytest.fixture()
def client() -> Generator[ApiClient, None, None]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    async def override_db() -> AsyncGenerator[Session, None]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    try:
        yield ApiClient()
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def create_finding(client: ApiClient, suffix: str = "1") -> int:
    response = client.post(
        "/findings",
        json={
            "vuln_type": "xss",
            "url": f"https://example.test/search?q={suffix}",
            "evidence": "A safe test marker was reflected.",
            "severity": "medium",
            "fingerprint_hash": f"test-{suffix}",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_program_crud(client: ApiClient) -> None:
    created = client.post(
        "/programs",
        json={"name": "Example Program", "in_scope_domains": ["example.test"]},
    )
    assert created.status_code == 201
    program_id = created.json()["id"]
    assert client.get("/programs").json()[0]["name"] == "Example Program"
    assert client.get(f"/programs/{program_id}").status_code == 200
    assert client.patch(f"/programs/{program_id}", json={"rules": "Test safely."}).status_code == 200
    assert client.delete(f"/programs/{program_id}").status_code == 204


def test_findings_crud_and_filters(client: ApiClient) -> None:
    finding_id = create_finding(client, "xss")
    create_finding(client, "second")
    filtered = client.get("/findings", params={"status": "new", "vuln_type": "xss"})
    assert filtered.status_code == 200
    assert len(filtered.json()) == 2
    assert client.get(f"/findings/{finding_id}").status_code == 200
    updated = client.patch(f"/findings/{finding_id}", json={"status": "triaged"})
    assert updated.json()["status"] == "triaged"
    assert client.delete(f"/findings/{finding_id}").status_code == 204


def test_disclosure_crud(client: ApiClient) -> None:
    finding_id = create_finding(client)
    created = client.post(
        "/disclosures",
        json={"finding_id": finding_id, "timeline_events": [{"event": "drafted"}]},
    )
    assert created.status_code == 201
    disclosure_id = created.json()["id"]
    assert len(client.get("/disclosures").json()) == 1
    assert client.get(f"/disclosures/{disclosure_id}").status_code == 200
    updated = client.patch(f"/disclosures/{disclosure_id}", json={"cve_id": "CVE-2026-1234"})
    assert updated.json()["cve_id"] == "CVE-2026-1234"
    assert client.delete(f"/disclosures/{disclosure_id}").status_code == 204


def test_scans_in_scope_submission(client: ApiClient) -> None:
    prog = client.post(
        "/programs",
        json={"name": "Scan Test Program", "in_scope_domains": ["target.local"]},
    ).json()

    # Valid in-scope target submission
    scan_resp = client.post(
        "/scans",
        json={"program_id": prog["id"], "target_url": "http://target.local/page"},
    )
    assert scan_resp.status_code == 201
    scan_data = scan_resp.json()
    assert scan_data["status"] == "pending"
    assert scan_data["target_url"] == "http://target.local/page"

    # List scans
    scans_list = client.get("/scans", params={"program_id": prog["id"]}).json()
    assert len(scans_list) == 1
    assert scans_list[0]["id"] == scan_data["id"]

    # Get single scan
    get_resp = client.get(f"/scans/{scan_data['id']}")
    assert get_resp.status_code == 200


def test_scans_out_of_scope_rejection(client: ApiClient) -> None:
    prog = client.post(
        "/programs",
        json={
            "name": "Scope Test Program",
            "in_scope_domains": ["authorized.local"],
            "out_of_scope_domains": ["forbidden.local"]
        },
    ).json()

    # Out of scope target submission
    scan_resp = client.post(
        "/scans",
        json={"program_id": prog["id"], "target_url": "http://unauthorized.com/page"},
    )
    assert scan_resp.status_code == 400
    assert "out of scope" in scan_resp.json()["detail"].lower()


def test_cors_headers(client: ApiClient) -> None:
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"

