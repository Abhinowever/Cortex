"""Two-pass deduplication engine for Cortex triage pipeline.

Pass 1: Fingerprint hash matching on (vuln_type, normalized_url, parameter_name).
Pass 2: LLM semantic similarity evaluation for near-duplicates missed by Pass 1.
"""

import hashlib
import logging
from urllib.parse import parse_qs, urlparse

from triage.llm_client import LLMClient, get_llm_client

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normalize URL by lowering scheme/host, removing trailing slashes, and stripping query parameters."""
    if not url:
        return ""
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    return f"{scheme}://{netloc}{path}"


def extract_parameter_name(finding: dict) -> str:
    """Extract affected parameter name from finding evidence or URL query string."""
    evidence = finding.get("evidence", "")
    if "param=" in evidence:
        try:
            return evidence.split("param=")[1].split()[0].strip()
        except IndexError:
            pass

    url = finding.get("url", "")
    if "?" in url:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        if query:
            # Sort keys for deterministic parameter representation
            return ",".join(sorted(query.keys()))
    return ""


def compute_fingerprint_hash(vuln_type: str, url: str, parameter_name: str = "") -> str:
    """Compute SHA-256 fingerprint hash for Pass 1 fast deduplication."""
    norm_url = normalize_url(url)
    raw = f"{vuln_type.upper()}|{norm_url}|{parameter_name.lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class Deduplicator:
    def __init__(self, client: LLMClient | None = None):
        self.client = client or get_llm_client()

    def pass_1_hash_check(self, new_finding: dict, existing_findings: list[dict]) -> dict | None:
        """Pass 1: Fast fingerprint hash lookup."""
        new_vuln = new_finding.get("vuln_type", "")
        new_url = new_finding.get("url", "")
        new_param = extract_parameter_name(new_finding)
        new_hash = new_finding.get("fingerprint_hash") or compute_fingerprint_hash(new_vuln, new_url, new_param)

        for existing in existing_findings:
            if existing.get("id") == new_finding.get("id"):
                continue
            ex_hash = existing.get("fingerprint_hash") or compute_fingerprint_hash(
                existing.get("vuln_type", ""),
                existing.get("url", ""),
                extract_parameter_name(existing)
            )
            if new_hash == ex_hash:
                logger.info("Pass 1 hash match: finding %s is duplicate of %s", new_finding.get("id"), existing.get("id"))
                return existing
        return None

    async def pass_2_llm_check(self, new_finding: dict, existing_findings: list[dict]) -> dict | None:
        """Pass 2: LLM semantic evaluation for near-duplicates."""
        for existing in existing_findings:
            if existing.get("id") == new_finding.get("id"):
                continue
            if existing.get("status") == "duplicate":
                continue

            is_dup = await self.client.check_duplicate(new_finding, existing)
            if is_dup:
                logger.info("Pass 2 LLM match: finding %s is duplicate of %s", new_finding.get("id"), existing.get("id"))
                return existing
        return None

    async def deduplicate(self, new_finding: dict, existing_findings: list[dict]) -> tuple[bool, int | None]:
        """Execute two-pass deduplication logic.

        Returns (is_duplicate, original_finding_id).
        """
        # Pass 1: Fast Hash Pass
        match_pass1 = self.pass_1_hash_check(new_finding, existing_findings)
        if match_pass1:
            return True, match_pass1.get("id")

        # Pass 2: LLM Semantic Pass
        match_pass2 = await self.pass_2_llm_check(new_finding, existing_findings)
        if match_pass2:
            return True, match_pass2.get("id")

        return False, None
