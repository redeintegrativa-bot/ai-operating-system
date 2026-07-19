# Browser Agent
# Handles headless web browsing, scraping, OCR, and web automation
# Provides structured data extraction and file download capabilities

from .proxy_manager import (
    ProxyManager,
    ProxyInfo,
    ProxyProtocol,
    RotationStrategy,
)
from .session_manager import SessionManager

__all__ = [
    "ProxyManager",
    "ProxyInfo",
    "ProxyProtocol",
    "RotationStrategy",
    "SessionManager",
]
