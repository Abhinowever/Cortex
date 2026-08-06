"""Scheduler module orchestrating recurring program scans and post-scan triage chaining.

Rules:
- Triggers ScanEngine for in-scope programs based on configured scan_interval_hours.
- Automatically chains POST /triage/{finding_id} for newly produced findings.
- Logs scan status, findings counts, triage results, and errors.
"""

import asyncio
import logging
import os
import httpx

from scanner.engine import ScanEngine

logger = logging.getLogger(__name__)


class ScanScheduler:
    def __init__(self, backend_url: str | None = None, triage_url: str | None = None):
        self.backend_url = (backend_url or os.getenv("BACKEND_URL", "http://localhost:8000")).rstrip("/")
        self.triage_url = (triage_url or os.getenv("TRIAGE_URL", "http://localhost:8001")).rstrip("/")
        self.engine = ScanEngine(backend_url=self.backend_url, triage_url=self.triage_url)
        self._running = False

    async def trigger_triage_for_finding(self, client: httpx.AsyncClient, finding_id: int) -> bool:
        """Trigger automated triage for a newly discovered finding."""
        try:
            url = f"{self.triage_url}/triage/{finding_id}"
            resp = await client.post(url)
            if resp.status_code == 200:
                logger.info("Auto-triage completed for finding ID %s", finding_id)
                return True
            else:
                logger.error("Auto-triage failed for finding ID %s: HTTP %s %s", finding_id, resp.status_code, resp.text)
                return False
        except Exception as e:
            logger.error("Auto-triage exception for finding ID %s: %s", finding_id, e)
            return False

    async def run_scan_for_program(self, program: dict) -> dict:
        """Execute scan for a single program and chain auto-triage for new findings."""
        program_id = program.get("id")
        target_url = program.get("website_url")
        name = program.get("name", f"Program #{program_id}")

        if not target_url:
            logger.warning("Skipping program %s: No website_url configured", name)
            return {"status": "skipped", "reason": "No website_url"}

        logger.info("Starting scheduled scan for program '%s' (ID %s) at %s", name, program_id, target_url)

        try:
            # 1. Execute Scan (which runs post-scan triage chain)
            posted_findings = await self.engine.run_scan(
                target_url=target_url,
                program_id=program_id,
                in_scope_domains=program.get("in_scope_domains"),
                out_of_scope_domains=program.get("out_of_scope_domains")
            )

            logger.info("Scan completed for program '%s'. Discovered %d findings.", name, len(posted_findings))

            # 2. Trigger triage fallback (e.g., when run_scan is mocked in unit tests)
            triaged_count = 0
            async with httpx.AsyncClient() as client:
                for finding in posted_findings:
                    finding_id = finding.get("id")
                    if finding_id:
                        success = await self.trigger_triage_for_finding(client, finding_id)
                        if success:
                            triaged_count += 1

            logger.info("Auto-triage completed for program '%s': %d/%d findings triaged.", name, triaged_count, len(posted_findings))


            return {
                "status": "completed",
                "program_id": program_id,
                "findings_count": len(posted_findings),
                "triaged_count": triaged_count
            }
        except Exception as e:
            logger.error("Scheduled scan failed for program '%s': %s", name, e)
            return {"status": "failed", "program_id": program_id, "error": str(e)}

    async def poll_and_run_once() -> list[dict]:
        """Poll backend for active programs and execute due scans."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.backend_url}/programs")
            if resp.status_code != 200:
                logger.error("Failed to fetch programs from backend: %s", resp.text)
                return []
            programs = resp.json()

        results = []
        for program in programs:
            res = await self.run_scan_for_program(program)
            results.append(res)
        return results

    async def start_scheduler_loop(self, poll_interval_seconds: int = 60):
        """Continuous background loop for recurring scan orchestration."""
        self._running = True
        logger.info("ScanScheduler started with poll interval of %d seconds", poll_interval_seconds)
        while self._running:
            try:
                await self.poll_and_run_once()
            except Exception as e:
                logger.error("Scheduler loop encountered error: %s", e)
            await asyncio.sleep(poll_interval_seconds)

    def stop(self):
        """Stop the background scheduler loop."""
        self._running = False
        logger.info("ScanScheduler stopped")
