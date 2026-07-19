"""Integration tests for BrowserAgent with real websites.

These tests use safe, public test websites and include rate limiting
to avoid abuse. Tests are marked with @pytest.mark.integration and can
be skipped with: pytest -m "not integration"

Safe test websites used:
- example.com: IANA reserved domain for documentation
- httpbin.org: HTTP testing service for request/response testing
- jsonplaceholder.typicode.com: Fake REST API for testing
- filesamples.com: Sample files for download testing

Rate limiting: 2-second delay between tests to avoid service abuse.
"""

import os
import time
import pytest
import tempfile

from src.agents.browser_agent.browser_agent import BrowserAgent


RATE_LIMIT_DELAY = 2

TEST_WEBSITES = {
    "example": "https://example.com",
    "httpbin": "https://httpbin.org",
    "jsonplaceholder": "https://jsonplaceholder.typicode.com",
    "filesamples": "https://filesamples.com",
}


@pytest.fixture(scope="module")
def browser_agent():
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = BrowserAgent(project_root=tmpdir)
        agent.start()
        yield agent
        agent.stop()


@pytest.fixture(scope="module")
def rate_limiter():
    last_call = [0.0]

    def wait():
        elapsed = time.time() - last_call[0]
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        last_call[0] = time.time()

    return wait


@pytest.fixture
def screenshot_dir(tmp_path):
    screenshot_path = tmp_path / "screenshots"
    screenshot_path.mkdir()
    return str(screenshot_path)


@pytest.fixture
def download_dir(tmp_path):
    download_path = tmp_path / "downloads"
    download_path.mkdir()
    return str(download_path)


pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
]


class TestBrowseIntegration:

    def test_browse_example_com(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "browse",
            "url": TEST_WEBSITES["example"],
        })

        assert result.success is True
        assert result.output["url"] == TEST_WEBSITES["example"]
        assert result.output["html_length"] > 0
        assert "Example Domain" in result.output["title"] or "example" in result.output["title"].lower()

    def test_browse_httpbin_get(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "browse",
            "url": f"{TEST_WEBSITES['httpbin']}/get",
        })

        assert result.success is True
        assert result.output["html_length"] > 0

    def test_browse_with_links_extraction(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "browse",
            "url": TEST_WEBSITES["example"],
            "extract_links": True,
        })

        assert result.success is True
        assert "links" in result.output
        assert isinstance(result.output["links"], list)

    def test_browse_with_meta_extraction(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "browse",
            "url": TEST_WEBSITES["example"],
            "extract_meta": True,
        })

        assert result.success is True
        assert "meta" in result.output
        assert isinstance(result.output["meta"], dict)


class TestHttpbinIntegration:

    def test_httpbin_headers(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "browse",
            "url": f"{TEST_WEBSITES['httpbin']}/headers",
        })

        assert result.success is True
        assert result.output["html_length"] > 0

    def test_httpbin_user_agent(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "browse",
            "url": f"{TEST_WEBSITES['httpbin']}/user-agent",
        })

        assert result.success is True

    def test_httpbin_ip(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "browse",
            "url": f"{TEST_WEBSITES['httpbin']}/ip",
        })

        assert result.success is True


class TestJsonPlaceholderIntegration:

    def test_jsonplaceholder_posts(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "browse",
            "url": f"{TEST_WEBSITES['jsonplaceholder']}/posts",
        })

        assert result.success is True
        assert result.output["html_length"] > 0

    def test_jsonplaceholder_single_post(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "browse",
            "url": f"{TEST_WEBSITES['jsonplaceholder']}/posts/1",
        })

        assert result.success is True

    def test_jsonplaceholder_comments(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "browse",
            "url": f"{TEST_WEBSITES['jsonplaceholder']}/comments",
        })

        assert result.success is True


class TestScreenshotIntegration:

    def test_screenshot_example_com(self, browser_agent, rate_limiter, screenshot_dir):
        rate_limiter()
        result = browser_agent.execute({
            "type": "screenshot",
            "url": TEST_WEBSITES["example"],
            "output_path": screenshot_dir,
        })

        assert result.success is True
        assert "file_path" in result.output
        assert os.path.exists(result.output["file_path"])
        assert os.path.getsize(result.output["file_path"]) > 0

    def test_screenshot_custom_dimensions(self, browser_agent, rate_limiter, screenshot_dir):
        rate_limiter()
        result = browser_agent.execute({
            "type": "screenshot",
            "url": TEST_WEBSITES["example"],
            "output_path": screenshot_dir,
            "width": 800,
            "height": 600,
            "full_page": False,
        })

        assert result.success is True
        assert result.output["full_page"] is False
        assert os.path.exists(result.output["file_path"])

    def test_screenshot_httpbin(self, browser_agent, rate_limiter, screenshot_dir):
        rate_limiter()
        result = browser_agent.execute({
            "type": "screenshot",
            "url": TEST_WEBSITES["httpbin"],
            "output_path": screenshot_dir,
        })

        assert result.success is True
        assert os.path.exists(result.output["file_path"])


class TestDownloadIntegration:

    def test_download_small_file(self, browser_agent, rate_limiter, download_dir):
        rate_limiter()
        result = browser_agent.execute({
            "type": "download",
            "url": f"{TEST_WEBSITES['filesamples']}/formats/txt/sample.txt",
            "output_dir": download_dir,
        })

        assert result.success is True
        assert "file_path" in result.output
        assert os.path.exists(result.output["file_path"])
        assert result.output["file_size"] > 0

    def test_download_with_custom_filename(self, browser_agent, rate_limiter, download_dir):
        rate_limiter()
        result = browser_agent.execute({
            "type": "download",
            "url": f"{TEST_WEBSITES['filesamples']}/formats/txt/sample.txt",
            "output_dir": download_dir,
            "filename": "custom_name.txt",
        })

        assert result.success is True
        assert "custom_name.txt" in result.output["file_path"]
        assert os.path.exists(result.output["file_path"])

    def test_download_json_file(self, browser_agent, rate_limiter, download_dir):
        rate_limiter()
        result = browser_agent.execute({
            "type": "download",
            "url": f"{TEST_WEBSITES['filesamples']}/formats/json/sample.json",
            "output_dir": download_dir,
        })

        assert result.success is True
        assert os.path.exists(result.output["file_path"])


class TestSearchIntegration:

    def test_search_basic(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "search",
            "query": "python testing",
            "num_results": 3,
        })

        assert result.success is True
        assert result.output["query"] == "python testing"
        assert isinstance(result.output["results"], list)

    def test_search_returns_results(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "search",
            "query": "example domain",
            "num_results": 5,
        })

        assert result.success is True
        assert isinstance(result.output["results"], list)


class TestScrapeIntegration:

    def test_scrape_example_com(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "scrape",
            "url": TEST_WEBSITES["example"],
            "extract": "text",
        })

        assert result.success is True
        assert "data" in result.output

    def test_scrape_links(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "scrape",
            "url": TEST_WEBSITES["example"],
            "extract": "links",
        })

        assert result.success is True
        assert "data" in result.output

    def test_scrape_with_css_selector(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "scrape",
            "url": TEST_WEBSITES["example"],
            "selector": "div",
            "selector_type": "css",
        })

        assert result.success is True
        assert "data" in result.output


class TestExtractJsonIntegration:

    def test_extract_json_httpbin(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "extract_json",
            "url": f"{TEST_WEBSITES['httpbin']}/json",
        })

        assert result.success is True
        assert "structured_data" in result.output

    def test_extract_json_with_selectors(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "extract_json",
            "url": TEST_WEBSITES["example"],
            "selectors": {"title": "h1"},
        })

        assert result.success is True
        assert "extracted" in result.output


class TestProxyIntegration:

    def test_browse_with_invalid_proxy_fails(self, browser_agent, rate_limiter):
        rate_limiter()
        result = browser_agent.execute({
            "type": "browse",
            "url": TEST_WEBSITES["example"],
            "proxy": "http://invalid-proxy:9999",
        })

        assert result.success is False
        assert len(result.errors) > 0


class TestSessionIntegration:

    def test_browse_with_session(self, browser_agent, rate_limiter, tmp_path):
        rate_limiter()
        agent = BrowserAgent(project_root=str(tmp_path))
        agent.start()
        try:
            result = agent.execute({
                "type": "browse",
                "url": TEST_WEBSITES["example"],
                "session": "test_session",
            })

            assert result.success is True

            result2 = agent.execute({
                "type": "browse",
                "url": f"{TEST_WEBSITES['example']}/",
                "session": "test_session",
            })

            assert result2.success is True
        finally:
            agent.stop()


class TestCleanup:

    def test_agent_stops_cleanly(self, browser_agent):
        assert browser_agent._playwright_available is False
        assert browser_agent._browser is None

    def test_agent_status_after_stop(self, tmp_path):
        from src.agents.base_agent import AgentStatus
        agent = BrowserAgent(project_root=str(tmp_path))
        agent.start()
        agent.stop()
        assert agent.status == AgentStatus.OFFLINE
