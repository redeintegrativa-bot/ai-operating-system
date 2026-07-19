#!/usr/bin/env python3
"""Example: Structured scraping with selectors."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.agents.browser_agent import BrowserAgent


def main():
    agent = BrowserAgent(project_root=os.getcwd())

    # Scrape a table from a page
    result = agent.execute({
        "type": "scrape",
        "url": "https://en.wikipedia.org/wiki/List_of_countries_by_population",
        "selector": "table.wikitable",
        "extract": "table",
    })

    if result.success:
        data = result.output.get("data", [])
        print(f"Table rows found: {len(data)}")
        for row in data[:5]:
            print(row)
    else:
        print(f"Error: {result.errors}")

    # Scrape with raw HTML
    html = """
    <html>
    <body>
        <div class="product">
            <h2>Widget A</h2>
            <span class="price">$10.00</span>
        </div>
        <div class="product">
            <h2>Widget B</h2>
            <span class="price">$20.00</span>
        </div>
    </body>
    </html>
    """

    result = agent.execute({
        "type": "scrape",
        "html": html,
        "selector": ".product",
    })

    if result.success:
        print(f"\nProducts found: {result.output['data']}")

    agent.stop()


if __name__ == "__main__":
    main()
