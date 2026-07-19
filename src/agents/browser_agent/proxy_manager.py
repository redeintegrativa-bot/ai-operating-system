"""Proxy manager for Browser Agent with rotation and failover support."""

import os
import random
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ProxyProtocol(Enum):
    """Supported proxy protocols."""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class RotationStrategy(Enum):
    """Proxy rotation strategies."""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"


@dataclass
class ProxyInfo:
    """Proxy configuration data."""
    protocol: ProxyProtocol
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    fail_count: int = 0
    last_used: float = 0.0
    
    def __str__(self) -> str:
        if self.username and self.password:
            return f"{self.protocol.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol.value}://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for requests/playwright."""
        return {
            "http": str(self),
            "https": str(self),
        }
    
    @property
    def is_usable(self) -> bool:
        """Check if proxy is usable (max 3 failures)."""
        return self.fail_count < 3


class ProxyManager:
    """Manages proxy pool with rotation and failover."""
    
    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        proxy_file: Optional[str] = None,
        rotation: RotationStrategy = RotationStrategy.ROUND_ROBIN,
        max_failures: int = 3,
    ):
        """Initialize proxy manager.
        
        Args:
            proxies: List of proxy URLs
            proxy_file: Path to file with proxies (one per line)
            rotation: Rotation strategy
            max_failures: Max failures before marking proxy as unusable
        """
        self._proxies: List[ProxyInfo] = []
        self._rotation = rotation
        self._max_failures = max_failures
        self._current_index = 0
        
        # Load proxies
        if proxies:
            self.add_proxies(proxies)
        if proxy_file:
            self.load_from_file(proxy_file)
        
        # Also check environment variables
        self._load_from_env()
    
    def _load_from_env(self) -> None:
        """Load proxies from environment variables."""
        env_vars = [
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
        ]
        
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                try:
                    proxy = self._parse_proxy(value)
                    if proxy and not self._proxy_exists(proxy):
                        self._proxies.append(proxy)
                        logger.debug(f"Loaded proxy from {var}: {proxy.host}:{proxy.port}")
                except Exception as e:
                    logger.warning(f"Failed to parse proxy from {var}: {e}")
    
    def _parse_proxy(self, proxy_url: str) -> Optional[ProxyInfo]:
        """Parse proxy URL string into ProxyInfo."""
        try:
            # Handle socks5h:// which is common
            url = proxy_url
            if url.startswith("socks5h://"):
                url = "socks5://" + url[9:]
            
            parsed = urlparse(url)
            
            if not parsed.hostname or not parsed.port:
                logger.warning(f"Invalid proxy URL: {proxy_url}")
                return None
            
            # Determine protocol
            scheme = parsed.scheme.lower()
            if scheme in ("http", "https"):
                protocol = ProxyProtocol.HTTP
            elif scheme == "socks4":
                protocol = ProxyProtocol.SOCKS4
            elif scheme in ("socks5", "socks5h"):
                protocol = ProxyProtocol.SOCKS5
            else:
                logger.warning(f"Unsupported protocol: {scheme}")
                return None
            
            return ProxyInfo(
                protocol=protocol,
                host=parsed.hostname,
                port=parsed.port,
                username=parsed.username,
                password=parsed.password,
            )
        except Exception as e:
            logger.error(f"Failed to parse proxy: {proxy_url}: {e}")
            return None
    
    def _proxy_exists(self, proxy: ProxyInfo) -> bool:
        """Check if proxy already exists in pool."""
        return any(
            p.host == proxy.host and p.port == proxy.port
            for p in self._proxies
        )
    
    def add_proxy(self, proxy_url: str) -> bool:
        """Add a single proxy.
        
        Args:
            proxy_url: Proxy URL string
            
        Returns:
            True if added successfully
        """
        proxy = self._parse_proxy(proxy_url)
        if proxy is None:
            return False
        
        if self._proxy_exists(proxy):
            logger.debug(f"Proxy already exists: {proxy.host}:{proxy.port}")
            return False
        
        self._proxies.append(proxy)
        logger.info(f"Added proxy: {proxy.host}:{proxy.port}")
        return True
    
    def add_proxies(self, proxy_urls: List[str]) -> int:
        """Add multiple proxies.
        
        Args:
            proxy_urls: List of proxy URL strings
            
        Returns:
            Number of proxies added
        """
        count = 0
        for url in proxy_urls:
            if self.add_proxy(url):
                count += 1
        return count
    
    def load_from_file(self, file_path: str) -> int:
        """Load proxies from file.
        
        Args:
            file_path: Path to proxy file (one proxy per line)
            
        Returns:
            Number of proxies loaded
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Proxy file not found: {file_path}")
            return 0
        
        try:
            content = path.read_text()
            proxies = []
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    proxies.append(line)
            
            count = self.add_proxies(proxies)
            logger.info(f"Loaded {count} proxies from {file_path}")
            return count
        except Exception as e:
            logger.error(f"Failed to load proxies from {file_path}: {e}")
            return 0
    
    @property
    def proxy_count(self) -> int:
        """Get number of proxies in pool."""
        return len(self._proxies)
    
    @property
    def active_count(self) -> int:
        """Get number of active proxies."""
        return sum(1 for p in self._proxies if p.is_usable)
    
    def get_proxy(self) -> Optional[ProxyInfo]:
        """Get next proxy based on rotation strategy.
        
        Returns:
            Next proxy or None if no proxies available
        """
        active = [p for p in self._proxies if p.is_usable]
        if not active:
            logger.warning("No active proxies available")
            return None
        
        if self._rotation == RotationStrategy.RANDOM:
            return random.choice(active)
        
        # Round-robin
        proxy = active[self._current_index % len(active)]
        self._current_index = (self._current_index + 1) % len(active)
        return proxy
    
    def mark_failed(self, proxy: ProxyInfo) -> None:
        """Mark proxy as failed.
        
        Args:
            proxy: The failed proxy
        """
        proxy.fail_count += 1
        logger.warning(
            f"Proxy failed ({proxy.fail_count}/{self._max_failures}): "
            f"{proxy.host}:{proxy.port}"
        )
        
        if proxy.fail_count >= self._max_failures:
            logger.error(f"Proxy marked unusable: {proxy.host}:{proxy.port}")
    
    def mark_success(self, proxy: ProxyInfo) -> None:
        """Mark proxy as successful (reset failure count).
        
        Args:
            proxy: The successful proxy
        """
        proxy.fail_count = 0
    
    def get_request_proxies(self, proxy: Optional[ProxyInfo] = None) -> Optional[Dict[str, str]]:
        """Get proxies dict for requests library.
        
        Args:
            proxy: Specific proxy to use, or None for next in rotation
            
        Returns:
            Proxies dict or None
        """
        if proxy is None:
            proxy = self.get_proxy()
        
        if proxy is None:
            return None
        
        return {
            "http": str(proxy),
            "https": str(proxy),
        }
    
    def get_playwright_proxy(self, proxy: Optional[ProxyInfo] = None) -> Optional[Dict[str, str]]:
        """Get proxy config for Playwright.
        
        Args:
            proxy: Specific proxy to use, or None for next in rotation
            
        Returns:
            Playwright proxy config or None
        """
        if proxy is None:
            proxy = self.get_proxy()
        
        if proxy is None:
            return None
        
        config = {
            "server": f"{proxy.protocol.value}://{proxy.host}:{proxy.port}",
        }
        
        if proxy.username and proxy.password:
            config["username"] = proxy.username
            config["password"] = proxy.password
        
        return config
    
    def get_socks_proxy(self, proxy: Optional[ProxyInfo] = None) -> Optional[Tuple[str, int, str, str]]:
        """Get SOCKS proxy for PySocks.
        
        Args:
            proxy: Specific proxy to use, or None for next in rotation
            
        Returns:
            Tuple of (host, port, username, password) or None
        """
        if proxy is None:
            proxy = self.get_proxy()
        
        if proxy is None:
            return None
        
        if proxy.protocol not in (ProxyProtocol.SOCKS4, ProxyProtocol.SOCKS5):
            return None
        
        return (
            proxy.host,
            proxy.port,
            proxy.username or "",
            proxy.password or "",
        )
    
    def reset_failures(self) -> None:
        """Reset all proxy failure counts."""
        for proxy in self._proxies:
            proxy.fail_count = 0
        logger.info("Reset all proxy failures")
    
    def clear(self) -> None:
        """Remove all proxies."""
        self._proxies.clear()
        self._current_index = 0
        logger.info("Cleared proxy pool")
    
    def get_stats(self) -> Dict:
        """Get proxy pool statistics."""
        return {
            "total": len(self._proxies),
            "active": self.active_count,
            "rotation": self._rotation.value,
            "proxies": [
                {
                    "host": p.host,
                    "port": p.port,
                    "protocol": p.protocol.value,
                    "failures": p.fail_count,
                    "usable": p.is_usable,
                }
                for p in self._proxies
            ],
        }
