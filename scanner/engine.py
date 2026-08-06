import os
import logging
import httpx

from scanner.scope import is_in_scope
from scanner.crawler import PlaywrightCrawler
from scanner.detectors.xss import XSSDetector
from scanner.detectors.sqli import SQLiDetector
from scanner.detectors.ssrf import SSRFDetector
from scanner.detectors.idor import IDORDetector

logger = logging.getLogger(__name__)


async def trigger_triage_for_findings(findings: list[dict], triage_url: str) -> int:
    """Shared scan-to-triage chain helper function for newly created findings."""
    triaged_count = 0
    endpoint = triage_url.rstrip("/")
    async with httpx.AsyncClient() as client:
        for finding in findings:
            finding_id = finding.get("id")
            if not finding_id:
                continue
            try:
                url = f"{endpoint}/triage/{finding_id}"
                resp = await client.post(url)
                if resp.status_code == 200:
                    logger.info("Auto-triage completed for finding ID %s", finding_id)
                    triaged_count += 1
                else:
                    logger.error("Auto-triage failed for finding ID %s: HTTP %s %s", finding_id, resp.status_code, resp.text)
            except Exception as e:
                logger.error("Auto-triage exception for finding ID %s: %s", finding_id, e)
    return triaged_count


class ScanEngine:
    def __init__(self, backend_url: str | None = None, triage_url: str | None = None):
        self.backend_url = (backend_url or os.getenv("BACKEND_URL", "http://localhost:8000")).rstrip("/")
        self.triage_url = (triage_url or os.getenv("TRIAGE_URL", "http://localhost:8001")).rstrip("/")

    async def fetch_program_scope(self, program_id: int) -> tuple[list[str], list[str]]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.backend_url}/programs/{program_id}")
            if resp.status_code != 200:
                raise ValueError(f"Program ID {program_id} not found in backend: {resp.text}")
            data = resp.json()
            return data.get("in_scope_domains", []), data.get("out_of_scope_domains", [])

    async def trigger_triage(self, findings: list[dict]) -> int:
        """Trigger triage chain for given list of findings."""
        return await trigger_triage_for_findings(findings, self.triage_url)

    async def run_scan(self, target_url: str, program_id: int, in_scope_domains: list[str] | None = None, out_of_scope_domains: list[str] | None = None, auto_triage: bool = True) -> list[dict]:
        # Fetch scope from backend if not provided directly
        if in_scope_domains is None:
            in_scope_domains, out_of_scope_domains = await self.fetch_program_scope(program_id)

        # 1. Validate Scope BEFORE any request
        if not is_in_scope(target_url, in_scope_domains, out_of_scope_domains):
            logger.error("Scan aborted: Target URL %s is OUT OF SCOPE for program %s", target_url, program_id)
            raise ValueError(f"Target URL {target_url} is out of scope for program {program_id}")

        logger.info("Scope validated for %s. Starting Playwright crawl...", target_url)

        # 2. Crawl Target
        crawler = PlaywrightCrawler(allowed_domains=in_scope_domains, disallowed_domains=out_of_scope_domains)
        crawl_result = await crawler.crawl(target_url)

        # 3. Detect Vulnerabilities across all 4 classes
        xss_detector = XSSDetector(allowed_domains=in_scope_domains)
        sqli_detector = SQLiDetector(allowed_domains=in_scope_domains)
        ssrf_detector = SSRFDetector(allowed_domains=in_scope_domains)
        idor_detector = IDORDetector(allowed_domains=in_scope_domains)

        all_findings = []

        for visited_url in crawl_result.visited_urls:
            all_findings.extend(await xss_detector.scan_url(visited_url))
            all_findings.extend(await sqli_detector.scan_url(visited_url))
            all_findings.extend(await ssrf_detector.scan_url(visited_url))
            all_findings.extend(await idor_detector.scan_url(visited_url))

        # 4. Report Findings to Backend API
        posted_findings = []
        async with httpx.AsyncClient() as client:
            for finding in all_findings:
                payload = {
                    "vuln_type": finding.vuln_type,
                    "url": finding.url,
                    "evidence": finding.evidence,
                    "severity": None,
                    "fingerprint_hash": finding.fingerprint_hash,
                    "status": "new"
                }
                resp = await client.post(f"{self.backend_url}/findings", json=payload)
                if resp.status_code == 201 or resp.status_code == 200:
                    posted_findings.append(resp.json())
                else:
                    logger.error("Failed to POST finding to backend: %s", resp.text)

        # 5. Chain Triage (dedup -> severity -> PoC -> report) for newly posted findings
        if auto_triage and posted_findings:
            logger.info("Triggering post-scan triage chain for %d findings...", len(posted_findings))
            await self.trigger_triage(posted_findings)

        return posted_findings

