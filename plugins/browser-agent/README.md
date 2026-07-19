# Browser Agent Plugin

AIOS marketplace plugin for headless web browsing, scraping, OCR, screenshots, file downloads, and web search with proxy rotation and session persistence.

## Overview

The Browser Agent is a fully-featured web automation agent for the AI Operating System. It provides:

- **Browsing** — Navigate to URLs and extract content (Playwright for JS-rendered pages, requests as fallback)
- **Scraping** — Structured data extraction with CSS/XPath selectors, tables, links, images
- **OCR** — Text extraction from images and PDFs with multiple backends (Tesseract, EasyOCR, PaddleOCR)
- **Screenshots** — Full-page or viewport screenshots via Playwright
- **Downloads** — File download with streaming support
- **Search** — Automated web search (Google via Playwright, DuckDuckGo via requests)
- **JSON Extraction** — Extract structured JSON-LD data and custom selectors from pages
- **Proxy Rotation** — Round-robin or random proxy rotation with failover
- **Session Persistence** — Save/restore cookies, localStorage, sessionStorage across requests
- **Memory Integration** — Store results in AIOS episodic memory

## Installation

### Quick Install

```bash
pip install -r requirements.txt
pip install playwright && playwright install chromium
```

### Full Install (all OCR backends)

```bash
pip install -r requirements.txt
pip install playwright pytesseract easyocr pdf2image
playwright install chromium
apt-get install -y tesseract-ocr poppler-utils
```

### Minimal Install (requests-only, no Playwright)

```bash
pip install -r requirements.txt
```

## Usage

### Programmatic Usage

```python
from src.agents.browser_agent import BrowserAgent, ProxyManager, SessionManager

agent = BrowserAgent(project_root="/path/to/project")

# Browse a URL
result = agent.execute({
    "type": "browse",
    "url": "https://example.com",
    "extract_links": True,
    "extract_meta": True,
})
print(result.output["text"])

# Scrape structured data
result = agent.execute({
    "type": "scrape",
    "url": "https://example.com/data",
    "selector": "table.results",
    "extract": "table",
})
print(result.output["data"])

# OCR from image
result = agent.execute({
    "type": "ocr",
    "file_path": "/path/to/image.png",
    "lang": "eng",
    "backend": "tesseract",
})
print(result.output["text"])

# Take screenshot
result = agent.execute({
    "type": "screenshot",
    "url": "https://example.com",
    "full_page": True,
    "width": 1920,
    "height": 1080,
})
print(result.output["file_path"])

# Download file
result = agent.execute({
    "type": "download",
    "url": "https://example.com/file.zip",
    "output_dir": "/path/to/downloads",
})
print(result.output["file_size"])

# Web search
result = agent.execute({
    "type": "search",
    "query": "python web scraping",
    "num_results": 5,
})
for r in result.output["results"]:
    print(f"{r['title']}: {r['url']}")

# Extract JSON-LD
result = agent.execute({
    "type": "extract_json",
    "url": "https://example.com/product",
    "selectors": {"price": ".price", "name": "h1"},
})
print(result.output["structured_data"])
```

### Proxy Configuration

```python
from src.agents.browser_agent import BrowserAgent, ProxyManager

# Create proxy manager with proxy list
proxy_manager = ProxyManager(
    proxies=[
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
        "socks5://proxy3.example.com:1080",
    ],
    rotation="round_robin",
)

agent = BrowserAgent(project_root="/path/to/project", proxy_manager=proxy_manager)

# Use proxy in task
result = agent.execute({
    "type": "browse",
    "url": "https://example.com",
    "proxy": "http://proxy1.example.com:8080",
})

# Or load from file
proxy_manager.load_from_file("proxies.txt")
```

### Session Persistence

```python
from src.agents.browser_agent import BrowserAgent, SessionManager

session_manager = SessionManager(
    storage_dir="sessions",
    default_expiration=86400,  # 24 hours
)

agent = BrowserAgent(project_root="/path/to/project", session_manager=session_manager)

# Browse with session (saves cookies)
result = agent.execute({
    "type": "browse",
    "url": "https://example.com/login",
    "session": "my_session",
})

# Later: browse with same session (restores cookies)
result = agent.execute({
    "type": "browse",
    "url": "https://example.com/dashboard",
    "session": "my_session",
})

# List sessions
sessions = session_manager.list_sessions()

# Cleanup expired sessions
removed = session_manager.cleanup_expired()
```

### OCR with Different Backends

```python
from src.agents.browser_agent import BrowserAgent

# Auto-select best available backend
agent = BrowserAgent(project_root="/path", ocr_backend="auto")

# Force specific backend
agent = BrowserAgent(project_root="/path", ocr_backend="easyocr")

# Extract from PDF
result = agent.execute({
    "type": "ocr",
    "file_path": "/path/to/document.pdf",
    "lang": "eng",
})

# Extract from image with preprocessing
result = agent.execute({
    "type": "ocr",
    "file_path": "/path/to/image.png",
    "preprocess": "grayscale",
    "backend": "paddleocr",
})
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ocr_backend` | string | `auto` | OCR engine: `auto`, `tesseract`, `easyocr`, `paddleocr` |
| `proxy_rotation` | string | `round_robin` | Rotation: `round_robin`, `random` |
| `proxy_max_failures` | integer | `3` | Max failures before proxy is marked unusable |
| `session_expiration` | integer | `86400` | Session TTL in seconds |
| `session_storage_dir` | string | `sessions` | Directory for session files |
| `user_agent` | string | `Mozilla/5.0 ...` | HTTP User-Agent header |
| `request_timeout` | integer | `30` | HTTP timeout in seconds |
| `playwright_headless` | boolean | `true` | Run Playwright headless |

### Environment Variables

The proxy manager also reads from standard proxy environment variables:

| Variable | Description |
|----------|-------------|
| `HTTP_PROXY` | HTTP proxy URL |
| `HTTPS_PROXY` | HTTPS proxy URL |
| `ALL_PROXY` | All-protocol proxy URL |

## Capabilities

| Capability | Description |
|------------|-------------|
| `browse` | Navigate URLs and extract page content |
| `scrape` | Structured data extraction with selectors |
| `ocr` | Text extraction from images and PDFs |
| `screenshot` | Capture full-page or viewport screenshots |
| `download` | Download files from URLs |
| `search` | Automated web search |
| `extract_json` | Extract JSON-LD and custom structured data |

## Task Types

### browse
Navigate to a URL and extract content.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | URL to browse |
| `extract_links` | bool | `false` | Extract all links |
| `extract_images` | bool | `false` | Extract all images |
| `extract_meta` | bool | `false` | Extract meta tags |
| `proxy` | string | `none` | Proxy URL to use |
| `session` | string | `none` | Session name for persistence |

### scrape
Extract structured data from pages.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | `none` | URL to scrape |
| `html` | string | `none` | Raw HTML content |
| `selector` | string | `""` | CSS/XPath selector |
| `selector_type` | string | `css` | Selector type: `css`, `xpath` |
| `extract` | string | `text` | Extract type: `text`, `table`, `links`, `images` |

### ocr
Extract text from images or PDFs.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | string | `none` | Path to image/PDF |
| `url` | string | `none` | URL to download and OCR |
| `lang` | string | `eng` | Tesseract language code |
| `preprocess` | string | `none` | Preprocessing: `grayscale`, etc. |
| `backend` | string | `none` | Override OCR backend |

### screenshot
Capture a screenshot of a web page.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | URL to screenshot |
| `output_path` | string | `screenshots/` | Output directory |
| `full_page` | bool | `true` | Capture full page |
| `width` | int | `1280` | Viewport width |
| `height` | int | `720` | Viewport height |

### download
Download a file from a URL.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | URL to download |
| `output_dir` | string | `downloads/` | Output directory |
| `filename` | string | auto | Custom filename |

### search
Perform a web search.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search query |
| `num_results` | int | `5` | Number of results |

### extract_json
Extract structured JSON data from pages.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | `none` | URL to fetch |
| `html` | string | `none` | Raw HTML content |
| `selectors` | dict | `none` | Custom CSS selectors to extract |

## Troubleshooting

### Playwright not available
```
Playwright not available: No module named 'playwright'
```
Install Playwright: `pip install playwright && playwright install chromium`

### OCR backends not found
```
No OCR backend available
```
Install at least one OCR backend:
- Tesseract: `pip install pytesseract && apt-get install -y tesseract-ocr`
- EasyOCR: `pip install easyocr`
- PaddleOCR: `pip install paddleocr paddlepaddle`

### Proxy connection failures
```
Connection failed through proxy
```
- Check proxy URL format: `protocol://host:port` or `protocol://user:pass@host:port`
- Verify proxy is reachable: `curl -x http://proxy:port https://example.com`
- Check `proxy_max_failures` setting (default: 3)

### Session not restoring
- Check session name matches between save and load
- Verify session hasn't expired (`session_expiration` setting)
- Check `sessions/` directory exists and is writable

### PDF OCR fails
```
pdf2image not installed; PDF OCR limited
```
Install: `pip install pdf2image && apt-get install -y poppler-utils`

## Examples

See the `examples/` directory for complete working examples:

- `basic_browse.py` — Browse URLs and extract content
- `scraper.py` — Structured data extraction
- `ocr_extract.py` — OCR from images and PDFs
- `proxy_usage.py` — Proxy rotation and configuration
- `session_persistence.py` — Session save/restore
- `web_search.py` — Automated web search

## License

MIT License — see [LICENSE](LICENSE) for details.
