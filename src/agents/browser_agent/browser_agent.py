from typing import Any, Dict, List, Optional
import logging
import os
import time

from ..base_agent import BaseAgent, AgentResult
from .page_scraper import PageScraper
from .ocr_engine import OCREngine
from .proxy_manager import ProxyManager, ProxyInfo

logger = logging.getLogger(__name__)


class BrowserAgent(BaseAgent):
    def __init__(self, project_root: str, memory_system=None, proxy_manager: Optional[ProxyManager] = None):
        super().__init__("browser_agent", project_root)
        self._scraper = PageScraper()
        self._ocr = OCREngine()
        self._playwright_available = False
        self._browser = None
        self._context = None
        self._memory = memory_system
        self._proxy_manager = proxy_manager or ProxyManager()

    def set_memory_system(self, memory_system):
        """Set or replace the memory system for storing results."""
        self._memory = memory_system
    
    def set_proxy_manager(self, proxy_manager: ProxyManager) -> None:
        """Set or replace the proxy manager."""
        self._proxy_manager = proxy_manager
    
    def get_proxy_manager(self) -> ProxyManager:
        """Get the current proxy manager."""
        return self._proxy_manager

    def _store_result(self, task_type: str, result_data: Dict, keywords: Optional[List[str]] = None):
        """Store a result in the memory system if available."""
        if self._memory is None:
            return
        try:
            from src.core.memory import MemoryType
            importance = 0.6 if task_type in ("scrape", "ocr") else 0.4
            self._memory.add_memory(
                agent_name="browser_agent",
                memory_type=MemoryType.EPISODIC,
                content={"task_type": task_type, "result": result_data},
                keywords=keywords or [task_type, "browser"],
                importance=importance,
            )
            logger.debug("Stored %s result in memory", task_type)
        except Exception as e:
            logger.warning("Failed to store result in memory: %s", e)
    
    def _get_proxy_from_task(self, task: Dict) -> Optional[ProxyInfo]:
        """Get proxy from task parameters if specified."""
        proxy_config = task.get("proxy")
        if proxy_config is None:
            return None
        
        # If it's a proxy URL string, parse it
        if isinstance(proxy_config, str):
            return self._proxy_manager._parse_proxy(proxy_config)
        
        # If it's already a ProxyInfo, return it
        if isinstance(proxy_config, ProxyInfo):
            return proxy_config
        
        # If it's a dict, create ProxyInfo
        if isinstance(proxy_config, Dict):
            from .proxy_manager import ProxyProtocol
            protocol_map = {
                "http": ProxyProtocol.HTTP,
                "https": ProxyProtocol.HTTP,
                "socks4": ProxyProtocol.SOCKS4,
                "socks5": ProxyProtocol.SOCKS5,
            }
            protocol = protocol_map.get(proxy_config.get("protocol", "http"), ProxyProtocol.HTTP)
            return ProxyInfo(
                protocol=protocol,
                host=proxy_config.get("host", ""),
                port=proxy_config.get("port", 0),
                username=proxy_config.get("username"),
                password=proxy_config.get("password"),
            )
        
        return None

    def execute(self, task: Dict) -> AgentResult:
        task_type = task.get("type", "browse")
        handlers = {
            "browse": self._browse,
            "scrape": self._scrape,
            "ocr": self._ocr_extract,
            "screenshot": self._screenshot,
            "download": self._download,
            "search": self._search,
            "extract_json": self._extract_json,
        }
        handler = handlers.get(task_type)
        if handler is None:
            return AgentResult(
                success=False,
                output=None,
                errors=[f"Unknown task type: {task_type}"],
            )
        return handler(task)

    def get_capabilities(self) -> List[str]:
        return [
            "browser",
            "browse",
            "scrape",
            "web",
            "webpage",
            "html",
            "ocr",
            "screenshot",
            "capture",
            "download",
            "search",
            "extract_json",
            "parsing",
            "url",
            "pdf",
            "image",
        ]

    def _ensure_playwright(self) -> bool:
        """Initialize playwright browser if available."""
        if self._playwright_available and self._browser is not None:
            return True
        try:
            from playwright.sync_api import sync_playwright
            if not self._playwright_available:
                self._pw = sync_playwright().start()
                self._browser = self._pw.chromium.launch(headless=True)
                self._playwright_available = True
            return True
        except Exception as e:
            logger.warning(f"Playwright not available: {e}")
            self._playwright_available = False
            return False

    def _browse(self, task: Dict) -> AgentResult:
        """Navigate to a URL and extract page content."""
        url = task.get("url", "")
        if not url:
            return AgentResult(success=False, output=None, errors=["No URL provided"])

        extract_links = task.get("extract_links", False)
        extract_images = task.get("extract_images", False)
        extract_meta = task.get("extract_meta", False)

        if self._ensure_playwright():
            return self._browse_with_playwright(url, extract_links, extract_images, extract_meta)
        return self._browse_with_requests(url, extract_links, extract_images, extract_meta)

    def _browse_with_playwright(self, url: str, extract_links: bool, extract_images: bool, extract_meta: bool) -> AgentResult:
        """Browse using playwright for JS-rendered pages."""
        try:
            page = self._browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            html = page.content()
            title = page.title()
            page.close()

            result: Dict[str, Any] = {
                "url": url,
                "title": title,
                "html_length": len(html),
                "text": self._scraper.clean_text(self._scraper.parse_html(html).get_text() if self._scraper._beautifulsoup_available else html),
            }

            if extract_links:
                result["links"] = self._scraper.extract_links(html, url)
            if extract_images:
                result["images"] = self._scraper.extract_images(html, url)
            if extract_meta:
                result["meta"] = self._scraper.extract_meta(html)

            self._store_result("browse", result, keywords=["browse", "webpage", url])
            return AgentResult(success=True, output=result)
        except Exception as e:
            logger.error(f"Playwright browse failed: {e}")
            return AgentResult(success=False, output=None, errors=[str(e)])

    def _browse_with_requests(self, url: str, extract_links: bool, extract_images: bool, extract_meta: bool, proxy: Optional[ProxyInfo] = None) -> AgentResult:
        """Browse using requests as fallback."""
        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {"User-Agent": "Mozilla/5.0 (compatible; AIOSSrowserAgent/1.0)"}
            proxies = self._proxy_manager.get_request_proxies(proxy)
            
            response = requests.get(url, headers=headers, timeout=30, proxies=proxies)
            response.raise_for_status()
            
            if proxy:
                self._proxy_manager.mark_success(proxy)
            
            html = response.text

            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string if soup.title else ""

            result: Dict[str, Any] = {
                "url": url,
                "title": title or "",
                "html_length": len(html),
                "text": self._scraper.clean_text(soup.get_text()),
            }

            if extract_links:
                result["links"] = self._scraper.extract_links(html, url)
            if extract_images:
                result["images"] = self._scraper.extract_images(html, url)
            if extract_meta:
                result["meta"] = self._scraper.extract_meta(html)

            self._store_result("browse", result, keywords=["browse", "webpage", url])
            return AgentResult(success=True, output=result)
        except Exception as e:
            if proxy:
                self._proxy_manager.mark_failed(proxy)
            logger.error(f"Requests browse failed: {e}")
            return AgentResult(success=False, output=None, errors=[str(e)])

    def _scrape(self, task: Dict) -> AgentResult:
        """Structured scraping with selectors."""
        url = task.get("url", "")
        html_content = task.get("html", "")
        selector = task.get("selector", "")
        selector_type = task.get("selector_type", "css")
        extract_type = task.get("extract", "text")
        proxy = self._get_proxy_from_task(task)

        if not html_content and not url:
            return AgentResult(success=False, output=None, errors=["No URL or HTML content provided"])

        if not html_content:
            if self._ensure_playwright():
                try:
                    proxy_config = self._proxy_manager.get_playwright_proxy(proxy)
                    page = self._browser.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2000)
                    html_content = page.content()
                    page.close()
                except Exception as e:
                    return AgentResult(success=False, output=None, errors=[f"Failed to fetch page: {e}"])
            else:
                try:
                    import requests
                    headers = {"User-Agent": "Mozilla/5.0 (compatible; AIOSSrowserAgent/1.0)"}
                    proxies = self._proxy_manager.get_request_proxies(proxy)
                    resp = requests.get(url, headers=headers, timeout=30, proxies=proxies)
                    resp.raise_for_status()
                    if proxy:
                        self._proxy_manager.mark_success(proxy)
                    html_content = resp.text
                except Exception as e:
                    if proxy:
                        self._proxy_manager.mark_failed(proxy)
                    return AgentResult(success=False, output=None, errors=[f"Failed to fetch page: {e}"])

        result: Dict[str, Any] = {"url": url}

        if extract_type == "table":
            result["data"] = self._scraper.extract_table(html_content, selector or "table")
        elif extract_type == "links":
            result["data"] = self._scraper.extract_links(html_content, url)
        elif extract_type == "images":
            result["data"] = self._scraper.extract_images(html_content, url)
        elif selector:
            result["data"] = self._scraper.extract_by_selector(html_content, selector, selector_type)
        else:
            soup = self._scraper.parse_html(html_content)
            result["data"] = self._scraper.clean_text(soup.get_text()) if self._scraper._beautifulsoup_available else html_content

        self._store_result("scrape", result, keywords=["scrape", "data", url])
        return AgentResult(success=True, output=result)

    def _ocr_extract(self, task: Dict) -> AgentResult:
        """Extract text from images or PDFs using OCR."""
        file_path = task.get("file_path", "")
        url = task.get("url", "")
        lang = task.get("lang", "eng")
        preprocess = task.get("preprocess", None)

        if not file_path and not url:
            return AgentResult(success=False, output=None, errors=["No file_path or URL provided"])

        if url and not file_path:
            file_path = self._download_file(url)
            if not file_path:
                return AgentResult(success=False, output=None, errors=[f"Failed to download file from {url}"])

        if not os.path.exists(file_path):
            return AgentResult(success=False, output=None, errors=[f"File not found: {file_path}"])

        if preprocess:
            try:
                processed_path = file_path + ".processed.png"
                self._ocr.preprocess_image(file_path, processed_path, mode=preprocess)
                file_path = processed_path
            except Exception as e:
                logger.warning(f"Preprocessing failed, using original: {e}")

        if file_path.lower().endswith(".pdf"):
            result = self._ocr.extract_from_pdf(file_path, lang=lang)
        else:
            result = self._ocr.extract_from_image(file_path, lang=lang)

        result["source_file"] = file_path
        success = not result.get("error")
        if success:
            self._store_result("ocr", result, keywords=["ocr", "text", "extraction"])
        return AgentResult(success=success, output=result, errors=[result["error"]] if result.get("error") else [])

    def _screenshot(self, task: Dict) -> AgentResult:
        """Capture a screenshot of a web page."""
        url = task.get("url", "")
        output_path = task.get("output_path", os.path.join(self.project_root, "screenshots"))
        full_page = task.get("full_page", True)
        width = task.get("width", 1280)
        height = task.get("height", 720)

        if not url:
            return AgentResult(success=False, output=None, errors=["No URL provided"])

        if self._ensure_playwright():
            return self._screenshot_playwright(url, output_path, full_page, width, height)
        return AgentResult(
            success=False,
            output=None,
            errors=["Playwright required for screenshots (install with: pip install playwright && playwright install)"],
        )

    def _screenshot_playwright(self, url: str, output_path: str, full_page: bool, width: int, height: int) -> AgentResult:
        """Take screenshot using playwright."""
        try:
            os.makedirs(output_path, exist_ok=True)
            timestamp = int(time.time() * 1000)
            filename = os.path.join(output_path, f"screenshot_{timestamp}.png")

            page = self._browser.new_page(viewport={"width": width, "height": height})
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)
            page.screenshot(path=filename, full_page=full_page)
            page.close()

            output = {"url": url, "file_path": filename, "full_page": full_page}
            self._store_result("screenshot", output, keywords=["screenshot", "capture", url])
            return AgentResult(success=True, output=output)
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return AgentResult(success=False, output=None, errors=[str(e)])

    def _download(self, task: Dict) -> AgentResult:
        """Download a file from a URL."""
        url = task.get("url", "")
        output_dir = task.get("output_dir", os.path.join(self.project_root, "downloads"))
        filename = task.get("filename", "")
        proxy = self._get_proxy_from_task(task)

        if not url:
            return AgentResult(success=False, output=None, errors=["No URL provided"])

        try:
            import requests
            os.makedirs(output_dir, exist_ok=True)

            if not filename:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                filename = os.path.basename(parsed.path) or "download"

            output_path = os.path.join(output_dir, filename)
            headers = {"User-Agent": "Mozilla/5.0 (compatible; AIOSSrowserAgent/1.0)"}
            proxies = self._proxy_manager.get_request_proxies(proxy)
            response = requests.get(url, headers=headers, timeout=60, stream=True, proxies=proxies)
            response.raise_for_status()
            
            if proxy:
                self._proxy_manager.mark_success(proxy)

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = os.path.getsize(output_path)
            output = {
                "url": url,
                "file_path": output_path,
                "file_size": file_size,
                "content_type": response.headers.get("content-type", "unknown"),
            }
            self._store_result("download", output, keywords=["download", "file", url])
            return AgentResult(success=True, output=output)
        except Exception as e:
            if proxy:
                self._proxy_manager.mark_failed(proxy)
            logger.error(f"Download failed: {e}")
            return AgentResult(success=False, output=None, errors=[str(e)])

    def _download_file(self, url: str, proxy: Optional[ProxyInfo] = None) -> str:
        """Download a file to a temp location and return the path."""
        try:
            import requests
            import tempfile

            headers = {"User-Agent": "Mozilla/5.0 (compatible; AIOSSrowserAgent/1.0)"}
            proxies = self._proxy_manager.get_request_proxies(proxy)
            response = requests.get(url, headers=headers, timeout=30, proxies=proxies)
            response.raise_for_status()
            
            if proxy:
                self._proxy_manager.mark_success(proxy)

            suffix = ".pdf" if "pdf" in response.headers.get("content-type", "") else ".png"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(response.content)
                return f.name
        except Exception as e:
            if proxy:
                self._proxy_manager.mark_failed(proxy)
            logger.error(f"File download failed: {e}")
            return ""

    def _search(self, task: Dict) -> AgentResult:
        """Perform an automated web search and return results."""
        query = task.get("query", "")
        num_results = task.get("num_results", 5)
        proxy = self._get_proxy_from_task(task)

        if not query:
            return AgentResult(success=False, output=None, errors=["No search query provided"])

        if self._ensure_playwright():
            return self._search_playwright(query, num_results)
        return self._search_requests(query, num_results, proxy)

    def _search_playwright(self, query: str, num_results: int) -> AgentResult:
        """Search using playwright."""
        try:
            page = self._browser.new_page()
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            html = page.content()
            page.close()

            soup = self._scraper.parse_html(html)
            results = []
            if self._scraper._beautifulsoup_available:
                from bs4 import BeautifulSoup
                for g in soup.select("div.g")[:num_results]:
                    title_el = g.select_one("h3")
                    link_el = g.select_one("a")
                    snippet_el = g.select_one("div.VwiC3b")
                    if title_el and link_el:
                        results.append({
                            "title": title_el.get_text(strip=True),
                            "url": link_el.get("href", ""),
                            "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                        })

            output = {"query": query, "results": results}
            self._store_result("search", output, keywords=["search", query])
            return AgentResult(success=True, output=output)
        except Exception as e:
            logger.error(f"Playwright search failed: {e}")
            return AgentResult(success=False, output=None, errors=[str(e)])

    def _search_requests(self, query: str, num_results: int, proxy: Optional[ProxyInfo] = None) -> AgentResult:
        """Search using requests as fallback (limited)."""
        try:
            import requests
            from bs4 import BeautifulSoup
            from urllib.parse import quote_plus

            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {"User-Agent": "Mozilla/5.0 (compatible; AIOSSrowserAgent/1.0)"}
            proxies = self._proxy_manager.get_request_proxies(proxy)
            response = requests.get(search_url, headers=headers, timeout=15, proxies=proxies)
            response.raise_for_status()
            
            if proxy:
                self._proxy_manager.mark_success(proxy)

            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            for result_div in soup.select(".result")[:num_results]:
                title_el = result_div.select_one(".result__title a")
                snippet_el = result_div.select_one(".result__snippet")
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": title_el.get("href", ""),
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })

            output = {"query": query, "results": results}
            self._store_result("search", output, keywords=["search", query])
            return AgentResult(success=True, output=output)
        except Exception as e:
            if proxy:
                self._proxy_manager.mark_failed(proxy)
            logger.error(f"Search failed: {e}")
            return AgentResult(success=False, output=None, errors=[str(e)])

    def _extract_json(self, task: Dict) -> AgentResult:
        """Extract structured JSON data from a web page or HTML content."""
        url = task.get("url", "")
        html_content = task.get("html", "")
        selectors = task.get("selectors", {})

        if not html_content and not url:
            return AgentResult(success=False, output=None, errors=["No URL or HTML content provided"])

        if not html_content:
            if self._ensure_playwright():
                try:
                    page = self._browser.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2000)
                    html_content = page.content()
                    page.close()
                except Exception as e:
                    return AgentResult(success=False, output=None, errors=[f"Failed to fetch page: {e}"])
            else:
                try:
                    import requests
                    headers = {"User-Agent": "Mozilla/5.0 (compatible; AIOSSrowserAgent/1.0)"}
                    resp = requests.get(url, headers=headers, timeout=30)
                    resp.raise_for_status()
                    html_content = resp.text
                except Exception as e:
                    return AgentResult(success=False, output=None, errors=[f"Failed to fetch page: {e}"])

        structured = self._scraper.extract_json(html_content)

        extracted = {}
        if selectors:
            for key, sel in selectors.items():
                extracted[key] = self._scraper.extract_by_selector(html_content, sel)

        output = {
            "url": url,
            "structured_data": structured,
            "extracted": extracted if extracted else None,
        }
        self._store_result("extract_json", output, keywords=["extract", "json", url])
        return AgentResult(success=True, output=output)

    def stop(self):
        """Clean up playwright resources."""
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        if hasattr(self, "_pw") and self._pw:
            try:
                self._pw.stop()
            except Exception:
                pass
            self._pw = None
        self._playwright_available = False
        super().stop()
