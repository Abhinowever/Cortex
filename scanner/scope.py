"""Scope validation module for Cortex scanner.

Ensures scope discipline before any outbound scanner request is made.
"""

from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

def is_in_scope(url: str, allowed_domains: list[str], disallowed_domains: list[str] | None = None) -> bool:
    """Validate if a URL is explicitly within allowed scope domains.
    
    Rules:
    - Domain must match or be a subdomain of an allowed domain in allowed_domains.
    - Domain must NOT match any domain in disallowed_domains.
    """
    if not url:
        return False

    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return False

    hostname = hostname.lower()

    if disallowed_domains:
        for d in disallowed_domains:
            d_clean = d.strip().lower()
            if not d_clean:
                continue
            if hostname == d_clean or hostname.endswith("." + d_clean):
                logger.warning("Target URL %s rejected due to disallowed domain rule %s", url, d)
                return False

    if not allowed_domains:
        logger.warning("No allowed domains specified for scope check on %s", url)
        return False

    for a in allowed_domains:
        a_clean = a.strip().lower()
        if not a_clean:
            continue
        if hostname == a_clean or hostname.endswith("." + a_clean):
            return True

    logger.warning("Target URL %s outside allowed scope domains %s", url, allowed_domains)
    return False
