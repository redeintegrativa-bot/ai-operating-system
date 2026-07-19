"""Session manager for Browser Agent with JSON-based persistence."""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_SESSION_DIR = "sessions"
DEFAULT_EXPIRATION_SECONDS = 86400  # 24 hours


class SessionManager:
    """Manages browser session persistence using JSON file storage.

    Supports multiple named sessions, expiration, and cleanup.
    """

    def __init__(
        self,
        storage_dir: Optional[str] = None,
        default_expiration: int = DEFAULT_EXPIRATION_SECONDS,
    ):
        """Initialize session manager.

        Args:
            storage_dir: Directory for session JSON files. Defaults to <project_root>/sessions.
            default_expiration: Default session TTL in seconds.
        """
        self._storage_dir = storage_dir or DEFAULT_SESSION_DIR
        self._default_expiration = default_expiration
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Create storage directory if it doesn't exist."""
        try:
            os.makedirs(self._storage_dir, exist_ok=True)
        except OSError as e:
            logger.error("Failed to create session storage dir: %s", e)

    def _session_path(self, name: str) -> str:
        """Get file path for a named session."""
        safe_name = name.replace("/", "_").replace("\\", "_")
        return os.path.join(self._storage_dir, f"{safe_name}.json")

    def _now(self) -> float:
        """Current timestamp."""
        return time.time()

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------

    def save_session(
        self,
        name: str,
        cookies: Optional[List[Dict[str, Any]]] = None,
        local_storage: Optional[Dict[str, str]] = None,
        session_storage: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expiration: Optional[int] = None,
    ) -> bool:
        """Save session state to a JSON file.

        Args:
            name: Session identifier.
            cookies: List of cookie dicts.
            local_storage: localStorage key-value pairs.
            session_storage: sessionStorage key-value pairs.
            metadata: Additional metadata to store.
            expiration: TTL in seconds from now (uses default if None).

        Returns:
            True if saved successfully.
        """
        now = self._now()
        ttl = expiration if expiration is not None else self._default_expiration

        session_data: Dict[str, Any] = {
            "name": name,
            "created_at": now,
            "updated_at": now,
            "expires_at": now + ttl,
            "cookies": cookies or [],
            "local_storage": local_storage or {},
            "session_storage": session_storage or {},
            "metadata": metadata or {},
        }

        try:
            path = self._session_path(name)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            self._sessions[name] = session_data
            logger.info("Session saved: %s", name)
            return True
        except (OSError, TypeError) as e:
            logger.error("Failed to save session %s: %s", name, e)
            return False

    def load_session(self, name: str) -> Optional[Dict[str, Any]]:
        """Load session state from disk.

        Returns the session dict or None if not found / expired.
        """
        # Check in-memory cache first
        if name in self._sessions:
            session = self._sessions[name]
            if self._is_expired(session):
                logger.info("Cached session expired: %s", name)
                self._sessions.pop(name, None)
                self.delete_session(name)
                return None
            return session

        path = self._session_path(name)
        if not os.path.exists(path):
            logger.debug("Session file not found: %s", name)
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                session = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Failed to load session %s: %s", name, e)
            return None

        if self._is_expired(session):
            logger.info("Session expired on load: %s", name)
            self.delete_session(name)
            return None

        self._sessions[name] = session
        logger.info("Session loaded: %s", name)
        return session

    def update_session(self, name: str, **kwargs: Any) -> bool:
        """Update fields in an existing session.

        Args:
            name: Session identifier.
            **kwargs: Fields to update (cookies, local_storage, session_storage, metadata).

        Returns:
            True if updated, False if session not found.
        """
        session = self.load_session(name)
        if session is None:
            logger.warning("Cannot update non-existent session: %s", name)
            return False

        for key in ("cookies", "local_storage", "session_storage", "metadata"):
            if key in kwargs:
                session[key] = kwargs[key]

        session["updated_at"] = self._now()

        try:
            path = self._session_path(name)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session, f, indent=2, ensure_ascii=False)
            self._sessions[name] = session
            logger.info("Session updated: %s", name)
            return True
        except (OSError, TypeError) as e:
            logger.error("Failed to update session %s: %s", name, e)
            return False

    # ------------------------------------------------------------------
    # Delete / Cleanup
    # ------------------------------------------------------------------

    def delete_session(self, name: str) -> bool:
        """Delete a session file and cache entry."""
        self._sessions.pop(name, None)
        path = self._session_path(name)
        if os.path.exists(path):
            try:
                os.remove(path)
                logger.info("Session deleted: %s", name)
                return True
            except OSError as e:
                logger.error("Failed to delete session %s: %s", name, e)
                return False
        return True

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions (from disk). Returns metadata only."""
        sessions: List[Dict[str, Any]] = []
        if not os.path.isdir(self._storage_dir):
            return sessions

        for fname in os.listdir(self._storage_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._storage_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "name": data.get("name", fname),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "expires_at": data.get("expires_at"),
                    "expired": self._is_expired(data),
                })
            except (OSError, json.JSONDecodeError):
                continue

        return sessions

    def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        removed = 0
        if not os.path.isdir(self._storage_dir):
            return removed

        for fname in list(os.listdir(self._storage_dir)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._storage_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if self._is_expired(data):
                    os.remove(path)
                    name = data.get("name", fname)
                    self._sessions.pop(name, None)
                    removed += 1
                    logger.info("Cleaned up expired session: %s", name)
            except (OSError, json.JSONDecodeError):
                continue

        logger.info("Cleanup removed %d expired sessions", removed)
        return removed

    # ------------------------------------------------------------------
    # Playwright integration helpers
    # ------------------------------------------------------------------

    def save_playwright_state(self, name: str, context: Any, **kwargs: Any) -> bool:
        """Extract and save state from a Playwright BrowserContext.

        Args:
            name: Session identifier.
            context: Playwright BrowserContext object.
            **kwargs: Extra metadata.

        Returns:
            True if saved successfully.
        """
        try:
            cookies = context.cookies()
        except Exception:
            cookies = []
            logger.warning("Failed to extract cookies from Playwright context")

        try:
            page = context.pages[0] if context.pages else context.new_page()
            local_storage = page.evaluate("() => { let s={}; for(let i=0;i<localStorage.length;i++){let k=localStorage.key(i); s[k]=localStorage.getItem(k);} return s; }")
        except Exception:
            local_storage = {}
            logger.warning("Failed to extract localStorage from Playwright context")

        try:
            session_storage = page.evaluate("() => { let s={}; for(let i=0;i<sessionStorage.length;i++){let k=sessionStorage.key(i); s[k]=sessionStorage.getItem(k);} return s; }")
        except Exception:
            session_storage = {}

        return self.save_session(
            name,
            cookies=cookies,
            local_storage=local_storage,
            session_storage=session_storage,
            metadata=kwargs,
        )

    def restore_playwright_state(self, name: str, context: Any) -> bool:
        """Restore session state into a Playwright BrowserContext.

        Args:
            name: Session identifier.
            context: Playwright BrowserContext object.

        Returns:
            True if restored successfully.
        """
        session = self.load_session(name)
        if session is None:
            return False

        # Restore cookies
        try:
            if session.get("cookies"):
                context.add_cookies(session["cookies"])
        except Exception as e:
            logger.warning("Failed to restore cookies: %s", e)

        # Restore localStorage and sessionStorage
        try:
            page = context.pages[0] if context.pages else context.new_page()
            if session.get("local_storage"):
                for key, value in session["local_storage"].items():
                    page.evaluate(
                        f"(k, v) => localStorage.setItem(k, v)",
                        [key, value],
                    )
            if session.get("session_storage"):
                for key, value in session["session_storage"].items():
                    page.evaluate(
                        f"(k, v) => sessionStorage.setItem(k, v)",
                        [key, value],
                    )
        except Exception as e:
            logger.warning("Failed to restore storage: %s", e)

        logger.info("Playwright state restored for session: %s", name)
        return True

    # ------------------------------------------------------------------
    # Requests integration helpers
    # ------------------------------------------------------------------

    def save_requests_cookies(self, name: str, cookies: Any) -> bool:
        """Save cookies from a requests.Session / requests.cookies.RequestsCookieJar.

        Args:
            name: Session identifier.
            cookies: requests cookie jar or list of cookie dicts.

        Returns:
            True if saved.
        """
        try:
            if hasattr(cookies, "get_dict"):
                cookie_list = [
                    {"name": c.name, "value": c.value, "domain": c.domain, "path": c.path}
                    for c in cookies
                ]
            elif isinstance(cookies, list):
                cookie_list = cookies
            else:
                cookie_list = []
        except Exception as e:
            logger.warning("Failed to extract requests cookies: %s", e)
            cookie_list = []

        return self.save_session(name, cookies=cookie_list)

    def restore_requests_cookies(self, name: str, session: Any) -> bool:
        """Restore cookies into a requests.Session.

        Args:
            name: Session identifier.
            session: requests.Session object.

        Returns:
            True if restored.
        """
        data = self.load_session(name)
        if data is None:
            return False

        try:
            for cookie in data.get("cookies", []):
                session.cookies.set(
                    cookie.get("name", ""),
                    cookie.get("value", ""),
                    domain=cookie.get("domain", ""),
                    path=cookie.get("path", "/"),
                )
        except Exception as e:
            logger.warning("Failed to restore requests cookies: %s", e)
            return False

        logger.info("Requests cookies restored for session: %s", name)
        return True

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _is_expired(session: Dict[str, Any]) -> bool:
        """Check if a session has expired."""
        expires_at = session.get("expires_at")
        if expires_at is None:
            return False
        return time.time() > expires_at
