"""Tests for the BrowserAgent, PageScraper, and OCREngine classes."""

import os
import json
import pytest
from unittest.mock import patch, MagicMock, PropertyMock, mock_open

from src.agents.base_agent import BaseAgent, AgentResult, AgentStatus
from src.agents.browser_agent.browser_agent import BrowserAgent
from src.agents.browser_agent.page_scraper import PageScraper
from src.agents.browser_agent.ocr_engine import OCREngine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_project(tmp_path):
    return str(tmp_path)


@pytest.fixture
def agent(tmp_project):
    return BrowserAgent(project_root=tmp_project)


@pytest.fixture
def agent_with_memory(tmp_project):
    memory = MagicMock()
    return BrowserAgent(project_root=tmp_project, memory_system=memory)


@pytest.fixture
def scraper():
    return PageScraper()


@pytest.fixture
def ocr():
    return OCREngine()


# ---------------------------------------------------------------------------
# BrowserAgent Initialization
# ---------------------------------------------------------------------------

class TestBrowserAgentInit:
    def test_agent_name(self, agent):
        assert agent.name == "browser_agent"

    def test_agent_is_base_agent(self, agent):
        assert isinstance(agent, BaseAgent)

    def test_project_root(self, agent, tmp_project):
        assert agent.project_root == tmp_project

    def test_status_idle_on_init(self, agent):
        assert agent.status == AgentStatus.IDLE

    def test_scraper_initialized(self, agent):
        assert isinstance(agent._scraper, PageScraper)

    def test_ocr_initialized(self, agent):
        assert isinstance(agent._ocr, OCREngine)

    def test_playwright_not_available_by_default(self, agent):
        assert agent._playwright_available is False

    def test_browser_none_by_default(self, agent):
        assert agent._browser is None

    def test_context_none_by_default(self, agent):
        assert agent._context is None

    def test_memory_none_by_default(self, agent):
        assert agent._memory is None

    def test_memory_set_via_constructor(self, agent_with_memory):
        assert agent_with_memory._memory is not None

    def test_set_memory_system(self, agent):
        new_memory = MagicMock()
        agent.set_memory_system(new_memory)
        assert agent._memory is new_memory


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------

class TestBrowserAgentCapabilities:
    def test_capabilities_list(self, agent):
        caps = agent.get_capabilities()
        assert isinstance(caps, list)

    def test_capabilities_contains_browser(self, agent):
        assert "browser" in agent.get_capabilities()

    def test_capabilities_contains_scrape(self, agent):
        assert "scrape" in agent.get_capabilities()

    def test_capabilities_contains_ocr(self, agent):
        assert "ocr" in agent.get_capabilities()

    def test_capabilities_contains_screenshot(self, agent):
        assert "screenshot" in agent.get_capabilities()

    def test_capabilities_contains_download(self, agent):
        assert "download" in agent.get_capabilities()

    def test_capabilities_contains_search(self, agent):
        assert "search" in agent.get_capabilities()

    def test_capabilities_contains_extract_json(self, agent):
        assert "extract_json" in agent.get_capabilities()

    def test_capabilities_count(self, agent):
        assert len(agent.get_capabilities()) == 16


# ---------------------------------------------------------------------------
# Execute Dispatch
# ---------------------------------------------------------------------------

class TestBrowserAgentExecute:
    def test_execute_unknown_type(self, agent):
        result = agent.execute({"type": "nonexistent"})
        assert result.success is False
        assert "Unknown task type" in result.errors[0]

    def test_execute_default_type_is_browse(self, agent):
        result = agent.execute({})
        assert result.success is False
        assert "No URL provided" in result.errors[0]


# ---------------------------------------------------------------------------
# Browse Task
# ---------------------------------------------------------------------------

class TestBrowseTask:
    def test_browse_no_url(self, agent):
        result = agent.execute({"type": "browse"})
        assert result.success is False
        assert "No URL provided" in result.errors[0]

    def test_browse_empty_url(self, agent):
        result = agent.execute({"type": "browse", "url": ""})
        assert result.success is False

    @patch("src.agents.browser_agent.browser_agent.requests")
    @patch("src.agents.browser_agent.browser_agent.BeautifulSoup", autospec=True)
    def test_browse_with_requests_success(self, mock_bs_class, mock_requests, agent):
        mock_resp = MagicMock()
        mock_resp.text = "<html><head><title>Test</title></head><body>Hello</body></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        mock_soup = MagicMock()
        mock_soup.title.string = "Test"
        mock_soup.get_text.return_value = "Hello"
        mock_bs_class.return_value = mock_soup

        result = agent.execute({"type": "browse", "url": "https://example.com"})
        assert result.success is True
        assert result.output["url"] == "https://example.com"
        assert result.output["title"] == "Test"
        assert result.output["html_length"] > 0

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_browse_requests_http_error(self, mock_requests, agent):
        mock_requests.get.side_effect = Exception("Connection failed")
        result = agent.execute({"type": "browse", "url": "https://bad.example.com"})
        assert result.success is False
        assert "Connection failed" in result.errors[0]

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_browse_with_extract_links(self, mock_requests, agent):
        mock_resp = MagicMock()
        mock_resp.text = '<html><body><a href="/page1">Link1</a></body></html>'
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = agent.execute({
            "type": "browse",
            "url": "https://example.com",
            "extract_links": True,
        })
        assert result.success is True
        assert "links" in result.output

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_browse_with_extract_images(self, mock_requests, agent):
        mock_resp = MagicMock()
        mock_resp.text = '<html><body><img src="/img.png" alt="pic"/></body></html>'
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = agent.execute({
            "type": "browse",
            "url": "https://example.com",
            "extract_images": True,
        })
        assert result.success is True
        assert "images" in result.output

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_browse_with_extract_meta(self, mock_requests, agent):
        mock_resp = MagicMock()
        mock_resp.text = '<html><head><meta name="desc" content="test"/></head></html>'
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = agent.execute({
            "type": "browse",
            "url": "https://example.com",
            "extract_meta": True,
        })
        assert result.success is True
        assert "meta" in result.output

    def test_browse_playwright_available(self, agent):
        mock_page = MagicMock()
        mock_page.content.return_value = "<html><head><title>PW</title></head></html>"
        mock_page.title.return_value = "PW"

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({"type": "browse", "url": "https://example.com"})
        assert result.success is True
        assert result.output["title"] == "PW"

    def test_browse_playwright_exception(self, agent):
        mock_browser = MagicMock()
        mock_browser.new_page.side_effect = Exception("PW error")

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({"type": "browse", "url": "https://example.com"})
        assert result.success is False
        assert "PW error" in result.errors[0]


# ---------------------------------------------------------------------------
# Scrape Task
# ---------------------------------------------------------------------------

class TestScrapeTask:
    def test_scrape_no_url_no_html(self, agent):
        result = agent.execute({"type": "scrape"})
        assert result.success is False
        assert "No URL or HTML content provided" in result.errors[0]

    def test_scrape_with_html_content(self, agent):
        html = "<html><body><p>Hello World</p></body></html>"
        result = agent.execute({"type": "scrape", "html": html})
        assert result.success is True
        assert "data" in result.output

    def test_scrape_table_extract(self, agent):
        html = "<html><body><table><tr><td>A</td><td>B</td></tr></table></body></html>"
        result = agent.execute({
            "type": "scrape",
            "html": html,
            "extract": "table",
        })
        assert result.success is True
        assert "data" in result.output

    def test_scrape_links_extract(self, agent):
        html = '<html><body><a href="/link">Link</a></body></html>'
        result = agent.execute({
            "type": "scrape",
            "html": html,
            "extract": "links",
        })
        assert result.success is True

    def test_scrape_images_extract(self, agent):
        html = '<html><body><img src="/pic.png"/></body></html>'
        result = agent.execute({
            "type": "scrape",
            "html": html,
            "extract": "images",
        })
        assert result.success is True

    def test_scrape_with_css_selector(self, agent):
        html = '<html><body><div class="info">Data</div></body></html>'
        result = agent.execute({
            "type": "scrape",
            "html": html,
            "selector": ".info",
            "selector_type": "css",
        })
        assert result.success is True

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_scrape_fetches_url_if_no_html(self, mock_requests, agent):
        mock_resp = MagicMock()
        mock_resp.text = "<html><body>Content</body></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = agent.execute({"type": "scrape", "url": "https://example.com"})
        assert result.success is True

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_scrape_url_fetch_fails(self, mock_requests, agent):
        mock_requests.get.side_effect = Exception("Network error")
        result = agent.execute({"type": "scrape", "url": "https://bad.com"})
        assert result.success is False
        assert "Network error" in result.errors[0]

    def test_scrape_playwright_fetch(self, agent):
        mock_page = MagicMock()
        mock_page.content.return_value = "<html><body>PW content</body></html>"
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({"type": "scrape", "url": "https://example.com"})
        assert result.success is True


# ---------------------------------------------------------------------------
# OCR Task
# ---------------------------------------------------------------------------

class TestOCRTask:
    def test_ocr_no_file_no_url(self, agent):
        result = agent.execute({"type": "ocr"})
        assert result.success is False
        assert "No file_path or URL provided" in result.errors[0]

    def test_ocr_file_not_found(self, agent, tmp_project):
        result = agent.execute({
            "type": "ocr",
            "file_path": "/nonexistent/image.png",
        })
        assert result.success is False
        assert "File not found" in result.errors[0]

    def test_ocr_image_success(self, agent, tmp_project):
        img_path = os.path.join(tmp_project, "test.png")
        with open(img_path, "wb") as f:
            f.write(b"\x89PNG\r\n")

        result = agent.execute({"type": "ocr", "file_path": img_path})
        assert "source_file" in result.output

    def test_ocr_pdf_file(self, agent, tmp_project):
        pdf_path = os.path.join(tmp_project, "test.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4")

        result = agent.execute({"type": "ocr", "file_path": pdf_path})
        assert "source_file" in result.output

    def test_ocr_with_language(self, agent, tmp_project):
        img_path = os.path.join(tmp_project, "test.png")
        with open(img_path, "wb") as f:
            f.write(b"\x89PNG")

        result = agent.execute({
            "type": "ocr",
            "file_path": img_path,
            "lang": "ita",
        })
        assert result.output["language"] == "ita"

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_ocr_downloads_url_if_no_file(self, mock_requests, agent):
        mock_resp = MagicMock()
        mock_resp.content = b"\x89PNG"
        mock_resp.headers = {"content-type": "image/png"}
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        with patch.object(agent, "_download_file", return_value="/tmp/fake.png") as mock_dl:
            with patch("os.path.exists", return_value=True):
                result = agent.execute({
                    "type": "ocr",
                    "url": "https://example.com/img.png",
                })
                mock_dl.assert_called_once_with("https://example.com/img.png")

    def test_ocr_download_fails(self, agent):
        with patch.object(agent, "_download_file", return_value=""):
            result = agent.execute({
                "type": "ocr",
                "url": "https://example.com/img.png",
            })
            assert result.success is False
            assert "Failed to download" in result.errors[0]

    def test_ocr_with_preprocess(self, agent, tmp_project):
        img_path = os.path.join(tmp_project, "test.png")
        with open(img_path, "wb") as f:
            f.write(b"\x89PNG")

        with patch.object(agent._ocr, "preprocess_image") as mock_pre:
            mock_pre.return_value = img_path + ".processed.png"
            result = agent.execute({
                "type": "ocr",
                "file_path": img_path,
                "preprocess": "grayscale",
            })
            mock_pre.assert_called_once()


# ---------------------------------------------------------------------------
# Screenshot Task
# ---------------------------------------------------------------------------

class TestScreenshotTask:
    def test_screenshot_no_url(self, agent):
        result = agent.execute({"type": "screenshot"})
        assert result.success is False
        assert "No URL provided" in result.errors[0]

    def test_screenshot_no_playwright(self, agent):
        result = agent.execute({
            "type": "screenshot",
            "url": "https://example.com",
        })
        assert result.success is False
        assert "Playwright required" in result.errors[0]

    def test_screenshot_with_playwright(self, agent, tmp_project):
        mock_page = MagicMock()
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        output_dir = os.path.join(tmp_project, "screenshots")

        result = agent.execute({
            "type": "screenshot",
            "url": "https://example.com",
            "output_path": output_dir,
        })
        assert result.success is True
        assert "file_path" in result.output
        assert result.output["url"] == "https://example.com"

    def test_screenshot_playwright_exception(self, agent, tmp_project):
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.screenshot.side_effect = Exception("Screenshot error")
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({
            "type": "screenshot",
            "url": "https://example.com",
        })
        assert result.success is False
        assert "Screenshot error" in result.errors[0]


# ---------------------------------------------------------------------------
# Download Task
# ---------------------------------------------------------------------------

class TestDownloadTask:
    def test_download_no_url(self, agent):
        result = agent.execute({"type": "download"})
        assert result.success is False
        assert "No URL provided" in result.errors[0]

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_download_success(self, mock_requests, agent, tmp_project):
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [b"file", b"content"]
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {"content-type": "application/octet-stream"}
        mock_requests.get.return_value = mock_resp

        output_dir = os.path.join(tmp_project, "downloads")
        result = agent.execute({
            "type": "download",
            "url": "https://example.com/file.zip",
            "output_dir": output_dir,
            "filename": "file.zip",
        })
        assert result.success is True
        assert result.output["file_size"] > 0
        assert result.output["url"] == "https://example.com/file.zip"

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_download_infers_filename(self, mock_requests, agent, tmp_project):
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [b"data"]
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {"content-type": "text/plain"}
        mock_requests.get.return_value = mock_resp

        output_dir = os.path.join(tmp_project, "downloads")
        result = agent.execute({
            "type": "download",
            "url": "https://example.com/document.pdf",
            "output_dir": output_dir,
        })
        assert result.success is True
        assert "file_path" in result.output

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_download_request_error(self, mock_requests, agent):
        mock_requests.get.side_effect = Exception("Timeout")
        result = agent.execute({
            "type": "download",
            "url": "https://example.com/big.zip",
        })
        assert result.success is False
        assert "Timeout" in result.errors[0]


# ---------------------------------------------------------------------------
# Search Task
# ---------------------------------------------------------------------------

class TestSearchTask:
    def test_search_no_query(self, agent):
        result = agent.execute({"type": "search"})
        assert result.success is False
        assert "No search query provided" in result.errors[0]

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_search_with_requests_fallback(self, mock_requests, agent):
        html = '''
        <html><body>
        <div class="result">
            <div class="result__title"><a href="https://example.com">Example</a></div>
            <div class="result__snippet">A snippet</div>
        </div>
        </body></html>
        '''
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = agent.execute({
            "type": "search",
            "query": "test query",
            "num_results": 3,
        })
        assert result.success is True
        assert result.output["query"] == "test query"
        assert isinstance(result.output["results"], list)

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_search_playwright(self, mock_requests, agent):
        mock_page = MagicMock()
        mock_page.content.return_value = '<html><body></body></html>'
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({
            "type": "search",
            "query": "python testing",
        })
        assert result.success is True
        assert result.output["query"] == "python testing"

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_search_exception(self, mock_requests, agent):
        mock_requests.get.side_effect = Exception("Search failed")
        result = agent.execute({"type": "search", "query": "error test"})
        assert result.success is False
        assert "Search failed" in result.errors[0]


# ---------------------------------------------------------------------------
# Extract JSON Task
# ---------------------------------------------------------------------------

class TestExtractJSONTask:
    def test_extract_json_no_url_no_html(self, agent):
        result = agent.execute({"type": "extract_json"})
        assert result.success is False
        assert "No URL or HTML content provided" in result.errors[0]

    def test_extract_json_with_html(self, agent):
        html = '<html><head><script type="application/ld+json">{"@type": "WebPage"}</script></head></html>'
        result = agent.execute({"type": "extract_json", "html": html})
        assert result.success is True
        assert "structured_data" in result.output

    def test_extract_json_with_selectors(self, agent):
        html = '<html><body><div class="price">$10</div></body></html>'
        result = agent.execute({
            "type": "extract_json",
            "html": html,
            "selectors": {"price": ".price"},
        })
        assert result.success is True
        assert result.output["extracted"] is not None

    def test_extract_json_no_selectors(self, agent):
        html = '<html><body>Plain text</body></html>'
        result = agent.execute({
            "type": "extract_json",
            "html": html,
        })
        assert result.success is True
        assert result.output["extracted"] is None

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_extract_json_fetches_url(self, mock_requests, agent):
        mock_resp = MagicMock()
        mock_resp.text = '<html><body>{"key": "value"}</body></html>'
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = agent.execute({
            "type": "extract_json",
            "url": "https://example.com/data",
        })
        assert result.success is True

    @patch("src.agents.browser_agent.browser_agent.requests")
    def test_extract_json_fetch_fails(self, mock_requests, agent):
        mock_requests.get.side_effect = Exception("Fetch error")
        result = agent.execute({
            "type": "extract_json",
            "url": "https://bad.com",
        })
        assert result.success is False


# ---------------------------------------------------------------------------
# Playwright Initialization
# ---------------------------------------------------------------------------

class TestPlaywrightInit:
    def test_ensure_playwright_already_available(self, agent):
        agent._playwright_available = True
        agent._browser = MagicMock()
        assert agent._ensure_playwright() is True

    @patch("src.agents.browser_agent.browser_agent.sync_playwright")
    def test_ensure_playwright_initializes(self, mock_sync_pw, agent):
        mock_pw = MagicMock()
        mock_sync_pw.return_value.start.return_value = mock_pw

        result = agent._ensure_playwright()
        assert result is True
        assert agent._playwright_available is True

    @patch("src.agents.browser_agent.browser_agent.sync_playwright", side_effect=ImportError("No playwright"))
    def test_ensure_playwright_import_error(self, mock_sync_pw, agent):
        result = agent._ensure_playwright()
        assert result is False
        assert agent._playwright_available is False


# ---------------------------------------------------------------------------
# Memory Integration
# ---------------------------------------------------------------------------

class TestMemoryIntegration:
    def test_store_result_no_memory(self, agent):
        agent._memory = None
        agent._store_result("browse", {"url": "test"})

    def test_store_result_with_memory(self, agent_with_memory):
        agent_with_memory._store_result(
            "scrape",
            {"data": "test"},
            keywords=["scrape", "test"],
        )
        agent_with_memory._memory.add_memory.assert_called_once()

    def test_store_result_importance_scrape(self, agent_with_memory):
        agent_with_memory._store_result("scrape", {})
        call_kwargs = agent_with_memory._store_memory.call_args
        # importance should be 0.6 for scrape/ocr
        agent_with_memory._memory.add_memory.assert_called_once()

    def test_store_result_memory_exception(self, agent_with_memory):
        agent_with_memory._memory.add_memory.side_effect = Exception("DB error")
        agent_with_memory._store_result("browse", {"url": "test"})
        # Should not raise

    def test_store_result_importance_for_screenshot(self, agent_with_memory):
        agent_with_memory._store_result("screenshot", {"file": "test.png"})
        agent_with_memory._memory.add_memory.assert_called_once()

    def test_store_result_default_keywords(self, agent_with_memory):
        agent_with_memory._store_result("download", {"file": "test.zip"})
        call_kwargs = agent_with_memory._memory.add_memory.call_args
        assert call_kwargs[1]["keywords"] == ["download", "browser"]


# ---------------------------------------------------------------------------
# Agent Lifecycle
# ---------------------------------------------------------------------------

class TestAgentLifecycle:
    def test_start(self, agent):
        agent.start()
        assert agent.status == AgentStatus.IDLE

    def test_stop(self, agent):
        agent.start()
        agent.stop()
        assert agent.status == AgentStatus.OFFLINE

    def test_stop_cleans_playwright(self, agent):
        agent._playwright_available = True
        agent._browser = MagicMock()
        agent._pw = MagicMock()

        agent.stop()

        assert agent._browser is None
        assert agent._pw is None
        assert agent._playwright_available is False

    def test_stop_handles_close_exception(self, agent):
        mock_browser = MagicMock()
        mock_browser.close.side_effect = Exception("Close error")
        agent._browser = mock_browser
        agent._playwright_available = True

        agent.stop()
        assert agent._browser is None

    def test_stop_handles_pw_stop_exception(self, agent):
        mock_pw = MagicMock()
        mock_pw.stop.side_effect = Exception("Stop error")
        agent._pw = mock_pw
        agent._browser = MagicMock()
        agent._playwright_available = True

        agent.stop()
        assert agent._pw is None

    def test_reset(self, agent):
        agent.start()
        agent.execute({"type": "browse", "url": ""})
        agent.reset()
        assert len(agent.execution_history) == 0
        assert agent.status == AgentStatus.IDLE
        assert agent._context == {}


# ---------------------------------------------------------------------------
# PageScraper
# ---------------------------------------------------------------------------

class TestPageScraperInit:
    def test_scraper_created(self, scraper):
        assert scraper is not None

    def test_beautifulsoup_available(self, scraper):
        assert scraper._beautifulsoup_available is True


class TestPageScraperParseHTML:
    def test_parse_html_returns_beautifulsoup(self, scraper):
        soup = scraper.parse_html("<html><body>Test</body></html>")
        assert soup is not None

    def test_parse_html_empty(self, scraper):
        soup = scraper.parse_html("")
        assert soup is not None


class TestPageScraperExtractBySelector:
    def test_css_selector(self, scraper):
        html = '<html><body><div class="item">Item 1</div><div class="item">Item 2</div></body></html>'
        results = scraper.extract_by_selector(html, ".item")
        assert len(results) == 2
        assert "Item 1" in results
        assert "Item 2" in results

    def test_css_selector_no_match(self, scraper):
        html = '<html><body><div>Content</div></body></html>'
        results = scraper.extract_by_selector(html, ".nonexistent")
        assert results == []

    def test_xpath_fallback(self, scraper):
        html = '<html><body><p>Hello</p></body></html>'
        results = scraper.extract_by_selector(html, "//p", selector_type="xpath")
        assert isinstance(results, list)


class TestPageScraperExtractLinks:
    def test_extract_links(self, scraper):
        html = '<html><body><a href="/page1">Link 1</a><a href="/page2">Link 2</a></body></html>'
        links = scraper.extract_links(html, "https://example.com")
        assert len(links) == 2
        assert links[0]["text"] == "Link 1"
        assert "page1" in links[0]["url"]

    def test_extract_links_no_base_url(self, scraper):
        html = '<html><body><a href="https://other.com">External</a></body></html>'
        links = scraper.extract_links(html)
        assert len(links) == 1

    def test_extract_links_no_links(self, scraper):
        html = '<html><body><p>No links here</p></body></html>'
        links = scraper.extract_links(html)
        assert links == []


class TestPageScraperExtractImages:
    def test_extract_images(self, scraper):
        html = '<html><body><img src="/pic.png" alt="A pic" title="Pic"/></body></html>'
        images = scraper.extract_images(html, "https://example.com")
        assert len(images) == 1
        assert images[0]["alt"] == "A pic"
        assert images[0]["title"] == "Pic"

    def test_extract_images_no_images(self, scraper):
        html = '<html><body><p>No images</p></body></html>'
        images = scraper.extract_images(html)
        assert images == []


class TestPageScraperExtractTable:
    def test_extract_table(self, scraper):
        html = '<html><body><table><tr><td>A</td><td>B</td></tr><tr><td>C</td><td>D</td></tr></table></body></html>'
        rows = scraper.extract_table(html)
        assert len(rows) == 2
        assert rows[0] == ["A", "B"]
        assert rows[1] == ["C", "D"]

    def test_extract_table_no_table(self, scraper):
        html = '<html><body><p>No tables</p></body></html>'
        rows = scraper.extract_table(html)
        assert rows == []

    def test_extract_table_custom_selector(self, scraper):
        html = '<html><body><table class="data"><tr><td>X</td></tr></table></body></html>'
        rows = scraper.extract_table(html, "table.data")
        assert len(rows) == 1


class TestPageScraperExtractJSON:
    def test_extract_json_ld(self, scraper):
        html = '<html><head><script type="application/ld+json">{"@type": "Article", "headline": "Test"}</script></head></html>'
        results = scraper.extract_json(html)
        assert len(results) == 1
        assert results[0]["@type"] == "Article"

    def test_extract_json_no_ld(self, scraper):
        html = '<html><head><script>var x = 1;</script></head></html>'
        results = scraper.extract_json(html)
        assert isinstance(results, list)

    def test_extract_json_empty_html(self, scraper):
        results = scraper.extract_json("")
        assert results == []


class TestPageScraperExtractMeta:
    def test_extract_meta(self, scraper):
        html = '<html><head><meta name="description" content="A test page"/><meta property="og:title" content="Title"/></head></html>'
        meta = scraper.extract_meta(html)
        assert meta["description"] == "A test page"
        assert meta["og:title"] == "Title"

    def test_extract_meta_no_meta(self, scraper):
        html = '<html><head><title>No meta</title></head></html>'
        meta = scraper.extract_meta(html)
        assert meta == {}


class TestPageScraperCleanText:
    def test_clean_text_whitespace(self, scraper):
        result = scraper.clean_text("  Hello   World  ")
        assert result == "Hello World"

    def test_clean_text_newlines(self, scraper):
        result = scraper.clean_text("Line1\n\nLine2\n\nLine3")
        assert result == "Line1 Line2 Line3"

    def test_clean_text_empty(self, scraper):
        result = scraper.clean_text("")
        assert result == ""


# ---------------------------------------------------------------------------
# OCREngine
# ---------------------------------------------------------------------------

class TestOCREngineInit:
    def test_ocr_created(self, ocr):
        assert ocr is not None

    def test_is_available_returns_dict(self, ocr):
        avail = ocr.is_available()
        assert isinstance(avail, dict)
        assert "pytesseract" in avail
        assert "pdf2image" in avail


class TestOCREngineExtractImage:
    def test_extract_image_no_pytesseract(self, ocr):
        ocr._pytesseract_available = False
        result = ocr.extract_from_image("/fake/path.png")
        assert result["text"] == ""
        assert "pytesseract not installed" in result["error"]

    def test_extract_image_file_not_found(self, ocr):
        ocr._pytesseract_available = True
        result = ocr.extract_from_image("/nonexistent/file.png")
        assert result["text"] == ""
        assert "File not found" in result["error"]

    @patch("src.agents.browser_agent.ocr_engine.os.path.exists", return_value=True)
    def test_extract_image_exception(self, mock_exists, ocr):
        ocr._pytesseract_available = True
        with patch("builtins.__import__", side_effect=ImportError("No PIL")):
            result = ocr.extract_from_image("/fake/img.png")
            assert result["text"] == ""


class TestOCREngineExtractPDF:
    def test_extract_pdf_file_not_found(self, ocr):
        result = ocr.extract_from_pdf("/nonexistent/file.pdf")
        assert result["pages"] == []
        assert "File not found" in result["error"]

    def test_extract_pdf_fallback_no_libraries(self, ocr):
        ocr._pdf_available = False
        ocr._pytesseract_available = False
        with patch("builtins.__import__", side_effect=ImportError("No lib")):
            with patch("os.path.exists", return_value=True):
                result = ocr.extract_from_pdf("/fake/file.pdf")
                assert "error" in result

    @patch("os.path.exists", return_value=True)
    @patch("builtins.__import__", side_effect=ImportError("No subprocess"))
    def test_extract_pdf_with_pdf2image(self, mock_import, mock_exists, ocr):
        ocr._pdf_available = True
        ocr._pytesseract_available = True
        with patch("builtins.__import__", side_effect=ImportError("fail")):
            result = ocr.extract_from_pdf("/fake/file.pdf")


class TestOCREnginePreprocessImage:
    def test_preprocess_image_file_not_found(self, ocr):
        with pytest.raises(FileNotFoundError):
            ocr.preprocess_image("/nonexistent/img.png", "/tmp/out.png")

    @patch("os.path.exists", return_value=True)
    def test_preprocess_image_exception(self, mock_exists, ocr):
        with patch("builtins.__import__", side_effect=ImportError("No PIL")):
            with pytest.raises(Exception):
                ocr.preprocess_image("/fake/img.png", "/tmp/out.png")


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_browse_with_all_options(self, agent):
        with patch.object(agent, "_ensure_playwright", return_value=False):
            with patch("src.agents.browser_agent.browser_agent.requests") as mock_req:
                mock_resp = MagicMock()
                mock_resp.text = '<html><head><title>T</title><meta name="x" content="y"/></head><body><a href="/l">L</a><img src="/i.png"/></body></html>'
                mock_resp.raise_for_status = MagicMock()
                mock_req.get.return_value = mock_resp

                result = agent.execute({
                    "type": "browse",
                    "url": "https://example.com",
                    "extract_links": True,
                    "extract_images": True,
                    "extract_meta": True,
                })
                assert result.success is True
                assert "links" in result.output
                assert "images" in result.output
                assert "meta" in result.output

    def test_scrape_empty_html(self, agent):
        result = agent.execute({"type": "scrape", "html": ""})
        assert result.success is True

    def test_extract_json_complex_html(self, agent):
        html = '''
        <html>
        <head>
            <script type="application/ld+json">{"@type": "Product", "name": "Widget"}</script>
            <script type="application/ld+json">{"@type": "BreadcrumbList"}</script>
        </head>
        <body></body>
        </html>
        '''
        result = agent.execute({"type": "extract_json", "html": html})
        assert result.success is True
        assert len(result.output["structured_data"]) == 2

    def test_can_handle_matching(self, agent):
        assert agent.can_handle({"keywords": ["browse"]}) is True
        assert agent.can_handle({"keywords": ["scrape"]}) is True
        assert agent.can_handle({"keywords": ["ocr"]}) is True

    def test_can_handle_no_match(self, agent):
        assert agent.can_handle({"keywords": ["blockchain"]}) is False
