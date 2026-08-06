"""SSRF detector module for Cortex scanner.

Detects Server-Side Request Forgery by testing URL/hostname parameters with callback probes.
"""

from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging
import httpx

logger = logging.getLogger(__name__)

SSRF_PARAM_NAMES = ["url", "dest", "target", "uri", "path", "redirect", "feed", "host"]
SSRF_PROBE_TARGETS = [
    "http://127.0.0.1:8899/ssrf-callback",
    "http://169.254.169.254/latest/meta-data/"
]


@dataclass
class SSRFFinding:
    vuln_type: str
    url: str
    evidence: str
    fingerprint_hash: str


class SSRFDetector:
    def __init__(self, allowed_domains: list[str]):
        self.allowed_domains = allowed_domains

    async def scan_url(self, target_url: str) -> list[SSRFFinding]:
        findings = []
        parsed = urlparse(target_url)
        params = parse_qs(parsed.query)

        if not params:
            return findings

        async with httpx.AsyncClient(timeout=5.0) as http_client:
            for param_name in params.keys():
                # Test params matching typical URL destination names or any parameter
                if param_name.lower() in SSRF_PARAM_NAMES or len(params) == 1:
                    for probe in SSRF_PROBE_TARGETS:
                        mutated_params = params.copy()
                        mutated_params[param_name] = [probe]
                        new_query = urlencode(mutated_params, doseq=True)
                        test_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

                        try:
                            res = await http_client.get(test_url)
                            # Check if callback reached or metadata reflected/triggered
                            if "ssrf_callback_hit" in res.text or "instance-id" in res.text.lower() or res.status_code == 200 and "fetched_content" in res.text:
                                findings.append(SSRFFinding(
                                    vuln_type="SSRF",
                                    url=test_url,
                                    evidence=f"SSRF probe payload triggered internal/callback fetch for parameter '{param_name}'",
                                    fingerprint_hash=f"ssrf:{parsed.netloc}{parsed.path}:{param_name}"
                                ))
                                break
                        except Exception as e:
                            logger.debug("SSRF check skipped/failed: %s", e)

        return findings
