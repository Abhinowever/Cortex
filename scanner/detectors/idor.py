"""IDOR detector module for Cortex scanner.

Detects Insecure Direct Object References by diffing response content across different session contexts/roles.
"""

from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs
import logging
import re
import httpx

logger = logging.getLogger(__name__)


@dataclass
class IDORFinding:
    vuln_type: str
    url: str
    evidence: str
    fingerprint_hash: str


class IDORDetector:
    def __init__(self, allowed_domains: list[str], secondary_headers: dict[str, str] | None = None):
        self.allowed_domains = allowed_domains
        self.secondary_headers = secondary_headers or {"X-User-Token": "user2_token"}

    async def scan_url(self, target_url: str, primary_headers: dict[str, str] | None = None) -> list[IDORFinding]:
        findings = []
        parsed = urlparse(target_url)

        # Look for numeric resource IDs in path (e.g. /user/123, /document/45)
        path_segments = [s for s in parsed.path.split("/") if s]
        has_id_in_path = any(s.isdigit() for s in path_segments)
        params = parse_qs(parsed.query)
        has_id_in_query = any("id" in k.lower() for k in params.keys())

        if not (has_id_in_path or has_id_in_query):
            return findings

        p_headers = primary_headers or {"X-User-Token": "user1_token"}

        async with httpx.AsyncClient(timeout=5.0) as http_client:
            try:
                # 1. Fetch resource with User 1 session
                res_user1 = await http_client.get(target_url, headers=p_headers)
                
                # 2. Fetch resource with User 2 session
                res_user2 = await http_client.get(target_url, headers=self.secondary_headers)

                # Flag IDOR if User 2 accesses private data of User 1 without 401/403 authorization error
                if res_user1.status_code == 200 and res_user2.status_code == 200:
                    if "private_data" in res_user2.text or res_user1.text == res_user2.text:
                        findings.append(IDORFinding(
                            vuln_type="IDOR",
                            url=target_url,
                            evidence=f"Resource accessible by secondary unprivileged session without authorization checks (HTTP {res_user2.status_code})",
                            fingerprint_hash=f"idor:{parsed.netloc}{parsed.path}"
                        ))
            except Exception as e:
                logger.debug("IDOR check failed: %s", e)

        return findings
