# Changelog

All notable changes to the Browser Agent plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-07-19

### Added
- Initial marketplace plugin release
- Browser Agent with Playwright and requests fallback
- Page scraping with CSS/XPath selectors
- OCR engine with Tesseract, EasyOCR, and PaddleOCR backends
- Auto-selection and fallback between OCR backends
- Screenshot capture via Playwright
- File download with streaming
- Web search (Google via Playwright, DuckDuckGo via requests)
- JSON-LD and structured data extraction
- Proxy manager with round-robin and random rotation
- Proxy failover with configurable max failures
- Session persistence with JSON file storage
- Playwright BrowserContext state save/restore
- Requests cookie save/restore
- Session expiration and cleanup
- Memory integration for storing results
- Environment variable proxy loading (HTTP_PROXY, HTTPS_PROXY, ALL_PROXY)
- Proxy file loading support
- Image preprocessing for OCR
- Plugin manifest with configuration options
- Complete documentation and examples
