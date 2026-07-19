"""Tests for the Suggestion Inbox module (SuggestionInbox, SuggestionGenerator)."""

import os
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from src.core.kernel import Suggestion
from src.core.suggestions import SuggestionInbox, SuggestionGenerator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_project(tmp_path):
    return str(tmp_path)


@pytest.fixture
def inbox(tmp_project):
    return SuggestionInbox(tmp_project)


@pytest.fixture
def sample_suggestion():
    return Suggestion(
        agent_name="engineer",
        title="Refactor database layer",
        description="Move from raw SQL to ORM for better maintainability.",
        suggestion_type="improvement",
        domain="database",
        priority="high",
    )


@pytest.fixture
def populated_inbox(inbox, sample_suggestion):
    inbox.add(sample_suggestion)
    inbox.add(Suggestion(
        agent_name="researcher",
        title="Research: Vector databases",
        description="Should we migrate to pgvector?",
        suggestion_type="research",
        domain="ai",
        priority="medium",
    ))
    inbox.add(Suggestion(
        agent_name="engineer",
        title="Question: Use Pydantic v2?",
        description="Should we upgrade to Pydantic v2 across the board?",
        suggestion_type="question",
        domain="core",
        priority="low",
    ))
    inbox.add(Suggestion(
        agent_name="architect",
        title="Mission: Migrate to microservices",
        description="Plan the migration from monolith to microservices.",
        suggestion_type="mission",
        domain="infrastructure",
        priority="high",
    ))
    return inbox


# ===================================================================
# SuggestionInbox - Initialization
# ===================================================================

class TestInboxInit:
    def test_creates_data_dir(self, tmp_project):
        inbox = SuggestionInbox(tmp_project)
        expected_dir = os.path.join(tmp_project, ".aios", "suggestions")
        assert os.path.isdir(expected_dir)

    def test_data_file_path(self, tmp_project):
        inbox = SuggestionInbox(tmp_project)
        expected = os.path.join(tmp_project, ".aios", "suggestions", "inbox.json")
        assert inbox._data_file() == expected

    def test_loads_existing_data(self, tmp_project, sample_suggestion):
        inbox1 = SuggestionInbox(tmp_project)
        inbox1.add(sample_suggestion)
        inbox2 = SuggestionInbox(tmp_project)
        loaded = inbox2.get(sample_suggestion.id)
        assert loaded is not None
        assert loaded.title == "Refactor database layer"

    def test_ignores_missing_file(self, tmp_project):
        inbox = SuggestionInbox(tmp_project)
        assert inbox.get_all() == []

    def test_ignores_corrupt_json(self, tmp_project):
        data_dir = os.path.join(tmp_project, ".aios", "suggestions")
        os.makedirs(data_dir, exist_ok=True)
        with open(os.path.join(data_dir, "inbox.json"), "w") as f:
            f.write("not valid json")
        inbox = SuggestionInbox(tmp_project)
        assert inbox.get_all() == []


# ===================================================================
# SuggestionInbox - Add / Get
# ===================================================================

class TestInboxAddGet:
    def test_add_returns_suggestion(self, inbox, sample_suggestion):
        result = inbox.add(sample_suggestion)
        assert result is sample_suggestion

    def test_add_persists_to_disk(self, inbox, sample_suggestion):
        inbox.add(sample_suggestion)
        assert os.path.exists(inbox._data_file())
        with open(inbox._data_file()) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["title"] == "Refactor database layer"

    def test_get_existing(self, inbox, sample_suggestion):
        inbox.add(sample_suggestion)
        result = inbox.get(sample_suggestion.id)
        assert result is not None
        assert result.title == "Refactor database layer"

    def test_get_nonexistent(self, inbox):
        assert inbox.get("nonexistent-id") is None

    def test_get_all(self, populated_inbox):
        assert len(populated_inbox.get_all()) == 4

    def test_get_pending(self, populated_inbox):
        pending = populated_inbox.get_pending()
        assert len(pending) == 4

    def test_get_pending_after_approve(self, populated_inbox):
        s = populated_inbox.get_all()[0]
        populated_inbox.approve(s.id)
        assert len(populated_inbox.get_pending()) == 3


# ===================================================================
# SuggestionInbox - Filtering
# ===================================================================

class TestInboxFiltering:
    def test_get_by_agent(self, populated_inbox):
        engineer_suggestions = populated_inbox.get_by_agent("engineer")
        assert len(engineer_suggestions) == 2
        for s in engineer_suggestions:
            assert s.agent_name == "engineer"

    def test_get_by_agent_none(self, populated_inbox):
        assert populated_inbox.get_by_agent("ghost") == []

    def test_get_by_type(self, populated_inbox):
        research = populated_inbox.get_by_type("research")
        assert len(research) == 1
        assert research[0].suggestion_type == "research"

    def test_get_by_status(self, populated_inbox):
        populated_inbox.approve(populated_inbox.get_all()[0].id)
        approved = populated_inbox.get_by_status("approved")
        assert len(approved) == 1

    def test_get_by_priority(self, populated_inbox):
        high = populated_inbox.get_by_priority("high")
        assert len(high) == 2
        for s in high:
            assert s.priority == "high"

    def test_get_by_priority_none(self, populated_inbox):
        assert populated_inbox.get_by_priority("critical") == []

    def test_get_recent(self, populated_inbox):
        recent = populated_inbox.get_recent(limit=2)
        assert len(recent) == 2

    def test_get_recent_all(self, populated_inbox):
        all_s = populated_inbox.get_recent(limit=100)
        assert len(all_s) == 4


# ===================================================================
# SuggestionInbox - Approve / Reject / Execute / Dismiss
# ===================================================================

class TestInboxReview:
    def test_approve_updates_status(self, inbox, sample_suggestion):
        inbox.add(sample_suggestion)
        assert inbox.approve(sample_suggestion.id) is True
        s = inbox.get(sample_suggestion.id)
        assert s.status == "approved"
        assert s.reviewed_at is not None

    def test_approve_already_rejected(self, inbox, sample_suggestion):
        inbox.add(sample_suggestion)
        inbox.reject(sample_suggestion.id, reason="not needed")
        assert inbox.approve(sample_suggestion.id) is False

    def test_reject_updates_status(self, inbox, sample_suggestion):
        inbox.add(sample_suggestion)
        assert inbox.reject(sample_suggestion.id, reason="not now") is True
        s = inbox.get(sample_suggestion.id)
        assert s.status == "rejected"
        assert s.metadata["rejection_reason"] == "not now"

    def test_reject_without_reason(self, inbox, sample_suggestion):
        inbox.add(sample_suggestion)
        assert inbox.reject(sample_suggestion.id) is True
        s = inbox.get(sample_suggestion.id)
        assert s.status == "rejected"
        assert "rejection_reason" not in s.metadata

    def test_approve_nonexistent(self, inbox):
        assert inbox.approve("bad-id") is False

    def test_reject_nonexistent(self, inbox):
        assert inbox.reject("bad-id") is False

    def test_mark_executed(self, inbox, sample_suggestion):
        inbox.add(sample_suggestion)
        inbox.approve(sample_suggestion.id)
        assert inbox.mark_executed(sample_suggestion.id) is True
        s = inbox.get(sample_suggestion.id)
        assert s.status == "executed"

    def test_mark_executed_from_pending_fails(self, inbox, sample_suggestion):
        inbox.add(sample_suggestion)
        assert inbox.mark_executed(sample_suggestion.id) is False

    def test_dismiss_removes(self, inbox, sample_suggestion):
        inbox.add(sample_suggestion)
        assert inbox.dismiss(sample_suggestion.id) is True
        assert inbox.get(sample_suggestion.id) is None

    def test_dismiss_nonexistent(self, inbox):
        assert inbox.dismiss("bad-id") is False

    def test_dismiss_reduces_count(self, populated_inbox):
        sid = populated_inbox.get_all()[0].id
        populated_inbox.dismiss(sid)
        assert len(populated_inbox.get_all()) == 3

    def test_approve_persists(self, tmp_project, sample_suggestion):
        inbox1 = SuggestionInbox(tmp_project)
        inbox1.add(sample_suggestion)
        inbox1.approve(sample_suggestion.id)
        inbox2 = SuggestionInbox(tmp_project)
        s = inbox2.get(sample_suggestion.id)
        assert s.status == "approved"


# ===================================================================
# SuggestionInbox - Stats
# ===================================================================

class TestInboxStats:
    def test_stats_empty(self, inbox):
        stats = inbox.get_stats()
        assert stats["total"] == 0
        assert stats["pending"] == 0
        assert stats["approved"] == 0
        assert stats["rejected"] == 0
        assert stats["executed"] == 0

    def test_stats_counts(self, populated_inbox):
        all_s = populated_inbox.get_all()
        populated_inbox.approve(all_s[0].id)
        populated_inbox.reject(all_s[1].id, reason="nope")
        populated_inbox.approve(all_s[2].id)
        populated_inbox.mark_executed(all_s[2].id)
        stats = populated_inbox.get_stats()
        assert stats["total"] == 4
        assert stats["pending"] == 1
        assert stats["approved"] == 1
        assert stats["rejected"] == 1
        assert stats["executed"] == 1

    def test_stats_by_type(self, populated_inbox):
        stats = populated_inbox.get_stats()
        assert stats["by_type"]["improvement"] == 1
        assert stats["by_type"]["research"] == 1
        assert stats["by_type"]["question"] == 1
        assert stats["by_type"]["mission"] == 1

    def test_stats_by_priority(self, populated_inbox):
        stats = populated_inbox.get_stats()
        assert stats["by_priority"]["low"] == 1
        assert stats["by_priority"]["medium"] == 1
        assert stats["by_priority"]["high"] == 2


# ===================================================================
# SuggestionGenerator
# ===================================================================

class TestSuggestionGenerator:
    def test_create_improvement(self):
        s = SuggestionGenerator.create_improvement(
            agent_name="engineer",
            domain="database",
            title="Add connection pooling",
            description="Implement connection pooling to reduce latency.",
            priority="high",
        )
        assert s.agent_name == "engineer"
        assert s.domain == "database"
        assert s.title == "Add connection pooling"
        assert s.suggestion_type == "improvement"
        assert s.priority == "high"
        assert s.status == "pending"

    def test_create_improvement_default_priority(self):
        s = SuggestionGenerator.create_improvement(
            agent_name="engineer",
            domain="core",
            title="Clean up logs",
            description="Remove debug logs from production.",
        )
        assert s.priority == "medium"

    def test_create_research(self):
        s = SuggestionGenerator.create_research(
            agent_name="researcher",
            domain="ai",
            topic="GraphQL vs REST",
            question="Should we adopt GraphQL for our public API?",
            priority="medium",
        )
        assert s.title == "Research: GraphQL vs REST"
        assert s.description == "Should we adopt GraphQL for our public API?"
        assert s.suggestion_type == "research"
        assert s.metadata["research_topic"] == "GraphQL vs REST"

    def test_create_question(self):
        s = SuggestionGenerator.create_question(
            agent_name="architect",
            domain="infrastructure",
            question="Should we adopt Kubernetes?",
            context="Team is growing, monolith is slowing us down.",
            priority="low",
        )
        assert s.title.startswith("Question: Should we adopt")
        assert s.suggestion_type == "question"
        assert s.metadata["context"] == "Team is growing, monolith is slowing us down."

    def test_create_question_default_context(self):
        s = SuggestionGenerator.create_question(
            agent_name="architect",
            domain="infrastructure",
            question="Should we adopt Kubernetes?",
        )
        assert s.metadata["context"] == ""

    def test_create_mission_idea(self):
        s = SuggestionGenerator.create_mission_idea(
            agent_name="architect",
            domain="infrastructure",
            title="Cloud migration",
            description="Move on-prem services to AWS.",
            priority="high",
        )
        assert s.title == "Cloud migration"
        assert s.suggestion_type == "mission"
        assert s.priority == "high"

    def test_create_mission_idea_default_priority(self):
        s = SuggestionGenerator.create_mission_idea(
            agent_name="architect",
            domain="infrastructure",
            title="Refactor CI/CD",
            description="Move from Jenkins to GitHub Actions.",
        )
        assert s.priority == "medium"

    def test_all_generators_set_agent_name(self):
        s1 = SuggestionGenerator.create_improvement("eng", "db", "t", "d")
        s2 = SuggestionGenerator.create_research("res", "ai", "t", "q")
        s3 = SuggestionGenerator.create_question("arch", "infra", "q?")
        s4 = SuggestionGenerator.create_mission_idea("lead", "ops", "t", "d")
        for s in [s1, s2, s3, s4]:
            assert s.agent_name != ""
            assert s.status == "pending"
            assert s.id is not None
