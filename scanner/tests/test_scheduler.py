"""Pytest suite for ScanScheduler and recurring scan auto-triage chaining."""

import pytest
import httpx

from scanner.scheduler import ScanScheduler


@pytest.mark.asyncio
async def test_scheduler_run_program_scan(monkeypatch):
    scheduler = ScanScheduler(backend_url="http://localhost:8000", triage_url="http://localhost:8001")

    # Mock ScanEngine.run_scan to return simulated findings
    async def mock_run_scan(self, target_url, program_id, in_scope_domains=None, out_of_scope_domains=None):
        return [
            {"id": 101, "vuln_type": "XSS", "url": "http://127.0.0.1:8899/search?q=1", "evidence": "xss evidence"},
            {"id": 102, "vuln_type": "SQLi", "url": "http://127.0.0.1:8899/sqli?id=1", "evidence": "sqli evidence"}
        ]

    from scanner.engine import ScanEngine
    monkeypatch.setattr(ScanEngine, "run_scan", mock_run_scan)

    # Track auto-triage triggers
    triaged_finding_ids = []

    async def mock_post(self, url, **kwargs):
        class MockResponse:
            status_code = 200
            text = "OK"
            def json(self):
                return {"status": "ok"}

        if "/triage/" in url:
            finding_id = int(url.split("/triage/")[1])
            triaged_finding_ids.append(finding_id)
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    program = {
        "id": 1,
        "name": "Test Program",
        "website_url": "http://127.0.0.1:8899",
        "in_scope_domains": ["127.0.0.1"],
        "out_of_scope_domains": [],
        "scan_interval_hours": 12
    }

    result = await scheduler.run_scan_for_program(program)

    assert result["status"] == "completed"
    assert result["findings_count"] == 2
    assert result["triaged_count"] == 2
    assert triaged_finding_ids == [101, 102]


@pytest.mark.asyncio
async def test_scheduler_skips_program_without_url():
    scheduler = ScanScheduler()
    program = {"id": 2, "name": "Empty Program", "website_url": None}

    result = await scheduler.run_scan_for_program(program)
    assert result["status"] == "skipped"
    assert result["reason"] == "No website_url"
