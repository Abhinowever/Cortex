"""Playwright-based crawler module for Cortex scanner."""

from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
import logging
import httpx

from scanner.scope import is_in_scope

logger = logging.getLogger(__name__)


@dataclass
class FormInput:
    name: str
    input_type: str
    value: str = ""


@dataclass
class DiscoveredForm:
    action_url: str
    method: str
    inputs: list[FormInput] = field(default_factory=list)


@dataclass
class CrawlResult:
    visited_urls: list[str] = field(default_factory=list)
    forms: list[DiscoveredForm] = field(default_factory=list)
    url_params: list[dict] = field(default_factory=list)


class PlaywrightCrawler:
    def __init__(self, allowed_domains: list[str], disallowed_domains: list[str] | None = None, max_pages: int = 20):
        self.allowed_domains = allowed_domains
        self.disallowed_domains = disallowed_domains or []
        self.max_pages = max_pages

    async def crawl(self, start_url: str) -> CrawlResult:
        if not is_in_scope(start_url, self.allowed_domains, self.disallowed_domains):
            raise ValueError(f"Start URL {start_url} is out of scope.")

        result = CrawlResult()
        to_visit = [start_url]
        visited = set()

        async with httpx.AsyncClient(timeout=5.0) as http_client:
            while to_visit and len(visited) < self.max_pages:
                current_url = to_visit.pop(0)
                if current_url in visited:
                    continue

                if not is_in_scope(current_url, self.allowed_domains, self.disallowed_domains):
                    continue

                visited.add(current_url)
                result.visited_urls.append(current_url)

                try:
                    res = await http_client.get(current_url)
                    if res.status_code == 200:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(res.text, "html.parser")
                        for a in soup.find_all("a", href=True):
                            href = a["href"]
                            full_link = urljoin(current_url, href)
                            parsed = urlparse(full_link)
                            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                            if parsed.query:
                                clean_url += f"?{parsed.query}"
                            if clean_url not in visited and is_in_scope(clean_url, self.allowed_domains, self.disallowed_domains):
                                to_visit.append(clean_url)

                        for form in soup.find_all("form"):
                            action = form.get("action") or current_url
                            action_full = urljoin(current_url, action)
                            method = (form.get("method") or "GET").upper()
                            inputs = []
                            for inp in form.find_all(["input", "textarea", "select"]):
                                name = inp.get("name")
                                if name:
                                    inputs.append(FormInput(name=name, input_type=inp.get("type", "text"), value=inp.get("value", "")))
                            result.forms.append(DiscoveredForm(action_url=action_full, method=method, inputs=inputs))
                except Exception as e:
                    logger.warning("Crawl error on %s: %s", current_url, e)

        return result
