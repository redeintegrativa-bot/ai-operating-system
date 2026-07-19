"""Tests for the ProxyManager class."""

import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from src.agents.browser_agent.proxy_manager import (
    ProxyManager,
    ProxyInfo,
    ProxyProtocol,
    RotationStrategy,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def proxy_manager():
    return ProxyManager()


@pytest.fixture
def proxy_with_proxies():
    proxies = [
        "http://proxy1.example.com:8080",
        "socks5://proxy2.example.com:1080",
        "http://user:pass@proxy3.example.com:8080",
    ]
    return ProxyManager(proxies=proxies)


@pytest.fixture
def proxy_file(tmp_path):
    file_path = tmp_path / "proxies.txt"
    file_path.write_text("""
# Comment line
http://file-proxy1.com:8080
socks5://file-proxy2.com:1080

# Another comment
http://user:pass@file-proxy3.com:8080
""")
    return str(file_path)


# ---------------------------------------------------------------------------
# ProxyInfo Tests
# ---------------------------------------------------------------------------

class TestProxyInfo:
    def test_proxy_info_creation(self):
        proxy = ProxyInfo(
            protocol=ProxyProtocol.HTTP,
            host="example.com",
            port=8080,
        )
        assert proxy.protocol == ProxyProtocol.HTTP
        assert proxy.host == "example.com"
        assert proxy.port == 8080
        assert proxy.username is None
        assert proxy.password is None
        assert proxy.fail_count == 0
    
    def test_proxy_info_str(self):
        proxy = ProxyInfo(
            protocol=ProxyProtocol.HTTP,
            host="example.com",
            port=8080,
        )
        assert str(proxy) == "http://example.com:8080"
    
    def test_proxy_info_str_with_auth(self):
        proxy = ProxyInfo(
            protocol=ProxyProtocol.SOCKS5,
            host="example.com",
            port=1080,
            username="user",
            password="pass",
        )
        assert str(proxy) == "socks5://user:pass@example.com:1080"
    
    def test_proxy_info_is_usable(self):
        proxy = ProxyInfo(
            protocol=ProxyProtocol.HTTP,
            host="example.com",
            port=8080,
            fail_count=0,
        )
        assert proxy.is_usable is True
    
    def test_proxy_info_is_unusable(self):
        proxy = ProxyInfo(
            protocol=ProxyProtocol.HTTP,
            host="example.com",
            port=8080,
            fail_count=3,
        )
        assert proxy.is_usable is False
    
    def test_proxy_info_to_dict(self):
        proxy = ProxyInfo(
            protocol=ProxyProtocol.HTTP,
            host="example.com",
            port=8080,
        )
        d = proxy.to_dict()
        assert "http" in d
        assert "https" in d
        assert d["http"] == "http://example.com:8080"


# ---------------------------------------------------------------------------
# ProxyManager Initialization
# ---------------------------------------------------------------------------

class TestProxyManagerInit:
    def test_empty_init(self, proxy_manager):
        assert proxy_manager.proxy_count == 0
        assert proxy_manager._rotation == RotationStrategy.ROUND_ROBIN
    
    def test_init_with_proxies(self, proxy_with_proxies):
        assert proxy_with_proxies.proxy_count == 3
    
    def test_init_with_rotation(self):
        pm = ProxyManager(rotation=RotationStrategy.RANDOM)
        assert pm._rotation == RotationStrategy.RANDOM
    
    def test_init_with_max_failures(self):
        pm = ProxyManager(max_failures=5)
        assert pm._max_failures == 5


# ---------------------------------------------------------------------------
# Add Proxies
# ---------------------------------------------------------------------------

class TestAddProxies:
    def test_add_single_proxy(self, proxy_manager):
        result = proxy_manager.add_proxy("http://proxy.example.com:8080")
        assert result is True
        assert proxy_manager.proxy_count == 1
    
    def test_add_duplicate_proxy(self, proxy_manager):
        proxy_manager.add_proxy("http://proxy.example.com:8080")
        result = proxy_manager.add_proxy("http://proxy.example.com:8080")
        assert result is False
        assert proxy_manager.proxy_count == 1
    
    def test_add_multiple_proxies(self, proxy_manager):
        proxies = [
            "http://proxy1.com:8080",
            "http://proxy2.com:8080",
            "socks5://proxy3.com:1080",
        ]
        count = proxy_manager.add_proxies(proxies)
        assert count == 3
        assert proxy_manager.proxy_count == 3
    
    def test_add_invalid_proxy(self, proxy_manager):
        result = proxy_manager.add_proxy("invalid://proxy")
        assert result is False
        assert proxy_manager.proxy_count == 0
    
    def test_add_socks4_proxy(self, proxy_manager):
        result = proxy_manager.add_proxy("socks4://proxy.example.com:1080")
        assert result is True
        proxy = proxy_manager._proxies[0]
        assert proxy.protocol == ProxyProtocol.SOCKS4
    
    def test_add_socks5_proxy(self, proxy_manager):
        result = proxy_manager.add_proxy("socks5://proxy.example.com:1080")
        assert result is True
        proxy = proxy_manager._proxies[0]
        assert proxy.protocol == ProxyProtocol.SOCKS5
    
    def test_add_socks5h_proxy(self, proxy_manager):
        result = proxy_manager.add_proxy("socks5h://proxy.example.com:1080")
        assert result is True
        proxy = proxy_manager._proxies[0]
        assert proxy.protocol == ProxyProtocol.SOCKS5


# ---------------------------------------------------------------------------
# Load from File
# ---------------------------------------------------------------------------

class TestLoadFromFile:
    def test_load_from_file(self, proxy_manager, proxy_file):
        count = proxy_manager.load_from_file(proxy_file)
        assert count == 3
        assert proxy_manager.proxy_count == 3
    
    def test_load_from_nonexistent_file(self, proxy_manager):
        count = proxy_manager.load_from_file("/nonexistent/file.txt")
        assert count == 0
        assert proxy_manager.proxy_count == 0
    
    def test_load_from_empty_file(self, proxy_manager, tmp_path):
        file_path = tmp_path / "empty.txt"
        file_path.write_text("")
        count = proxy_manager.load_from_file(str(file_path))
        assert count == 0


# ---------------------------------------------------------------------------
# Environment Variables
# ---------------------------------------------------------------------------

class TestEnvironmentVariables:
    def test_load_from_http_proxy(self, proxy_manager):
        with patch.dict(os.environ, {"HTTP_PROXY": "http://env-proxy.com:8080"}):
            pm = ProxyManager()
            assert pm.proxy_count == 1
    
    def test_load_from_https_proxy(self, proxy_manager):
        with patch.dict(os.environ, {"HTTPS_PROXY": "https://env-proxy.com:8080"}):
            pm = ProxyManager()
            assert pm.proxy_count == 1
    
    def test_load_from_all_proxy(self, proxy_manager):
        with patch.dict(os.environ, {"ALL_PROXY": "socks5://env-proxy.com:1080"}):
            pm = ProxyManager()
            assert pm.proxy_count == 1
    
    def test_dont_duplicate_env_proxy(self):
        with patch.dict(os.environ, {"HTTP_PROXY": "http://env-proxy.com:8080"}):
            pm = ProxyManager(proxies=["http://env-proxy.com:8080"])
            assert pm.proxy_count == 1


# ---------------------------------------------------------------------------
# Get Proxy
# ---------------------------------------------------------------------------

class TestGetProxy:
    def test_get_proxy_empty(self, proxy_manager):
        proxy = proxy_manager.get_proxy()
        assert proxy is None
    
    def test_get_proxy_round_robin(self, proxy_with_proxies):
        p1 = proxy_with_proxies.get_proxy()
        p2 = proxy_with_proxies.get_proxy()
        p3 = proxy_with_proxies.get_proxy()
        
        assert p1 is not None
        assert p2 is not None
        assert p3 is not None
    
    def test_get_proxy_random(self):
        proxies = ["http://proxy1.com:8080", "http://proxy2.com:8080"]
        pm = ProxyManager(proxies=proxies, rotation=RotationStrategy.RANDOM)
        
        proxy = pm.get_proxy()
        assert proxy is not None
    
    def test_get_proxy_skips_unusable(self, proxy_manager):
        proxy_manager.add_proxy("http://proxy1.com:8080")
        proxy_manager.add_proxy("http://proxy2.com:8080")
        
        # Mark first as unusable
        proxy_manager._proxies[0].fail_count = 3
        
        proxy = proxy_manager.get_proxy()
        assert proxy.host == "proxy2.com"
    
    def test_get_proxy_all_unusable(self, proxy_manager):
        proxy_manager.add_proxy("http://proxy1.com:8080")
        proxy_manager._proxies[0].fail_count = 3
        
        proxy = proxy_manager.get_proxy()
        assert proxy is None


# ---------------------------------------------------------------------------
# Mark Failed/Success
# ---------------------------------------------------------------------------

class TestProxyStatus:
    def test_mark_failed(self, proxy_manager):
        proxy_manager.add_proxy("http://proxy.com:8080")
        proxy = proxy_manager._proxies[0]
        
        proxy_manager.mark_failed(proxy)
        assert proxy.fail_count == 1
    
    def test_mark_failed_max(self, proxy_manager):
        proxy_manager.add_proxy("http://proxy.com:8080")
        proxy = proxy_manager._proxies[0]
        
        for _ in range(3):
            proxy_manager.mark_failed(proxy)
        
        assert proxy.is_usable is False
    
    def test_mark_success_resets_failures(self, proxy_manager):
        proxy_manager.add_proxy("http://proxy.com:8080")
        proxy = proxy_manager._proxies[0]
        
        proxy_manager.mark_failed(proxy)
        proxy_manager.mark_failed(proxy)
        proxy_manager.mark_success(proxy)
        
        assert proxy.fail_count == 0
    
    def test_reset_all_failures(self, proxy_manager):
        proxy_manager.add_proxy("http://proxy1.com:8080")
        proxy_manager.add_proxy("http://proxy2.com:8080")
        
        proxy_manager._proxies[0].fail_count = 2
        proxy_manager._proxies[1].fail_count = 1
        
        proxy_manager.reset_failures()
        
        assert proxy_manager._proxies[0].fail_count == 0
        assert proxy_manager._proxies[1].fail_count == 0


# ---------------------------------------------------------------------------
# Get Request Proxies
# ---------------------------------------------------------------------------

class TestGetRequestProxies:
    def test_get_request_proxies(self, proxy_manager):
        proxy_manager.add_proxy("http://proxy.com:8080")
        proxy = proxy_manager._proxies[0]
        
        proxies = proxy_manager.get_request_proxies(proxy)
        assert proxies is not None
        assert "http" in proxies
        assert "https" in proxies
        assert proxies["http"] == "http://proxy.com:8080"
    
    def test_get_request_proxies_auto(self, proxy_manager):
        proxy_manager.add_proxy("http://proxy.com:8080")
        
        proxies = proxy_manager.get_request_proxies()
        assert proxies is not None


# ---------------------------------------------------------------------------
# Get Playwright Proxy
# ---------------------------------------------------------------------------

class TestGetPlaywrightProxy:
    def test_get_playwright_proxy(self, proxy_manager):
        proxy_manager.add_proxy("http://proxy.com:8080")
        proxy = proxy_manager._proxies[0]
        
        config = proxy_manager.get_playwright_proxy(proxy)
        assert config is not None
        assert config["server"] == "http://proxy.com:8080"
    
    def test_get_playwright_proxy_with_auth(self, proxy_manager):
        proxy_manager.add_proxy("http://user:pass@proxy.com:8080")
        proxy = proxy_manager._proxies[0]
        
        config = proxy_manager.get_playwright_proxy(proxy)
        assert config["username"] == "user"
        assert config["password"] == "pass"
    
    def test_get_playwright_proxy_auto(self, proxy_manager):
        proxy_manager.add_proxy("socks5://proxy.com:1080")
        
        config = proxy_manager.get_playwright_proxy()
        assert config["server"] == "socks5://proxy.com:1080"


# ---------------------------------------------------------------------------
# Get SOCKS Proxy
# ---------------------------------------------------------------------------

class TestGetSocksProxy:
    def test_get_socks_proxy(self, proxy_manager):
        proxy_manager.add_proxy("socks5://proxy.com:1080")
        proxy = proxy_manager._proxies[0]
        
        result = proxy_manager.get_socks_proxy(proxy)
        assert result is not None
        assert result[0] == "proxy.com"
        assert result[1] == 1080
    
    def test_get_socks_proxy_with_auth(self, proxy_manager):
        proxy_manager.add_proxy("socks4://user:pass@proxy.com:1080")
        proxy = proxy_manager._proxies[0]
        
        result = proxy_manager.get_socks_proxy(proxy)
        assert result[2] == "user"
        assert result[3] == "pass"
    
    def test_get_socks_proxy_http_returns_none(self, proxy_manager):
        proxy_manager.add_proxy("http://proxy.com:8080")
        proxy = proxy_manager._proxies[0]
        
        result = proxy_manager.get_socks_proxy(proxy)
        assert result is None


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_get_stats(self, proxy_with_proxies):
        stats = proxy_with_proxies.get_stats()
        assert stats["total"] == 3
        assert stats["active"] == 3
        assert stats["rotation"] == "round_robin"
        assert len(stats["proxies"]) == 3
    
    def test_get_stats_with_failed(self, proxy_with_proxies):
        proxy_with_proxies._proxies[0].fail_count = 3
        stats = proxy_with_proxies.get_stats()
        assert stats["active"] == 2


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------

class TestClear:
    def test_clear(self, proxy_with_proxies):
        proxy_with_proxies.clear()
        assert proxy_with_proxies.proxy_count == 0
    
    def test_clear_resets_index(self, proxy_with_proxies):
        proxy_with_proxies.get_proxy()
        proxy_with_proxies.clear()
        assert proxy_with_proxies._current_index == 0


# ---------------------------------------------------------------------------
# Active Count
# ---------------------------------------------------------------------------

class TestActiveCount:
    def test_active_count(self, proxy_with_proxies):
        assert proxy_with_proxies.active_count == 3
    
    def test_active_count_with_failed(self, proxy_with_proxies):
        proxy_with_proxies._proxies[0].fail_count = 3
        proxy_with_proxies._proxies[1].fail_count = 2
        assert proxy_with_proxies.active_count == 2  # fail_count=2 is still < 3, so usable
