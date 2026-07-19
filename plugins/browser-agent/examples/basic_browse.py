#!/usr/bin/env python3
"""Example: Basic browsing with the Browser Agent."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.agents.browser_agent import BrowserAgent


def main():
    agent = BrowserAgent(project_root=os.getcwd())

    # Browse a URL and extract content
    result = agent.execute({
        "type": "browse",
        "url": "https://example.com",
        "extract_links": True,
        "extract_meta": True,
    })

    if result.success:
        print(f"Title: {result.output['title']}")
        print(f"Text length: {len(result.output['text'])} chars")
        print(f"Links found: {len(result.output.get('links', []))}")
        print(f"Meta tags: {result.output.get('meta', {})}")
        print(f"\nFirst 500 chars of text:\n{result.output['text'][:500]}")
    else:
        print(f"Error: {result.errors}")

    agent.stop()


if __name__ == "__main__":
    main()
