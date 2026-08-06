"""Abstract LLM client interface and concrete provider implementations for Cortex triage.

Rules:
- LLM provider SDKs (OpenAI, Anthropic, etc.) are imported ONLY within this file.
- The active provider is determined dynamically by the LLM_PROVIDER environment variable.
"""

from abc import ABC, abstractmethod
from typing import Literal
import json
import logging
import os
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SeverityResult(BaseModel):
    severity: Literal["Critical", "High", "Medium", "Low"]
    justification: str = Field(min_length=1)


class LLMClient(ABC):
    @abstractmethod
    async def classify_severity(self, finding: dict) -> SeverityResult:
        """Classify the severity of a finding and provide a justification."""
        pass

    @abstractmethod
    async def generate_poc(self, finding: dict) -> list[str]:
        """Generate numbered reproduction steps based strictly on captured evidence."""
        pass

    @abstractmethod
    async def draft_report(self, finding: dict, poc_steps: list[str] | None = None) -> str:
        """Draft a structured disclosure report in Markdown with required sections."""
        pass

    @abstractmethod
    async def check_duplicate(self, finding_a: dict, finding_b: dict) -> bool:
        """Check if finding_a and finding_b represent the same underlying vulnerability."""
        pass


class MockLLMClient(LLMClient):
    """Mock LLM Client for testing and local offline fallback."""

    async def classify_severity(self, finding: dict) -> SeverityResult:
        vuln_type = (finding.get("vuln_type") or "").upper()
        if "XSS" in vuln_type or "SQL" in vuln_type or "RCE" in vuln_type:
            return SeverityResult(
                severity="High",
                justification=f"Mock analysis: {vuln_type} allows potential client/server side execution."
            )
        return SeverityResult(
            severity="Medium",
            justification=f"Mock analysis: {vuln_type} finding assessed with standard impact."
        )

    async def generate_poc(self, finding: dict) -> list[str]:
        target_url = finding.get("url", "http://target.local")
        evidence = finding.get("evidence", "Evidence captured by scanner")
        return [
            f"Navigate to {target_url}",
            f"Observe scanner evidence: {evidence}",
            "Verify vulnerability behavior in target response."
        ]

    async def draft_report(self, finding: dict, poc_steps: list[str] | None = None) -> str:
        steps = poc_steps or await self.generate_poc(finding)
        steps_formatted = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
        vuln_type = finding.get("vuln_type", "Vulnerability")
        url = finding.get("url", "http://target.local")
        evidence = finding.get("evidence", "")

        return (
            f"# Disclosure Report: {vuln_type}\n\n"
            f"## Summary\n"
            f"A {vuln_type} vulnerability was identified at `{url}`.\n\n"
            f"## Impact\n"
            f"An attacker can exploit this endpoint resulting in unexpected vulnerability behavior.\n\n"
            f"## Steps to Reproduce\n"
            f"{steps_formatted}\n\n"
            f"## Suggested Fix\n"
            f"Sanitize and validate all user inputs at `{url}` and apply contextual encoding."
        )

    async def check_duplicate(self, finding_a: dict, finding_b: dict) -> bool:
        v_a = (finding_a.get("vuln_type") or "").upper()
        v_b = (finding_b.get("vuln_type") or "").upper()
        u_a = finding_a.get("url", "").split("?")[0]
        u_b = finding_b.get("url", "").split("?")[0]

        # Consider near-duplicate if same vuln_type and base URL match
        return (v_a == v_b) and (u_a == u_b) and len(u_a) > 0


class OpenAILLMClient(LLMClient):
    """OpenAI implementation of LLMClient."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    async def classify_severity(self, finding: dict) -> SeverityResult:
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. Falling back to MockLLMClient.")
            return await MockLLMClient().classify_severity(finding)

        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.api_key)
            prompt = (
                f"Classify vulnerability severity (Critical/High/Medium/Low) and provide a concise justification.\n"
                f"Finding Details:\n"
                f"Vuln Type: {finding.get('vuln_type')}\n"
                f"URL: {finding.get('url')}\n"
                f"Evidence: {finding.get('evidence')}\n"
            )
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity vulnerability triage assistant. Return JSON with 'severity' and 'justification'."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            return SeverityResult(
                severity=data.get("severity", "Medium"),
                justification=data.get("justification", "Assessed by OpenAI LLM.")
            )
        except Exception as e:
            logger.error("OpenAI API call failed: %s. Falling back to MockLLMClient.", e)
            return await MockLLMClient().classify_severity(finding)

    async def generate_poc(self, finding: dict) -> list[str]:
        if not self.api_key:
            return await MockLLMClient().generate_poc(finding)
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.api_key)
            prompt = (
                f"Generate clear reproduction steps based strictly on the captured finding evidence.\n"
                f"Do not invent new payloads or attack steps.\n"
                f"Finding Details:\nURL: {finding.get('url')}\nEvidence: {finding.get('evidence')}\n"
                f"Return JSON: {{\"steps\": [\"step 1\", \"step 2\"]}}"
            )
            resp = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(resp.choices[0].message.content)
            return data.get("steps", await MockLLMClient().generate_poc(finding))
        except Exception as e:
            logger.error("OpenAI generate_poc failed: %s", e)
            return await MockLLMClient().generate_poc(finding)

    async def draft_report(self, finding: dict, poc_steps: list[str] | None = None) -> str:
        if not self.api_key:
            return await MockLLMClient().draft_report(finding, poc_steps)
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.api_key)
            steps = poc_steps or await self.generate_poc(finding)
            steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
            prompt = (
                f"Draft a vulnerability disclosure report in markdown.\n"
                f"MUST include exact H2 headings: ## Summary, ## Impact, ## Steps to Reproduce, ## Suggested Fix.\n"
                f"Details:\nVuln Type: {finding.get('vuln_type')}\nURL: {finding.get('url')}\n"
                f"Evidence: {finding.get('evidence')}\nSteps to Reproduce:\n{steps_text}\n"
            )
            resp = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI draft_report failed: %s", e)
            return await MockLLMClient().draft_report(finding, poc_steps)

    async def check_duplicate(self, finding_a: dict, finding_b: dict) -> bool:
        if not self.api_key:
            return await MockLLMClient().check_duplicate(finding_a, finding_b)
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.api_key)
            prompt = (
                f"Determine if these two security findings are duplicate reports of the same vulnerability.\n"
                f"Finding A: {finding_a}\nFinding B: {finding_b}\n"
                f"Return JSON: {{\"is_duplicate\": true/false}}"
            )
            resp = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(resp.choices[0].message.content)
            return bool(data.get("is_duplicate", False))
        except Exception as e:
            logger.error("OpenAI check_duplicate failed: %s", e)
            return await MockLLMClient().check_duplicate(finding_a, finding_b)


class AnthropicLLMClient(LLMClient):
    """Anthropic implementation of LLMClient."""

    def __init__(self, api_key: str | None = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model

    async def classify_severity(self, finding: dict) -> SeverityResult:
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Falling back to MockLLMClient.")
            return await MockLLMClient().classify_severity(finding)

        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            prompt = (
                f"Classify vulnerability severity (Critical/High/Medium/Low) and provide a concise justification.\n"
                f"Respond ONLY with valid JSON: {{\"severity\": \"High\", \"justification\": \"reason\"}}\n"
                f"Finding Details:\n"
                f"Vuln Type: {finding.get('vuln_type')}\n"
                f"URL: {finding.get('url')}\n"
                f"Evidence: {finding.get('evidence')}\n"
            )
            response = await client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text
            data = json.loads(text)
            return SeverityResult(
                severity=data.get("severity", "Medium"),
                justification=data.get("justification", "Assessed by Anthropic LLM.")
            )
        except Exception as e:
            logger.error("Anthropic API call failed: %s. Falling back to MockLLMClient.", e)
            return await MockLLMClient().classify_severity(finding)

    async def generate_poc(self, finding: dict) -> list[str]:
        if not self.api_key:
            return await MockLLMClient().generate_poc(finding)
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            prompt = (
                f"Generate reproduction steps based strictly on captured finding evidence.\n"
                f"Return JSON: {{\"steps\": [\"step 1\", \"step 2\"]}}\n"
                f"Finding: {finding.get('url')} - Evidence: {finding.get('evidence')}\n"
            )
            resp = await client.messages.create(
                model=self.model,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            data = json.loads(resp.content[0].text)
            return data.get("steps", await MockLLMClient().generate_poc(finding))
        except Exception as e:
            logger.error("Anthropic generate_poc failed: %s", e)
            return await MockLLMClient().generate_poc(finding)

    async def draft_report(self, finding: dict, poc_steps: list[str] | None = None) -> str:
        if not self.api_key:
            return await MockLLMClient().draft_report(finding, poc_steps)
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            steps = poc_steps or await self.generate_poc(finding)
            steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
            prompt = (
                f"Draft a vulnerability disclosure report in markdown with section headers:\n"
                f"## Summary\n## Impact\n## Steps to Reproduce\n## Suggested Fix\n"
                f"Finding: {finding.get('vuln_type')} at {finding.get('url')}\n"
                f"Evidence: {finding.get('evidence')}\nSteps:\n{steps_text}\n"
            )
            resp = await client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.content[0].text
        except Exception as e:
            logger.error("Anthropic draft_report failed: %s", e)
            return await MockLLMClient().draft_report(finding, poc_steps)

    async def check_duplicate(self, finding_a: dict, finding_b: dict) -> bool:
        if not self.api_key:
            return await MockLLMClient().check_duplicate(finding_a, finding_b)
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            prompt = (
                f"Determine if these two security findings are duplicates.\n"
                f"Finding A: {finding_a}\nFinding B: {finding_b}\n"
                f"Respond ONLY with valid JSON: {{\"is_duplicate\": true/false}}"
            )
            resp = await client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            data = json.loads(resp.content[0].text)
            return bool(data.get("is_duplicate", False))
        except Exception as e:
            logger.error("Anthropic check_duplicate failed: %s", e)
            return await MockLLMClient().check_duplicate(finding_a, finding_b)


def get_llm_client() -> LLMClient:
    """Factory function to instantiate the active LLMClient based on LLM_PROVIDER env var."""
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider == "openai":
        return OpenAILLMClient()
    elif provider == "anthropic":
        return AnthropicLLMClient()
    else:
        return MockLLMClient()
