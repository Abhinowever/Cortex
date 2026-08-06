"""Pytest test suite for scanner engine, scope validation, and XSS/SQLi/SSRF/IDOR detectors."""

import pytest
import uvicorn
import time
import httpx
import threading

from scanner.scope import is_in_scope
from scanner.engine import ScanEngine
from scanner.detectors.sqli import SQLiDetector
from scanner.detectors.ssrf import SSRFDetector
from scanner.detectors.idor import IDORDetector
from scanner.tests.fixtures.app import fixture_app


def run_fixture_server(server):
    server.run()


@pytest.fixture(scope="module")
def fixture_server():
    config = uvicorn.Config(fixture_app, host="127.0.0.1", port=8899, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=run_fixture_server, args=(server,), daemon=True)
    thread.start()
    time.sleep(1.0)
    yield "http://127.0.0.1:8899"
    server.should_exit = True


def test_scope_validation():
    allowed = ["example.com", "test.local"]
    disallowed = ["out.example.com"]

    assert is_in_scope("http://example.com/page", allowed) is True
    assert is_in_scope("http://sub.example.com/page", allowed) is True
    assert is_in_scope("http://malicious.com/page", allowed) is False
    assert is_in_scope("http://out.example.com/page", allowed, disallowed) is False
    assert is_in_scope("", allowed) is False


@pytest.mark.asyncio
async def test_sqli_detector(fixture_server):
    detector = SQLiDetector(allowed_domains=["127.0.0.1"])
    findings = await detector.scan_url(f"{fixture_server}/sqli?id=1")
    assert len(findings) > 0
    assert findings[0].vuln_type == "SQLi"
    assert "sql syntax" in findings[0].evidence.lower() or "sqlite3" in findings[0].evidence.lower()


@pytest.mark.asyncio
async def test_ssrf_detector(fixture_server):
    detector = SSRFDetector(allowed_domains=["127.0.0.1"])
    findings = await detector.scan_url(f"{fixture_server}/ssrf?url=http://example.com")
    assert len(findings) > 0
    assert findings[0].vuln_type == "SSRF"
    assert "ssrf_callback_hit" in findings[0].evidence or "callback" in findings[0].evidence


@pytest.mark.asyncio
async def test_idor_detector(fixture_server):
    detector = IDORDetector(allowed_domains=["127.0.0.1"])
    findings = await detector.scan_url(f"{fixture_server}/idor/user/101")
    assert len(findings) > 0
    assert findings[0].vuln_type == "IDOR"


@pytest.mark.asyncio
async def test_scan_vulnerable_fixture_app(fixture_server, monkeypatch):
    target_url = f"{fixture_server}/search?q=test"
    allowed_domains = ["127.0.0.1"]

    # Mock backend reporting so we test scanner flow independently
    posted_payloads = []

    async def mock_post(self, url, json=None, **kwargs):
        class MockResponse:
            status_code = 201
            def json(self):
                return {"id": 1, **(json or {})}
            @property
            def text(self):
                return "OK"

        posted_payloads.append(json)
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    engine = ScanEngine(backend_url="http://localhost:8000")
    findings = await engine.run_scan(
        target_url=target_url,
        program_id=1,
        in_scope_domains=allowed_domains
    )

    assert len(findings) > 0
    assert any(f["vuln_type"] == "XSS" for f in findings)
    assert len(posted_payloads) > 0


@pytest.mark.asyncio
async def test_out_of_scope_scan_rejected():
    engine = ScanEngine(backend_url="http://localhost:8000")
    with pytest.raises(ValueError, match="out of scope"):
        await engine.run_scan(
            target_url="http://unauthorized-domain.com/path",
            program_id=1,
            in_scope_domains=["authorized.com"]
        )


@pytest.mark.asyncio
async def test_scan_chains_auto_triage(fixture_server, monkeypatch):
    target_url = f"{fixture_server}/search?q=test"
    allowed_domains = ["127.0.0.1"]
    triage_calls = []

    async def mock_post(self, url, json=None, **kwargs):
        class MockResponse:
            status_code = 201
            def json(self):
                return {"id": 99, "vuln_type": "XSS", "url": target_url}
            @property
            def text(self):
                return "OK"

        if "/triage/" in str(url):
            triage_calls.append(str(url))
            return MockResponse()

        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    engine = ScanEngine(backend_url="http://localhost:8000", triage_url="http://localhost:8001")
    findings = await engine.run_scan(
        target_url=target_url,
        program_id=1,
        in_scope_domains=allowed_domains
    )

    assert len(findings) > 0
    assert len(triage_calls) > 0
    assert any("/triage/99" in url for url in triage_calls)

