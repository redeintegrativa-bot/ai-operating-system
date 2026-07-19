"""Tests for the BrowserAgent, PageScraper, and OCREngine classes."""

import os
import json
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

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
# Helper: create sys.modules mock for requests + bs4
# ---------------------------------------------------------------------------

def _make_requests_bs4_mock(response_text="", raise_status=True):
    """Create a context-managed sys.modules patch for requests + bs4."""
    mock_requests = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = response_text
    mock_resp.iter_content.return_value = [b"chunk1", b"chunk2"]
    mock_resp.content = b"raw_content"
    mock_resp.headers = {"content-type": "text/html"}
    if raise_status:
        mock_resp.raise_for_status = MagicMock()
    else:
        mock_resp.raise_for_status.side_effect = Exception("HTTP Error")
    mock_requests.get.return_value = mock_resp

    mock_bs4 = MagicMock()
    mock_soup = MagicMock()
    mock_soup.title.string = "Test Page"
    mock_soup.get_text.return_value = "extracted text"
    mock_bs4.BeautifulSoup.return_value = mock_soup

    return mock_requests, mock_bs4, mock_resp, mock_soup


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

    def test_browse_with_requests_fallback(self, agent):
        mock_requests, mock_bs4, mock_resp, mock_soup = _make_requests_bs4_mock(
            response_text="<html><head><title>Test</title></head><body>Hello</body></html>"
        )
        mock_soup.title.string = "Test"

        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
            result = agent.execute({"type": "browse", "url": "https://example.com"})

        assert result.success is True
        assert result.output["url"] == "https://example.com"
        assert result.output["title"] == "Test"
        assert result.output["html_length"] > 0

    def test_browse_requests_http_error(self, agent):
        mock_requests, mock_bs4, _, _ = _make_requests_bs4_mock()
        mock_requests.get.side_effect = Exception("Connection failed")

        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
            result = agent.execute({"type": "browse", "url": "https://bad.example.com"})

        assert result.success is False
        assert "Connection failed" in result.errors[0]

    def test_browse_with_extract_links(self, agent):
        mock_requests, mock_bs4, mock_resp, mock_soup = _make_requests_bs4_mock()

        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
            result = agent.execute({
                "type": "browse",
                "url": "https://example.com",
                "extract_links": True,
            })

        assert result.success is True
        assert "links" in result.output

    def test_browse_with_extract_images(self, agent):
        mock_requests, mock_bs4, mock_resp, mock_soup = _make_requests_bs4_mock()

        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
            result = agent.execute({
                "type": "browse",
                "url": "https://example.com",
                "extract_images": True,
            })

        assert result.success is True
        assert "images" in result.output

    def test_browse_with_extract_meta(self, agent):
        mock_requests, mock_bs4, mock_resp, mock_soup = _make_requests_bs4_mock()

        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
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

    def test_browse_playwright_with_extract_links(self, agent):
        mock_page = MagicMock()
        mock_page.content.return_value = '<html><body><a href="/link">L</a></body></html>'
        mock_page.title.return_value = "Links"

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({
            "type": "browse",
            "url": "https://example.com",
            "extract_links": True,
        })
        assert result.success is True
        assert "links" in result.output

    def test_browse_playwright_with_extract_meta(self, agent):
        mock_page = MagicMock()
        mock_page.content.return_value = '<html><head><meta name="x" content="y"/></head></html>'
        mock_page.title.return_value = "Meta"

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({
            "type": "browse",
            "url": "https://example.com",
            "extract_meta": True,
        })
        assert result.success is True
        assert "meta" in result.output

    def test_browse_playwright_with_extract_images(self, agent):
        mock_page = MagicMock()
        mock_page.content.return_value = '<html><body><img src="/i.png"/></body></html>'
        mock_page.title.return_value = "Images"

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({
            "type": "browse",
            "url": "https://example.com",
            "extract_images": True,
        })
        assert result.success is True
        assert "images" in result.output


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

    def test_scrape_fetches_url_if_no_html(self, agent):
        mock_requests, mock_bs4, mock_resp, mock_soup = _make_requests_bs4_mock(
            response_text="<html><body>Content</body></html>"
        )
        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
            result = agent.execute({"type": "scrape", "url": "https://example.com"})
        assert result.success is True

    def test_scrape_url_fetch_fails(self, agent):
        mock_requests, mock_bs4, _, _ = _make_requests_bs4_mock()
        mock_requests.get.side_effect = Exception("Network error")
        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
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

    def test_scrape_playwright_fetch_exception(self, agent):
        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("Nav error")
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({"type": "scrape", "url": "https://example.com"})
        assert result.success is False
        assert "Nav error" in result.errors[0]


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

    def test_ocr_downloads_url_if_no_file(self, agent):
        with patch.object(agent, "_download_file", return_value="/tmp/fake.png") as mock_dl:
            with patch("os.path.exists", return_value=True):
                result = agent.execute({
                    "type": "ocr",
                    "url": "https://example.com/img.png",
                })
                mock_dl.assert_called_once_with("https://example.com/img.png", None)

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

    def test_ocr_preprocess_fails_uses_original(self, agent, tmp_project):
        img_path = os.path.join(tmp_project, "test.png")
        with open(img_path, "wb") as f:
            f.write(b"\x89PNG")

        with patch.object(agent._ocr, "preprocess_image", side_effect=Exception("Preprocess error")):
            result = agent.execute({
                "type": "ocr",
                "file_path": img_path,
                "preprocess": "grayscale",
            })
            assert "source_file" in result.output


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

    def test_screenshot_playwright_exception(self, agent):
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

    def test_screenshot_custom_dimensions(self, agent, tmp_project):
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
            "width": 800,
            "height": 600,
            "full_page": False,
        })
        assert result.success is True
        assert result.output["full_page"] is False

    def test_screenshot_default_output_path(self, agent):
        mock_page = MagicMock()
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({
            "type": "screenshot",
            "url": "https://example.com",
        })
        assert result.success is True
        assert os.path.isdir(os.path.dirname(result.output["file_path"]))


# ---------------------------------------------------------------------------
# Download Task
# ---------------------------------------------------------------------------

class TestDownloadTask:
    def test_download_no_url(self, agent):
        result = agent.execute({"type": "download"})
        assert result.success is False
        assert "No URL provided" in result.errors[0]

    def test_download_success(self, agent, tmp_project):
        mock_requests, mock_bs4, mock_resp, _ = _make_requests_bs4_mock()
        mock_resp.iter_content.return_value = [b"file", b"content"]
        mock_resp.headers = {"content-type": "application/octet-stream"}

        output_dir = os.path.join(tmp_project, "downloads")
        with patch.dict("sys.modules", {"requests": mock_requests}):
            result = agent.execute({
                "type": "download",
                "url": "https://example.com/file.zip",
                "output_path": output_dir,
                "output_dir": output_dir,
                "filename": "file.zip",
            })
        assert result.success is True
        assert result.output["url"] == "https://example.com/file.zip"
        assert result.output["file_size"] > 0

    def test_download_infers_filename(self, agent, tmp_project):
        mock_requests, _, mock_resp, _ = _make_requests_bs4_mock()
        mock_resp.headers = {"content-type": "text/plain"}

        output_dir = os.path.join(tmp_project, "downloads")
        with patch.dict("sys.modules", {"requests": mock_requests}):
            result = agent.execute({
                "type": "download",
                "url": "https://example.com/document.pdf",
                "output_dir": output_dir,
            })
        assert result.success is True
        assert "file_path" in result.output

    def test_download_request_error(self, agent):
        mock_requests, _, _, _ = _make_requests_bs4_mock()
        mock_requests.get.side_effect = Exception("Timeout")

        with patch.dict("sys.modules", {"requests": mock_requests}):
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

    def test_search_with_requests_fallback(self, agent):
        html = '''
        <html><body>
        <div class="result">
            <div class="result__title"><a href="https://example.com">Example</a></div>
            <div class="result__snippet">A snippet</div>
        </div>
        </body></html>
        '''
        mock_requests, mock_bs4, mock_resp, mock_soup = _make_requests_bs4_mock(
            response_text=html
        )
        real_bs4 = None
        try:
            from bs4 import BeautifulSoup as RealBS
            real_bs4 = RealBS
        except ImportError:
            pass

        if real_bs4 is None:
            # Simulate parsing: mock soup.select returns results
            mock_result_div = MagicMock()
            mock_title_el = MagicMock()
            mock_title_el.get_text.return_value = "Example"
            mock_title_el.get.return_value = "https://example.com"
            mock_snippet_el = MagicMock()
            mock_snippet_el.get_text.return_value = "A snippet"

            mock_result_div.select_one.side_effect = lambda sel: {
                ".result__title a": mock_title_el,
                ".result__snippet": mock_snippet_el,
            }.get(sel)

            mock_soup.select.return_value = [mock_result_div]

        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
            result = agent.execute({
                "type": "search",
                "query": "test query",
                "num_results": 3,
            })
        assert result.success is True
        assert result.output["query"] == "test query"
        assert isinstance(result.output["results"], list)

    def test_search_playwright(self, agent):
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

    def test_search_playwright_exception(self, agent):
        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("Search PW error")
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({"type": "search", "query": "error test"})
        assert result.success is False
        assert "Search PW error" in result.errors[0]

    def test_search_requests_exception(self, agent):
        mock_requests, mock_bs4, _, _ = _make_requests_bs4_mock()
        mock_requests.get.side_effect = Exception("Search failed")

        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
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

    def test_extract_json_fetches_url(self, agent):
        mock_requests, mock_bs4, _, _ = _make_requests_bs4_mock(
            response_text='<html><body>{"key": "value"}</body></html>'
        )
        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
            result = agent.execute({
                "type": "extract_json",
                "url": "https://example.com/data",
            })
        assert result.success is True

    def test_extract_json_fetch_fails(self, agent):
        mock_requests, mock_bs4, _, _ = _make_requests_bs4_mock()
        mock_requests.get.side_effect = Exception("Fetch error")
        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
            result = agent.execute({
                "type": "extract_json",
                "url": "https://bad.com",
            })
        assert result.success is False

    def test_extract_json_playwright_fetch(self, agent):
        html = '<html><head><script type="application/ld+json">{"@type":"Thing"}</script></head></html>'
        mock_page = MagicMock()
        mock_page.content.return_value = html
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({
            "type": "extract_json",
            "url": "https://example.com/data",
        })
        assert result.success is True

    def test_extract_json_playwright_exception(self, agent):
        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("PW fetch error")
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({
            "type": "extract_json",
            "url": "https://example.com/data",
        })
        assert result.success is False
        assert "PW fetch error" in result.errors[0]

    def test_extract_json_complex_html(self, agent):
        html = '''
        <html><head>
            <script type="application/ld+json">{"@type": "Product", "name": "Widget"}</script>
            <script type="application/ld+json">{"@type": "BreadcrumbList"}</script>
        </head></html>
        '''
        result = agent.execute({"type": "extract_json", "html": html})
        assert result.success is True
        # With bs4: parses LD+JSON scripts; without bs4: falls back to raw JSON parse on whole html
        structured = result.output["structured_data"]
        assert isinstance(structured, list)


# ---------------------------------------------------------------------------
# Playwright Initialization
# ---------------------------------------------------------------------------

class TestPlaywrightInit:
    def test_ensure_playwright_already_available(self, agent):
        agent._playwright_available = True
        agent._browser = MagicMock()
        assert agent._ensure_playwright() is True

    def test_ensure_playwright_initializes(self, agent):
        mock_pw_module = MagicMock()
        mock_pw_instance = MagicMock()
        mock_pw_module.start.return_value = mock_pw_instance

        with patch.dict("sys.modules", {"playwright": MagicMock(), "playwright.sync_api": MagicMock()}) as mock_modules:
            mock_modules["playwright.sync_api"].sync_playwright.return_value = mock_pw_module
            result = agent._ensure_playwright()

        assert result is True
        assert agent._playwright_available is True

    def test_ensure_playwright_import_error(self, agent):
        with patch("builtins.__import__", side_effect=ImportError("No playwright")):
            result = agent._ensure_playwright()
        assert result is False
        assert agent._playwright_available is False

    def test_ensure_playwright_launch_error(self, agent):
        mock_pw_module = MagicMock()
        mock_pw_module.start.side_effect = Exception("Launch failed")

        with patch.dict("sys.modules", {"playwright": MagicMock(), "playwright.sync_api": MagicMock()}) as mock_modules:
            mock_modules["playwright.sync_api"].sync_playwright.return_value = mock_pw_module
            result = agent._ensure_playwright()

        assert result is False
        assert agent._playwright_available is False


# ---------------------------------------------------------------------------
# Memory Integration
# ---------------------------------------------------------------------------

class TestMemoryIntegration:
    def test_store_result_no_memory(self, agent):
        agent._memory = None
        # Should not raise
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
        call_kwargs = agent_with_memory._memory.add_memory.call_args
        assert call_kwargs[1]["importance"] == 0.6

    def test_store_result_importance_ocr(self, agent_with_memory):
        agent_with_memory._store_result("ocr", {})
        call_kwargs = agent_with_memory._memory.add_memory.call_args
        assert call_kwargs[1]["importance"] == 0.6

    def test_store_result_importance_browse(self, agent_with_memory):
        agent_with_memory._store_result("browse", {})
        call_kwargs = agent_with_memory._memory.add_memory.call_args
        assert call_kwargs[1]["importance"] == 0.4

    def test_store_result_importance_screenshot(self, agent_with_memory):
        agent_with_memory._store_result("screenshot", {})
        call_kwargs = agent_with_memory._memory.add_memory.call_args
        assert call_kwargs[1]["importance"] == 0.4

    def test_store_result_memory_exception(self, agent_with_memory):
        agent_with_memory._memory.add_memory.side_effect = Exception("DB error")
        # Should not raise
        agent_with_memory._store_result("browse", {"url": "test"})

    def test_store_result_default_keywords(self, agent_with_memory):
        agent_with_memory._store_result("download", {"file": "test.zip"})
        call_kwargs = agent_with_memory._memory.add_memory.call_args
        assert call_kwargs[1]["keywords"] == ["download", "browser"]

    def test_store_result_custom_keywords(self, agent_with_memory):
        agent_with_memory._store_result(
            "search", {"query": "test"}, keywords=["search", "query"]
        )
        call_kwargs = agent_with_memory._memory.add_memory.call_args
        assert call_kwargs[1]["keywords"] == ["search", "query"]

    def test_store_result_uses_episodic_memory_type(self, agent_with_memory):
        agent_with_memory._store_result("browse", {})
        call_kwargs = agent_with_memory._memory.add_memory.call_args
        from src.core.memory import MemoryType
        assert call_kwargs[1]["memory_type"] == MemoryType.EPISODIC


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

    def test_stop_without_playwright(self, agent):
        agent.stop()
        assert agent.status == AgentStatus.OFFLINE

    def test_reset_clears_history(self, agent):
        agent.start()
        agent._context = {}
        agent.execute({"type": "browse", "url": ""})
        agent.reset()
        assert len(agent.execution_history) == 0
        assert agent.status == AgentStatus.IDLE


# ---------------------------------------------------------------------------
# PageScraper
# ---------------------------------------------------------------------------

class TestPageScraperInit:
    def test_scraper_created(self, scraper):
        assert scraper is not None

    def test_beautifulsoup_flag(self, scraper):
        # bs4 may or may not be installed in test env
        assert isinstance(scraper._beautifulsoup_available, bool)


class TestPageScraperParseHTML:
    def test_parse_html(self, scraper):
        result = scraper.parse_html("<html><body>Test</body></html>")
        assert result is not None

    def test_parse_html_empty(self, scraper):
        result = scraper.parse_html("")
        assert result is not None


class TestPageScraperExtractBySelector:
    def test_extract_by_selector_without_bs4(self, scraper):
        scraper._beautifulsoup_available = False
        results = scraper.extract_by_selector("<html></html>", "div")
        assert results == ["<html></html>"]


class TestPageScraperExtractLinks:
    def test_extract_links_without_bs4(self, scraper):
        scraper._beautifulsoup_available = False
        links = scraper.extract_links("<html></html>")
        assert links == []


class TestPageScraperExtractImages:
    def test_extract_images_without_bs4(self, scraper):
        scraper._beautifulsoup_available = False
        images = scraper.extract_images("<html></html>")
        assert images == []


class TestPageScraperExtractTable:
    def test_extract_table_without_bs4(self, scraper):
        scraper._beautifulsoup_available = False
        rows = scraper.extract_table("<html></html>")
        assert rows == []


class TestPageScraperExtractJSON:
    def test_extract_json_fallback_to_json_loads(self, scraper):
        scraper._beautifulsoup_available = False
        results = scraper.extract_json('{"key": "value"}')
        assert len(results) == 1
        assert results[0]["key"] == "value"

    def test_extract_json_fallback_invalid_json(self, scraper):
        scraper._beautifulsoup_available = False
        results = scraper.extract_json("not json")
        assert results == []

    def test_extract_json_fallback_empty(self, scraper):
        scraper._beautifulsoup_available = False
        results = scraper.extract_json("")
        assert results == []


class TestPageScraperExtractMeta:
    def test_extract_meta_without_bs4(self, scraper):
        scraper._beautifulsoup_available = False
        meta = scraper.extract_meta("<html></html>")
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

    def test_clean_text_tabs(self, scraper):
        result = scraper.clean_text("col1\tcol2\tcol3")
        assert result == "col1 col2 col3"

    def test_clean_text_single_space(self, scraper):
        result = scraper.clean_text("hello world")
        assert result == "hello world"


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

    def test_extract_image_import_error(self, ocr):
        ocr._pytesseract_available = True
        with patch("builtins.__import__", side_effect=ImportError("No PIL")):
            with patch("os.path.exists", return_value=True):
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
        with patch("os.path.exists", return_value=True):
            # Mock only the missing PDF libraries, not subprocess/PIL
            original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__
            def selective_import(name, *args, **kwargs):
                if name in ("pdftotext", "PyPDF2"):
                    raise ImportError(f"No module named '{name}'")
                return original_import(name, *args, **kwargs)
            with patch("builtins.__import__", side_effect=selective_import):
                result = ocr.extract_from_pdf("/fake/file.pdf")
                assert "error" in result

    def test_extract_pdf_with_pdf2image_success(self, ocr):
        ocr._pdf_available = True
        ocr._pytesseract_available = True
        mock_img = MagicMock()
        mock_pil_img = MagicMock()

        with patch("os.path.exists", return_value=True):
            with patch.dict("sys.modules", {
                "pdf2image": MagicMock(),
                "pytesseract": MagicMock(),
            }):
                mock_pdf2image = sys.modules["pdf2image"]
                mock_pdf2image.convert_from_path.return_value = [mock_pil_img]

                mock_pytesseract = sys.modules["pytesseract"]
                mock_pytesseract.image_to_string.return_value = "OCR text"

                result = ocr.extract_from_pdf("/fake/file.pdf")
                assert "full_text" in result
                assert result["total_pages"] == 1


class TestOCREnginePreprocessImage:
    def test_preprocess_image_file_not_found(self, ocr):
        with pytest.raises(FileNotFoundError):
            ocr.preprocess_image("/nonexistent/img.png", "/tmp/out.png")

    def test_preprocess_image_import_error(self, ocr):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.__import__", side_effect=ImportError("No PIL")):
                with pytest.raises(Exception):
                    ocr.preprocess_image("/fake/img.png", "/tmp/out.png")


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_browse_with_all_options_requests(self, agent):
        mock_requests, mock_bs4, mock_resp, mock_soup = _make_requests_bs4_mock()
        mock_soup.title.string = "Full"

        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
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
        # Empty string is falsy, so treated as no content
        assert result.success is False

    def test_can_handle_matching(self, agent):
        assert agent.can_handle({"keywords": ["browse"]}) is True
        assert agent.can_handle({"keywords": ["scrape"]}) is True
        assert agent.can_handle({"keywords": ["ocr"]}) is True
        assert agent.can_handle({"keywords": ["screenshot"]}) is True
        assert agent.can_handle({"keywords": ["download"]}) is True
        assert agent.can_handle({"keywords": ["search"]}) is True
        assert agent.can_handle({"keywords": ["extract_json"]}) is True

    def test_can_handle_no_match(self, agent):
        assert agent.can_handle({"keywords": ["blockchain"]}) is False
        assert agent.can_handle({"keywords": ["quantum"]}) is False

    def test_can_handle_empty_keywords(self, agent):
        assert agent.can_handle({}) is False

    def test_download_file_to_temp(self, agent):
        mock_requests, _, mock_resp, _ = _make_requests_bs4_mock()
        mock_resp.content = b"file content"
        mock_resp.headers = {"content-type": "image/png"}

        with patch.dict("sys.modules", {"requests": mock_requests}):
            result = agent._download_file("https://example.com/img.png")
        assert result != ""
        # Clean up temp file
        if result and os.path.exists(result):
            os.unlink(result)

    def test_download_file_exception(self, agent):
        mock_requests, _, _, _ = _make_requests_bs4_mock()
        mock_requests.get.side_effect = Exception("DL error")

        with patch.dict("sys.modules", {"requests": mock_requests}):
            result = agent._download_file("https://example.com/fail.png")
        assert result == ""

    def test_execute_dispatch_all_types(self, agent):
        """Verify all 7 task types are routed correctly."""
        types = ["browse", "scrape", "ocr", "screenshot", "download", "search", "extract_json"]
        for t in types:
            task = {"type": t}
            if t == "browse":
                task["url"] = ""
            elif t in ("scrape", "extract_json"):
                pass  # no url or html -> error
            elif t == "ocr":
                pass  # no file or url -> error
            elif t == "screenshot":
                task["url"] = ""
            elif t == "download":
                task["url"] = ""
            elif t == "search":
                pass  # no query -> error

            result = agent.execute(task)
            assert isinstance(result, AgentResult)

    def test_context_loaded(self, agent):
        # BrowserAgent overrides _context=None; fix it first to test BaseAgent behavior
        agent._context = {}
        agent.load_context({"key": "value"})
        ctx = agent.get_context()
        assert ctx["key"] == "value"

    def test_get_status(self, agent):
        status = agent.get_status()
        assert status["name"] == "browser_agent"
        assert status["status"] == "idle"
        assert isinstance(status["capabilities"], list)


# ---------------------------------------------------------------------------
# SessionManager
# ---------------------------------------------------------------------------

class TestSessionManagerInit:
    def test_created_with_dir(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=os.path.join(tmp_project, "sessions"))
        assert os.path.isdir(os.path.join(tmp_project, "sessions"))

    def test_custom_expiration(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project, default_expiration=3600)
        assert sm._default_expiration == 3600


class TestSessionSaveLoad:
    def test_save_and_load(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        ok = sm.save_session("test1", cookies=[{"name": "c", "value": "v"}])
        assert ok is True
        data = sm.load_session("test1")
        assert data is not None
        assert data["name"] == "test1"
        assert len(data["cookies"]) == 1
        assert data["cookies"][0]["name"] == "c"

    def test_load_nonexistent(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        assert sm.load_session("nope") is None

    def test_save_local_storage(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        sm.save_session("ls1", local_storage={"k1": "v1", "k2": "v2"})
        data = sm.load_session("ls1")
        assert data["local_storage"] == {"k1": "v1", "k2": "v2"}

    def test_save_session_storage(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        sm.save_session("ss1", session_storage={"sk": "sv"})
        data = sm.load_session("ss1")
        assert data["session_storage"] == {"sk": "sv"}

    def test_save_metadata(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        sm.save_session("m1", metadata={"source": "test"})
        data = sm.load_session("m1")
        assert data["metadata"]["source"] == "test"

    def test_update_session(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        sm.save_session("u1", cookies=[{"name": "a", "value": "1"}])
        ok = sm.update_session("u1", cookies=[{"name": "b", "value": "2"}])
        assert ok is True
        data = sm.load_session("u1")
        assert data["cookies"][0]["name"] == "b"

    def test_update_nonexistent(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        assert sm.update_session("ghost") is False


class TestSessionExpiration:
    def test_expired_session_returns_none(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project, default_expiration=0)
        sm.save_session("exp1", cookies=[{"name": "x", "value": "y"}])
        import time
        time.sleep(0.05)
        assert sm.load_session("exp1") is None

    def test_delete_expired_file(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project, default_expiration=0)
        sm.save_session("exp2")
        import time
        time.sleep(0.05)
        assert sm.load_session("exp2") is None
        path = os.path.join(tmp_project, "exp2.json")
        assert not os.path.exists(path)


class TestSessionDelete:
    def test_delete_session(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        sm.save_session("del1")
        assert sm.delete_session("del1") is True
        assert sm.load_session("del1") is None
        assert not os.path.exists(os.path.join(tmp_project, "del1.json"))

    def test_delete_nonexistent(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        assert sm.delete_session("ghost") is True


class TestSessionList:
    def test_list_sessions(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        sm.save_session("a1")
        sm.save_session("a2")
        sessions = sm.list_sessions()
        names = {s["name"] for s in sessions}
        assert "a1" in names
        assert "a2" in names

    def test_list_empty(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        assert sm.list_sessions() == []


class TestSessionCleanup:
    def test_cleanup_removes_expired(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project, default_expiration=0)
        sm.save_session("old1")
        sm.save_session("old2")
        import time
        time.sleep(0.05)
        removed = sm.cleanup_expired()
        assert removed == 2

    def test_cleanup_keeps_valid(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project, default_expiration=3600)
        sm.save_session("keep1")
        removed = sm.cleanup_expired()
        assert removed == 0
        assert sm.load_session("keep1") is not None


class TestSessionPlaywrightHelpers:
    def test_save_playwright_state(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)

        mock_context = MagicMock()
        mock_context.cookies.return_value = [
            {"name": "tok", "value": "abc123", "domain": ".example.com", "path": "/"}
        ]
        mock_page = MagicMock()
        mock_page.evaluate.return_value = {"lang": "en"}
        mock_context.pages = [mock_page]

        ok = sm.save_playwright_state("pw1", mock_context, url="https://example.com")
        assert ok is True
        data = sm.load_session("pw1")
        assert data["cookies"][0]["name"] == "tok"
        assert data["local_storage"]["lang"] == "en"

    def test_restore_playwright_state(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        sm.save_session(
            "pw2",
            cookies=[{"name": "x", "value": "y", "domain": "", "path": "/"}],
        )

        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_page.evaluate.return_value = None
        mock_context.pages = [mock_page]

        ok = sm.restore_playwright_state("pw2", mock_context)
        assert ok is True
        mock_context.add_cookies.assert_called_once()

    def test_restore_nonexistent_returns_false(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        mock_context = MagicMock()
        assert sm.restore_playwright_state("nope", mock_context) is False


class TestSessionRequestsHelpers:
    def test_save_requests_cookies(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)

        mock_jar = MagicMock()
        mock_jar.__iter__ = lambda self: iter(
            [MagicMock(name="sid", value="abc", domain=".example.com", path="/")]
        )

        ok = sm.save_requests_cookies("req1", mock_jar)
        assert ok is True
        data = sm.load_session("req1")
        assert len(data["cookies"]) == 1

    def test_restore_requests_cookies(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        sm.save_session(
            "req2",
            cookies=[{"name": "tok", "value": "123", "domain": ".ex.com", "path": "/"}],
        )

        mock_session = MagicMock()
        ok = sm.restore_requests_cookies("req2", mock_session)
        assert ok is True
        mock_session.cookies.set.assert_called_once()

    def test_restore_requests_nonexistent(self, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project)
        mock_session = MagicMock()
        assert sm.restore_requests_cookies("nope", mock_session) is False


# ---------------------------------------------------------------------------
# BrowserAgent Session Integration
# ---------------------------------------------------------------------------

class TestBrowserAgentSessionIntegration:
    def test_agent_has_session_manager(self, agent):
        from src.agents.browser_agent.session_manager import SessionManager
        assert isinstance(agent._session_manager, SessionManager)

    def test_set_session_manager(self, agent):
        from src.agents.browser_agent.session_manager import SessionManager
        new_sm = SessionManager(storage_dir="/tmp/test_sessions")
        agent.set_session_manager(new_sm)
        assert agent.get_session_manager() is new_sm

    def test_browse_with_session_playwright(self, agent, tmp_project):
        mock_page = MagicMock()
        mock_page.content.return_value = "<html><head><title>S</title></head></html>"
        mock_page.title.return_value = "S"
        mock_page.evaluate.return_value = {}
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_context.pages = [mock_page]
        mock_context.cookies.return_value = []

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        agent._playwright_available = True
        agent._browser = mock_browser

        result = agent.execute({
            "type": "browse",
            "url": "https://example.com",
            "session": "my_session",
        })
        assert result.success is True
        assert result.output["title"] == "S"
        # Session should have been saved
        sm = agent.get_session_manager()
        data = sm.load_session("my_session")
        assert data is not None

    def test_browse_with_session_requests(self, agent):
        mock_requests, mock_bs4, mock_resp, mock_soup = _make_requests_bs4_mock(
            response_text="<html><head><title>T</title></head></html>"
        )
        mock_soup.title.string = "T"
        mock_resp.cookies = {}

        with patch.dict("sys.modules", {"requests": mock_requests, "bs4": mock_bs4}):
            result = agent.execute({
                "type": "browse",
                "url": "https://example.com",
                "session": "req_session",
            })
        assert result.success is True

    def test_stop_cleans_expired_sessions(self, agent, tmp_project):
        from src.agents.browser_agent.session_manager import SessionManager
        sm = SessionManager(storage_dir=tmp_project, default_expiration=0)
        agent.set_session_manager(sm)
        sm.save_session("dead")
        import time
        time.sleep(0.05)
        agent.stop()
        assert sm.load_session("dead") is None

    def test_get_session_name_from_task(self, agent):
        assert agent._get_session_name({"session": "s1"}) == "s1"
        assert agent._get_session_name({"session_name": "s2"}) == "s2"
        assert agent._get_session_name({}) is None
