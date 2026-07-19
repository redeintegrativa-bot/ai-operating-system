#!/usr/bin/env python3
"""Example: Proxy rotation and configuration."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.agents.browser_agent import BrowserAgent, ProxyManager


def main():
    # Create proxy manager with multiple proxies
    proxy_manager = ProxyManager(
        proxies=[
            # Add your proxy URLs here
            # "http://proxy1.example.com:8080",
            # "http://user:pass@proxy2.example.com:8080",
            # "socks5://proxy3.example.com:1080",
        ],
        rotation="round_robin",  # or "random"
        max_failures=3,
    )

    # Also loads from environment: HTTP_PROXY, HTTPS_PROXY, ALL_PROXY
    print(f"Proxy pool: {proxy_manager.proxy_count} total, {proxy_manager.active_count} active")

    agent = BrowserAgent(
        project_root=os.getcwd(),
        proxy_manager=proxy_manager,
    )

    # Browse with a specific proxy
    result = agent.execute({
        "type": "browse",
        "url": "https://httpbin.org/ip",
        "proxy": "http://your-proxy:8080",  # optional: use specific proxy
    })

    if result.success:
        print(f"IP visible to server: {result.output['text'][:200]}")
    else:
        print(f"Error: {result.errors}")

    # Get proxy stats
    stats = proxy_manager.get_stats()
    print(f"\nProxy stats: {stats}")

    # Load proxies from file
    # proxy_manager.load_from_file("proxies.txt")

    # Reset all failure counts
    proxy_manager.reset_failures()

    agent.stop()


if __name__ == "__main__":
    main()
