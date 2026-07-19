# Page Scraper
# Handles HTML parsing, selector-based extraction, and JSON data extraction
# Supports CSS selectors, XPath, and structured data retrieval

from typing import Any, Dict, List, Optional
import re
import logging

logger = logging.getLogger(__name__)


class PageScraper:
    def __init__(self):
        self._beautifulsoup_available = False
        try:
            from bs4 import BeautifulSoup
            self._beautifulsoup_available = True
        except ImportError:
            logger.warning("beautifulsoup4 not installed; HTML parsing limited")

    def parse_html(self, html: str) -> Any:
        """Parse HTML content into a navigable structure."""
        if not self._beautifulsoup_available:
            return html
        from bs4 import BeautifulSoup
        return BeautifulSoup(html, "html.parser")

    def extract_by_selector(self, html: str, selector: str, selector_type: str = "css") -> List[str]:
        """Extract text or attribute values by CSS selector or XPath."""
        if not self._beautifulsoup_available:
            return [html]
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        if selector_type == "xpath":
            return self._extract_xpath(soup, html, selector)

        elements = soup.select(selector)
        return [el.get_text(strip=True) for el in elements]

    def _extract_xpath(self, soup: Any, html: str, xpath: str) -> List[str]:
        """Extract using lxml xpath as fallback."""
        try:
            from lxml import etree
            tree = etree.HTML(html)
            results = tree.xpath(xpath)
            return [str(r) if not hasattr(r, "text") else (r.text or "") for r in results]
        except (ImportError, Exception) as e:
            logger.warning(f"XPath extraction failed: {e}")
            return []

    def extract_links(self, html: str, base_url: str = "") -> List[Dict[str, str]]:
        """Extract all links from HTML."""
        if not self._beautifulsoup_available:
            return []
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if base_url:
                href = urljoin(base_url, href)
            links.append({"text": a_tag.get_text(strip=True), "url": href})
        return links

    def extract_images(self, html: str, base_url: str = "") -> List[Dict[str, str]]:
        """Extract all image sources from HTML."""
        if not self._beautifulsoup_available:
            return []
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        soup = BeautifulSoup(html, "html.parser")
        images = []
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if base_url and src:
                src = urljoin(base_url, src)
            images.append({
                "src": src,
                "alt": img.get("alt", ""),
                "title": img.get("title", ""),
            })
        return images

    def extract_table(self, html: str, selector: str = "table") -> List[List[str]]:
        """Extract table data as a list of rows."""
        if not self._beautifulsoup_available:
            return []
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one(selector)
        if not table:
            return []
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            rows.append(cells)
        return rows

    def extract_json(self, html: str) -> List[Any]:
        """Extract JSON-LD structured data or script-embedded JSON from HTML."""
        import json
        if not self._beautifulsoup_available:
            try:
                return [json.loads(html)]
            except (json.JSONDecodeError, TypeError):
                return []
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        results = []

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                results.append(data)
            except (json.JSONDecodeError, TypeError):
                continue

        if not results:
            for script in soup.find_all("script"):
                text = script.string or ""
                match = re.search(r"\{[\s\S]*\}", text)
                if match:
                    try:
                        results.append(json.loads(match.group()))
                    except (json.JSONDecodeError, ValueError):
                        continue

        return results

    def extract_meta(self, html: str) -> Dict[str, str]:
        """Extract meta tags from HTML."""
        if not self._beautifulsoup_available:
            return {}
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        meta = {}
        for tag in soup.find_all("meta"):
            name = tag.get("name") or tag.get("property") or tag.get("http-equiv", "")
            content = tag.get("content", "")
            if name:
                meta[name] = content
        return meta

    def clean_text(self, text: str) -> str:
        """Remove excess whitespace and normalize text."""
        text = re.sub(r"\s+", " ", text)
        return text.strip()
