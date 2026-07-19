# Browser Agent
# Handles headless web browsing, scraping, OCR, and web automation
# Provides structured data extraction and file download capabilities

from .proxy_manager import (
    ProxyManager,
    ProxyInfo,
    ProxyProtocol,
    RotationStrategy,
)

__all__ = [
    "ProxyManager",
    "ProxyInfo",
    "ProxyProtocol",
    "RotationStrategy",
]
