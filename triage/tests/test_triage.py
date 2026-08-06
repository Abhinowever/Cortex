"""Pytest suite for triage service, LLMClient abstraction, PoC generation, report drafting, and triage endpoint flow."""

import pytest
import httpx
from fastapi.testclient import TestClient

from triage.llm_client import MockLLMClient, OpenAILLMClient, AnthropicLLMClient, get_llm_client, SeverityResult
from triage.classifier import SeverityClassifier
from triage.poc_generator import PocGenerator
from triage.report_writer import ReportWriter
from triage.main import app


@pytest.mark.asyncio
async def test_mock_llm_client_xss():
    client = MockLLMClient()
    finding = {
        "id": 10,
        "vuln_type": "XSS",
        "url": "http://test.local/search?q=test",
        "evidence": "Reflected XSS payload in response"
    }
    result = await client.classify_severity(finding)
    assert isinstance(result, SeverityResult)
    assert result.severity == "High"
    assert "Mock analysis" in result.justification


def test_provider_switching(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    client_mock = get_llm_client()
    assert isinstance(client_mock, MockLLMClient)

    monkeypatch.setenv("LLM_PROVIDER", "openai")
    client_openai = get_llm_client()
    assert isinstance(client_openai, OpenAILLMClient)

    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    client_anthropic = get_llm_client()
    assert isinstance(client_anthropic, AnthropicLLMClient)


@pytest.mark.asyncio
async def test_classifier_with_mock_client():
    classifier = SeverityClassifier(client=MockLLMClient())
    finding = {
        "id": 1,
        "vuln_type": "Reflected XSS",
        "url": "http://example.com/vuln",
        "evidence": "<script>alert(1)</script>"
    }
    result = await classifier.classify(finding)
    assert result.severity in ["Critical", "High", "Medium", "Low"]
    assert len(result.justification) > 0


@pytest.mark.asyncio
async def test_poc_generator():
    generator = PocGenerator(client=MockLLMClient())
    finding = {
        "id": 2,
        "vuln_type": "SQLi",
        "url": "http://example.com/sqli?id=1'",
        "evidence": "SQL syntax error near SQLite3"
    }
    steps = await generator.generate_steps(finding)
    assert len(steps) >= 2
    assert any("http://example.com/sqli" in step for step in steps)


@pytest.mark.asyncio
async def test_report_writer_sections():
    writer = ReportWriter(client=MockLLMClient())
    finding = {
        "id": 3,
        "vuln_type": "SSRF",
        "url": "http://example.com/ssrf?url=http://127.0.0.1",
        "evidence": "SSRF callback triggered"
    }
    poc_steps = ["1. Navigate to URL", "2. Observe callback hit"]
    report = await writer.draft(finding, poc_steps)

    # Required sections check per spec
    assert "## Summary" in report
    assert "## Impact" in report
    assert "## Steps to Reproduce" in report
    assert "## Suggested Fix" in report


@pytest.mark.asyncio
async def test_triage_endpoint_flow(monkeypatch):
    finding_db = {
        "id": 42,
        "vuln_type": "XSS",
        "url": "http://fixture.local/search?q=test",
        "evidence": "Payload reflected",
        "severity": None,
        "report_draft": None,
        "status": "new"
    }

    patched_payloads = []

    async def mock_get(self, url, **kwargs):
        class MockGetResp:
            status_code = 200
            def json(self):
                if url.endswith("/findings"):
                    return [finding_db]
                return finding_db
            @property
            def text(self):
                return "OK"
        return MockGetResp()


    async def mock_patch(self, url, json=None, **kwargs):
        patched_payloads.append(json)
        class MockPatchResp:
            status_code = 200
            def json(self):
                updated = finding_db.copy()
                updated.update(json or {})
                return updated
            @property
            def text(self):
                return "OK"
        return MockPatchResp()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    monkeypatch.setattr(httpx.AsyncClient, "patch", mock_patch)
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    test_client = TestClient(app)
    response = test_client.post("/triage/42")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["finding_id"] == 42
    assert data["severity"] == "High"
    assert len(data["poc_steps"]) > 0
    assert "## Summary" in data["report_draft"]
    assert "## Impact" in data["report_draft"]
    assert "## Steps to Reproduce" in data["report_draft"]
    assert "## Suggested Fix" in data["report_draft"]
    assert data["updated_finding"]["status"] == "triaged"
    assert len(patched_payloads) == 1
    assert "poc_steps" in patched_payloads[0]
    assert "report_draft" in patched_payloads[0]
