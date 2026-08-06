"""SQLi detector module for Cortex scanner.

Detects SQL injection vulnerabilities via error-based reflection and sqlmap execution.
"""

from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging
import subprocess
import shutil
import httpx

logger = logging.getLogger(__name__)

SQL_ERRORS = [
    "you have an error in your sql syntax",
    "unclosed quotation mark after the character string",
    "sqlite3.operationalerror",
    "pg::syntaxerror",
    "warning: mysql_",
    "valid sqlite result",
    "quoted string not properly terminated"
]

SQLI_PAYLOADS = ["'", "1' OR '1'='1", "1' --", "' OR 1=1--"]


@dataclass
class SQLiFinding:
    vuln_type: str
    url: str
    evidence: str
    fingerprint_hash: str


class SQLiDetector:
    def __init__(self, allowed_domains: list[str]):
        self.allowed_domains = allowed_domains

    async def scan_url(self, target_url: str) -> list[SQLiFinding]:
        findings = []
        parsed = urlparse(target_url)
        params = parse_qs(parsed.query)

        if not params:
            return findings

        # 1. Quick HTTP Error-based detection
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            for param_name in params.keys():
                for payload in SQLI_PAYLOADS:
                    mutated_params = params.copy()
                    mutated_params[param_name] = [payload]
                    new_query = urlencode(mutated_params, doseq=True)
                    test_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

                    try:
                        res = await http_client.get(test_url)
                        resp_text_lower = res.text.lower()
                        for err in SQL_ERRORS:
                            if err in resp_text_lower:
                                findings.append(SQLiFinding(
                                    vuln_type="SQLi",
                                    url=test_url,
                                    evidence=f"SQL error pattern '{err}' detected in response for parameter '{param_name}'",
                                    fingerprint_hash=f"sqli:{parsed.netloc}{parsed.path}:{param_name}"
                                ))
                                break
                        if findings:
                            break
                    except Exception as e:
                        logger.debug("SQLi HTTP check failed: %s", e)

        # 2. Shell out to sqlmap if available and no findings yet
        if not findings and shutil.which("sqlmap"):
            try:
                cmd = ["sqlmap", "-u", target_url, "--batch", "--random-agent", "--level=1", "--risk=1"]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if "is vulnerable" in proc.stdout.lower():
                    findings.append(SQLiFinding(
                        vuln_type="SQLi",
                        url=target_url,
                        evidence="sqlmap confirmed parameter is vulnerable to SQL injection",
                        fingerprint_hash=f"sqli:{parsed.netloc}{parsed.path}:sqlmap"
                    ))
            except Exception as e:
                logger.debug("sqlmap execution failed or timed out: %s", e)

        return findings
