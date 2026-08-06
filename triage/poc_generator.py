"""PoC generator module for Cortex triage pipeline.

Formats evidence captured by scanner into numbered reproduction steps via LLMClient.
"""

import logging
from triage.llm_client import LLMClient, get_llm_client

logger = logging.getLogger(__name__)


class PocGenerator:
    def __init__(self, client: LLMClient | None = None):
        self.client = client or get_llm_client()

    async def generate_steps(self, finding: dict) -> list[str]:
        """Generate numbered reproduction steps for a finding based on scanner evidence."""
        if not finding:
            raise ValueError("Finding data cannot be empty.")

        logger.info("Generating PoC reproduction steps for finding ID %s", finding.get("id"))
        steps = await self.client.generate_poc(finding)
        logger.info("Generated %d reproduction steps for finding ID %s", len(steps), finding.get("id"))
        return steps
