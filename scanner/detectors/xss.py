"""XSS detector module for Cortex scanner.

Detects reflected and DOM-based XSS using Playwright.
"""

from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from playwright.async_api import async_playwright
import logging
import uuid
import httpx

logger = logging.getLogger(__name__)

XSS_MARKER = "ctx_xss_test_"

@dataclass
class XSSFinding:
    vuln_type: str
    url: str
    evidence: str
    fingerprint_hash: str


class XSSDetector:
    def __init__(self, allowed_domains: list[str]):
        self.allowed_domains = allowed_domains

    async def scan_url(self, target_url: str) -> list[XSSFinding]:
        findings = []
        parsed = urlparse(target_url)
        params = parse_qs(parsed.query)

        if not params:
            return findings

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            page = await browser.new_page()

            # Set up dialog listener for DOM XSS execution detection
            dialog_triggered = []
            page.on("dialog", lambda dialog: dialog_triggered.append(dialog.message))

            for param_name in params.keys():
                marker_id = f"{XSS_MARKER}{uuid.uuid4().hex[:8]}"
                payload = f"<script>alert('{marker_id}')</script>"

                # Construct mutated query string
                mutated_params = params.copy()
                mutated_params[param_name] = [payload]
                new_query = urlencode(mutated_params, doseq=True)
                test_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

                # Fast HTTP reflected check first
                try:
                    async with httpx.AsyncClient(timeout=5.0) as http_client:
                        res = await http_client.get(test_url)
                        if payload in res.text or marker_id in res.text:
                            findings.append(XSSFinding(
                                vuln_type="XSS",
                                url=test_url,
                                evidence=f"Reflected XSS payload landed unescaped in HTTP response for parameter '{param_name}'",
                                fingerprint_hash=f"xss:{parsed.netloc}{parsed.path}:{param_name}"
                            ))
                            continue
                except Exception as e:
                    logger.debug("HTTP check skipped: %s", e)

                # Playwright DOM/Dialog execution check
                try:
                    dialog_triggered.clear()
                    await page.goto(test_url, wait_until="commit", timeout=5000)
                    content = await page.content()

                    if any(marker_id in msg for msg in dialog_triggered):
                        findings.append(XSSFinding(
                            vuln_type="XSS",
                            url=test_url,
                            evidence=f"Reflected/DOM XSS payload executed alert popup with marker '{marker_id}' on param '{param_name}'",
                            fingerprint_hash=f"xss:{parsed.netloc}{parsed.path}:{param_name}"
                        ))
                    elif payload in content or marker_id in content:
                        findings.append(XSSFinding(
                            vuln_type="XSS",
                            url=test_url,
                            evidence=f"Reflected XSS payload landed unescaped in HTML DOM response for parameter '{param_name}'",
                            fingerprint_hash=f"xss:{parsed.netloc}{parsed.path}:{param_name}"
                        ))
                except Exception as e:
                    logger.warning("Failed XSS scan on %s: %s", test_url, e)

            await browser.close()

        return findings
