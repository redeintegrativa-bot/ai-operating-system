#!/usr/bin/env python3
"""Example: Session persistence across requests."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.agents.browser_agent import BrowserAgent, SessionManager


def main():
    session_manager = SessionManager(
        storage_dir="sessions",
        default_expiration=3600,  # 1 hour
    )

    agent = BrowserAgent(
        project_root=os.getcwd(),
        session_manager=session_manager,
    )

    # First request: creates session and saves cookies
    print("=== First request (creates session) ===")
    result = agent.execute({
        "type": "browse",
        "url": "https://httpbin.org/cookies/set?session_id=abc123",
        "session": "demo_session",
    })

    if result.success:
        print(f"Session saved with cookies")

    # Second request: restores cookies from session
    print("\n=== Second request (restores session) ===")
    result = agent.execute({
        "type": "browse",
        "url": "https://httpbin.org/cookies",
        "session": "demo_session",
    })

    if result.success:
        print(f"Cookies from session: {result.output['text'][:200]}")

    # List all sessions
    print("\n=== Active sessions ===")
    sessions = session_manager.list_sessions()
    for s in sessions:
        status = "expired" if s["expired"] else "active"
        print(f"  {s['name']}: {status}")

    # Cleanup expired sessions
    removed = session_manager.cleanup_expired()
    print(f"\nCleaned up {removed} expired sessions")

    # Manual session save
    session_manager.save_session(
        name="manual_session",
        cookies=[
            {"name": "token", "value": "xyz789", "domain": ".example.com", "path": "/"},
        ],
        metadata={"source": "manual"},
    )

    agent.stop()


if __name__ == "__main__":
    main()
