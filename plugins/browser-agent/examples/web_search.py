#!/usr/bin/env python3
"""Example: Automated web search."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.agents.browser_agent import BrowserAgent


def main():
    agent = BrowserAgent(project_root=os.getcwd())

    # Search with Playwright (Google) or requests fallback (DuckDuckGo)
    result = agent.execute({
        "type": "search",
        "query": "python web scraping best practices",
        "num_results": 5,
    })

    if result.success:
        print(f"Query: {result.output['query']}")
        print(f"Results: {len(result.output['results'])}\n")

        for i, r in enumerate(result.output["results"], 1):
            print(f"{i}. {r['title']}")
            print(f"   URL: {r['url']}")
            if r.get("snippet"):
                print(f"   {r['snippet'][:100]}...")
            print()
    else:
        print(f"Error: {result.errors}")

    agent.stop()


if __name__ == "__main__":
    main()
