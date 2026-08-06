"""Report writer module for Cortex triage pipeline.

Drafts structured disclosure reports in Markdown containing Summary, Impact, Steps to Reproduce, and Suggested Fix.
"""

import logging
from triage.llm_client import LLMClient, get_llm_client

logger = logging.getLogger(__name__)


class ReportWriter:
    def __init__(self, client: LLMClient | None = None):
        self.client = client or get_llm_client()

    async def draft(self, finding: dict, poc_steps: list[str] | None = None) -> str:
        """Draft a complete markdown disclosure report for a finding."""
        if not finding:
            raise ValueError("Finding data cannot be empty.")

        logger.info("Drafting disclosure report for finding ID %s", finding.get("id"))
        report_markdown = await self.client.draft_report(finding, poc_steps)
        logger.info("Report draft generated (%d chars) for finding ID %s", len(report_markdown), finding.get("id"))
        return report_markdown
