"""Severity classifier module for Cortex triage pipeline.

Uses the abstract LLMClient interface to classify raw findings into CVSS-aligned severity ratings.
"""

import logging
from triage.llm_client import LLMClient, SeverityResult, get_llm_client

logger = logging.getLogger(__name__)


class SeverityClassifier:
    def __init__(self, client: LLMClient | None = None):
        self.client = client or get_llm_client()

    async def classify(self, finding: dict) -> SeverityResult:
        """Classify a vulnerability finding using the configured LLMClient."""
        if not finding:
            raise ValueError("Finding data cannot be empty.")

        logger.info("Classifying severity for finding ID %s (vuln_type: %s)", finding.get("id"), finding.get("vuln_type"))
        result = await self.client.classify_severity(finding)
        logger.info("Severity classification result: %s - %s", result.severity, result.justification)
        return result
