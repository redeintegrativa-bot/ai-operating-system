"""Suggestion Inbox - Agent-generated suggestions for user review.

Agents can generate suggestions, research topics, strategic questions,
and mission ideas. All go to an inbox for human review.
No automatic execution - user must approve/reject each suggestion.
"""

import json
import os
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

# Import from kernel (will be created in parallel)
from src.core.kernel import Suggestion


logger = logging.getLogger("suggestions")


class SuggestionInbox:
    """Manages suggestions from agents with review workflow."""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self._suggestions: Dict[str, Suggestion] = {}
        self._data_dir = os.path.join(project_root, ".aios", "suggestions")
        os.makedirs(self._data_dir, exist_ok=True)
        self._load()

    def _data_file(self) -> str:
        return os.path.join(self._data_dir, "inbox.json")

    def _load(self):
        path = self._data_file()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for item in data:
                    s = Suggestion(**item)
                    self._suggestions[s.id] = s
                logger.info("Loaded %d suggestions", len(self._suggestions))
            except Exception as e:
                logger.error("Failed to load suggestions: %s", e)

    def _save(self):
        path = self._data_file()
        data = [asdict(s) for s in self._suggestions.values()]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def add(self, suggestion: Suggestion) -> Suggestion:
        """Add a new suggestion to the inbox."""
        self._suggestions[suggestion.id] = suggestion
        self._save()
        logger.info("New suggestion from '%s': %s", suggestion.agent_name, suggestion.title)
        return suggestion

    def get(self, suggestion_id: str) -> Optional[Suggestion]:
        return self._suggestions.get(suggestion_id)

    def get_pending(self) -> List[Suggestion]:
        """Get all pending suggestions for review."""
        return [s for s in self._suggestions.values() if s.status == "pending"]

    def get_by_agent(self, agent_name: str) -> List[Suggestion]:
        return [s for s in self._suggestions.values() if s.agent_name == agent_name]

    def get_by_type(self, suggestion_type: str) -> List[Suggestion]:
        return [s for s in self._suggestions.values() if s.suggestion_type == suggestion_type]

    def get_by_status(self, status: str) -> List[Suggestion]:
        return [s for s in self._suggestions.values() if s.status == status]

    def get_by_priority(self, priority: str) -> List[Suggestion]:
        return [s for s in self._suggestions.values() if s.priority == priority]

    def get_all(self) -> List[Suggestion]:
        return list(self._suggestions.values())

    def approve(self, suggestion_id: str) -> bool:
        """Approve a suggestion (user reviewed)."""
        s = self._suggestions.get(suggestion_id)
        if s and s.status == "pending":
            s.status = "approved"
            s.reviewed_at = datetime.now(timezone.utc).isoformat()
            self._save()
            logger.info("Suggestion '%s' approved", s.title)
            return True
        return False

    def reject(self, suggestion_id: str, reason: str = "") -> bool:
        """Reject a suggestion."""
        s = self._suggestions.get(suggestion_id)
        if s and s.status == "pending":
            s.status = "rejected"
            s.reviewed_at = datetime.now(timezone.utc).isoformat()
            if reason:
                s.metadata["rejection_reason"] = reason
            self._save()
            logger.info("Suggestion '%s' rejected: %s", s.title, reason)
            return True
        return False

    def mark_executed(self, suggestion_id: str) -> bool:
        """Mark a suggestion as executed."""
        s = self._suggestions.get(suggestion_id)
        if s and s.status == "approved":
            s.status = "executed"
            self._save()
            return True
        return False

    def dismiss(self, suggestion_id: str) -> bool:
        """Dismiss/remove a suggestion."""
        if suggestion_id in self._suggestions:
            del self._suggestions[suggestion_id]
            self._save()
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get inbox statistics."""
        all_s = list(self._suggestions.values())
        return {
            "total": len(all_s),
            "pending": len([s for s in all_s if s.status == "pending"]),
            "approved": len([s for s in all_s if s.status == "approved"]),
            "rejected": len([s for s in all_s if s.status == "rejected"]),
            "executed": len([s for s in all_s if s.status == "executed"]),
            "by_type": {
                t: len([s for s in all_s if s.suggestion_type == t])
                for t in ["improvement", "research", "question", "mission"]
            },
            "by_priority": {
                p: len([s for s in all_s if s.priority == p])
                for p in ["low", "medium", "high"]
            },
        }

    def get_recent(self, limit: int = 10) -> List[Suggestion]:
        """Get most recent suggestions."""
        sorted_s = sorted(self._suggestions.values(),
                         key=lambda s: s.created_at, reverse=True)
        return sorted_s[:limit]


class SuggestionGenerator:
    """Generates suggestions based on agent observations.

    This is a template/placeholder for future AI-powered suggestion generation.
    Currently provides rule-based suggestions that agents can use.
    """

    @staticmethod
    def create_improvement(agent_name: str, domain: str,
                          title: str, description: str,
                          priority: str = "medium") -> Suggestion:
        """Create an improvement suggestion."""
        return Suggestion(
            agent_name=agent_name,
            title=title,
            description=description,
            suggestion_type="improvement",
            domain=domain,
            priority=priority,
        )

    @staticmethod
    def create_research(agent_name: str, domain: str,
                       topic: str, question: str,
                       priority: str = "medium") -> Suggestion:
        """Create a research suggestion."""
        return Suggestion(
            agent_name=agent_name,
            title=f"Research: {topic}",
            description=question,
            suggestion_type="research",
            domain=domain,
            priority=priority,
            metadata={"research_topic": topic},
        )

    @staticmethod
    def create_question(agent_name: str, domain: str,
                       question: str, context: str = "",
                       priority: str = "low") -> Suggestion:
        """Create a strategic question."""
        return Suggestion(
            agent_name=agent_name,
            title=f"Question: {question[:60]}",
            description=question,
            suggestion_type="question",
            domain=domain,
            priority=priority,
            metadata={"context": context},
        )

    @staticmethod
    def create_mission_idea(agent_name: str, domain: str,
                           title: str, description: str,
                           priority: str = "medium") -> Suggestion:
        """Create a mission idea."""
        return Suggestion(
            agent_name=agent_name,
            title=title,
            description=description,
            suggestion_type="mission",
            domain=domain,
            priority=priority,
        )
