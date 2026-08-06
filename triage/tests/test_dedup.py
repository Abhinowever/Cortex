"""Pytest suite for Phase 7 deduplication engine, CVE tagging, and disclosure timeline."""

import pytest
import httpx
from fastapi.testclient import TestClient

from triage.dedup import Deduplicator, compute_fingerprint_hash, normalize_url, extract_parameter_name
from triage.llm_client import MockLLMClient


def test_url_normalization():
    assert normalize_url("HTTP://EXAMPLE.COM/test/?q=1#ref") == "http://example.com/test"
    assert normalize_url("https://target.local/api/v1/user/") == "https://target.local/api/v1/user"


def test_parameter_extraction():
    finding_1 = {"evidence": "Reflected payload in param=search"}
    assert extract_parameter_name(finding_1) == "search"

    finding_2 = {"url": "http://example.com/item?b=2&a=1"}
    assert extract_parameter_name(finding_2) == "a,b"


@pytest.mark.asyncio
async def test_pass_1_hash_deduplication():
    dedup = Deduplicator(client=MockLLMClient())
    finding_1 = {
        "id": 1,
        "vuln_type": "XSS",
        "url": "http://example.com/search?q=test1",
        "evidence": "param=q reflected"
    }
    finding_2 = {
        "id": 2,
        "vuln_type": "XSS",
        "url": "http://EXAMPLE.COM/search/?q=test2",
        "evidence": "param=q reflected"
    }

    is_dup, orig_id = await dedup.deduplicate(finding_2, [finding_1])
    assert is_dup is True
    assert orig_id == 1


@pytest.mark.asyncio
async def test_pass_2_llm_near_duplicate():
    dedup = Deduplicator(client=MockLLMClient())
    finding_1 = {
        "id": 10,
        "vuln_type": "SQLi",
        "url": "http://target.local/api/users?sort=asc",
        "evidence": "SQL syntax error"
    }
    finding_2 = {
        "id": 11,
        "vuln_type": "SQLi",
        "url": "http://target.local/api/users?page=2",
        "evidence": "SQL syntax error"
    }

    # Pass 1 hash differs because query param names differ, but MockLLMClient pass 2 matches base URL
    is_dup, orig_id = await dedup.deduplicate(finding_2, [finding_1])
    assert is_dup is True
    assert orig_id == 10


@pytest.mark.asyncio
async def test_non_duplicate_findings():
    dedup = Deduplicator(client=MockLLMClient())
    finding_1 = {
        "id": 1,
        "vuln_type": "XSS",
        "url": "http://example.com/search",
        "evidence": "XSS reflected"
    }
    finding_2 = {
        "id": 2,
        "vuln_type": "SQLi",
        "url": "http://example.com/login",
        "evidence": "SQL error"
    }

    is_dup, orig_id = await dedup.deduplicate(finding_2, [finding_1])
    assert is_dup is False
    assert orig_id is None
