"""Tests for the Kernel API module (KernelAPI, generate_api_json)."""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, PropertyMock

from src.core.kernel import (
    AIOSKernel, AgentConfig, AgentMode, AgentHealth,
    HeartbeatMonitor, Scheduler, ScheduledMission, Suggestion,
    create_default_kernel,
)
from src.core.suggestions import SuggestionInbox, SuggestionGenerator
from src.core.orchestrator import Orchestrator, Agent, AgentStatus
from src.api.kernel_api import KernelAPI, generate_api_json


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_project(tmp_path):
    return str(tmp_path)


@pytest.fixture
def api(tmp_project):
    return KernelAPI(tmp_project)


@pytest.fixture
def sample_config():
    return AgentConfig(
        name="test_agent",
        mode=AgentMode.AUTONOMOUS,
        capabilities=["coding", "testing"],
        max_concurrent_tasks=5,
        heartbeat_interval_seconds=15.0,
        auto_suggest=False,
        domain="testing",
        metadata={"version": "1.0"},
    )


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
def populated_api(api, sample_config, sample_suggestion):
    """API with registered agents and suggestions for testing."""
    api.kernel.agent_manager.register(sample_config)
    api.kernel.agent_manager.register(AgentConfig(name="researcher", mode=AgentMode.ASSISTED))
    api.inbox.add(sample_suggestion)
    api.inbox.add(Suggestion(
        agent_name="researcher",
        title="Research: Vector databases",
        description="Should we migrate to pgvector?",
        suggestion_type="research",
        domain="ai",
        priority="medium",
    ))
    api.kernel.heartbeat.record("test_agent", AgentHealth.HEALTHY, active_tasks=2)
    api.kernel.heartbeat.record("researcher", AgentHealth.DEGRADED, active_tasks=1)
    return api


@pytest.fixture
def sample_mission():
    return ScheduledMission(
        name="nightly_build",
        agent_name="engineer",
        description="Run nightly build tests",
        interval_seconds=3600,
        enabled=True,
    )


@pytest.fixture
def api_with_mission(api, sample_mission):
    """API with a scheduled mission added."""
    api.kernel.scheduler.add_mission(sample_mission)
    return api


@pytest.fixture
def mock_api(tmp_project):
    """API with heavily mocked internals for isolated endpoint testing."""
    with patch("src.api.kernel_api.create_default_kernel") as mock_create:
        mock_kernel = MagicMock(spec=AIOSKernel)
        mock_create.return_value = mock_kernel

        with patch("src.api.kernel_api.SuggestionInbox") as mock_inbox_cls:
            mock_inbox = MagicMock(spec=SuggestionInbox)
            mock_inbox_cls.return_value = mock_inbox

            with patch("src.api.kernel_api.Orchestrator") as mock_orch_cls:
                mock_orch = MagicMock(spec=Orchestrator)
                mock_orch_cls.return_value = mock_orch
                mock_orch.agents = {}

                api = KernelAPI(tmp_project)
                api.kernel = mock_kernel
                api.inbox = mock_inbox
                api.orchestrator = mock_orch
                yield api


# ===================================================================
# KernelAPI Initialization
# ===================================================================

class TestKernelAPIInit:
    def test_creates_kernel_api(self, api):
        assert api is not None
        assert isinstance(api.kernel, AIOSKernel)

    def test_creates_suggestion_inbox(self, api):
        assert isinstance(api.inbox, SuggestionInbox)

    def test_creates_orchestrator(self, api):
        assert isinstance(api.orchestrator, Orchestrator)

    def test_sets_orchestrator_on_kernel(self, api):
        assert api.kernel._orchestrator is api.orchestrator

    def test_stores_project_root(self, tmp_project):
        api = KernelAPI(tmp_project)
        assert api.project_root == tmp_project


# ===================================================================
# Agent Endpoints
# ===================================================================

class TestListAgents:
    def test_list_agents_empty(self, api):
        result = api.list_agents()
        default_count = len(api.kernel.agent_manager.get_all())
        assert result["total"] == default_count

    def test_list_agents_returns_agents(self, populated_api):
        result = populated_api.list_agents()
        names = [a["name"] for a in result["agents"]]
        assert "test_agent" in names
        assert "researcher" in names
        assert result["total"] >= 2

    def test_list_agents_includes_heartbeat(self, populated_api):
        result = populated_api.list_agents()
        agent = next(a for a in result["agents"] if a["name"] == "test_agent")
        assert agent["heartbeat"]["status"] == "healthy"
        assert agent["heartbeat"]["active_tasks"] == 2

    def test_list_agents_includes_orchestrator_data(self, populated_api):
        result = populated_api.list_agents()
        assert "tasks_completed" in result["agents"][0]
        assert "tasks_failed" in result["agents"][0]

    def test_list_agents_unknown_heartbeat(self, api):
        """Agent without heartbeat shows 'unknown' status."""
        api.kernel.agent_manager.register(AgentConfig(name="no_hb"))
        result = api.list_agents()
        agent = result["agents"][0]
        assert agent["heartbeat"]["status"] == "unknown"
        assert agent["heartbeat"]["timestamp"] is None
        assert agent["heartbeat"]["active_tasks"] == 0

    def test_list_agents_no_orchestrator_match(self, api):
        """Agent not in orchestrator shows 0 tasks."""
        api.kernel.agent_manager.register(AgentConfig(name="solo"))
        result = api.list_agents()
        agent = result["agents"][0]
        assert agent["tasks_completed"] == 0
        assert agent["tasks_failed"] == 0


class TestGetAgent:
    def test_get_agent_existing(self, populated_api):
        result = populated_api.get_agent("test_agent")
        assert result is not None
        assert result["name"] == "test_agent"
        assert result["mode"] == "autonomous"

    def test_get_agent_includes_heartbeat(self, populated_api):
        result = populated_api.get_agent("test_agent")
        assert result["heartbeat"]["status"] == "healthy"

    def test_get_agent_includes_orchestrator_stats(self, populated_api):
        result = populated_api.get_agent("test_agent")
        assert "tasks_completed" in result
        assert "tasks_failed" in result

    def test_get_agent_nonexistent(self, api):
        result = api.get_agent("ghost_agent")
        assert result is None

    def test_get_agent_unknown_heartbeat(self, api):
        api.kernel.agent_manager.register(AgentConfig(name="no_hb"))
        result = api.get_agent("no_hb")
        assert result["heartbeat"]["status"] == "unknown"
        assert result["heartbeat"]["timestamp"] is None

    def test_get_agent_no_orchestrator_match(self, api):
        api.kernel.agent_manager.register(AgentConfig(name="solo"))
        result = api.get_agent("solo")
        assert result["tasks_completed"] == 0
        assert result["tasks_failed"] == 0


class TestSetAgentMode:
    def test_set_agent_mode_valid(self, populated_api):
        result = populated_api.set_agent_mode("test_agent", "manual")
        assert result["success"] is True
        assert result["agent"] == "test_agent"
        assert result["mode"] == "manual"

    def test_set_agent_mode_invalid(self, populated_api):
        result = populated_api.set_agent_mode("test_agent", "invalid_mode")
        assert result["success"] is False
        assert "error" in result
        assert "Invalid mode" in result["error"]

    def test_set_agent_mode_all_modes(self, populated_api):
        for mode in ["manual", "assisted", "autonomous"]:
            result = populated_api.set_agent_mode("test_agent", mode)
            assert result["success"] is True
            assert result["mode"] == mode


# ===================================================================
# Suggestion Endpoints
# ===================================================================

class TestListSuggestions:
    def test_list_suggestions_empty(self, api):
        result = api.list_suggestions()
        assert result["suggestions"] == []
        assert result["total"] == 0
        assert "stats" in result

    def test_list_suggestions_with_data(self, populated_api):
        result = populated_api.list_suggestions()
        assert result["total"] == 2
        assert len(result["suggestions"]) == 2

    def test_list_suggestions_includes_stats(self, populated_api):
        result = populated_api.list_suggestions()
        assert "stats" in result
        assert result["stats"]["total"] == 2

    def test_list_suggestions_filter_by_status(self, populated_api):
        all_s = populated_api.inbox.get_all()
        populated_api.inbox.approve(all_s[0].id)
        result = populated_api.list_suggestions(status="approved")
        assert result["total"] == 1
        assert result["suggestions"][0]["status"] == "approved"

    def test_list_suggestions_filter_pending(self, populated_api):
        result = populated_api.list_suggestions(status="pending")
        assert result["total"] == 2

    def test_list_suggestions_filter_no_match(self, populated_api):
        result = populated_api.list_suggestions(status="executed")
        assert result["total"] == 0

    def test_list_suggestions_returns_suggestion_dicts(self, populated_api):
        result = populated_api.list_suggestions()
        for s in result["suggestions"]:
            assert "id" in s
            assert "title" in s
            assert "agent_name" in s
            assert "status" in s


class TestApproveSuggestion:
    def test_approve_existing(self, api, sample_suggestion):
        api.inbox.add(sample_suggestion)
        result = api.approve_suggestion(sample_suggestion.id)
        assert result["success"] is True
        assert result["id"] == sample_suggestion.id

    def test_approve_nonexistent(self, api):
        result = api.approve_suggestion("bad-id")
        assert result["success"] is False
        assert result["id"] == "bad-id"

    def test_approve_updates_status(self, api, sample_suggestion):
        api.inbox.add(sample_suggestion)
        api.approve_suggestion(sample_suggestion.id)
        s = api.inbox.get(sample_suggestion.id)
        assert s.status == "approved"


class TestRejectSuggestion:
    def test_reject_existing(self, api, sample_suggestion):
        api.inbox.add(sample_suggestion)
        result = api.reject_suggestion(sample_suggestion.id, reason="not needed")
        assert result["success"] is True
        assert result["id"] == sample_suggestion.id

    def test_reject_without_reason(self, api, sample_suggestion):
        api.inbox.add(sample_suggestion)
        result = api.reject_suggestion(sample_suggestion.id)
        assert result["success"] is True

    def test_reject_nonexistent(self, api):
        result = api.reject_suggestion("bad-id")
        assert result["success"] is False

    def test_reject_updates_status(self, api, sample_suggestion):
        api.inbox.add(sample_suggestion)
        api.reject_suggestion(sample_suggestion.id, reason="nope")
        s = api.inbox.get(sample_suggestion.id)
        assert s.status == "rejected"


class TestAddSuggestion:
    def test_add_suggestion(self, api):
        result = api.add_suggestion(
            agent_name="engineer",
            title="New feature",
            description="Add logging support",
        )
        assert result["success"] is True
        assert "id" in result

    def test_add_suggestion_with_all_params(self, api):
        result = api.add_suggestion(
            agent_name="architect",
            title="Migration plan",
            description="Migrate to cloud",
            suggestion_type="mission",
            domain="infrastructure",
            priority="high",
        )
        assert result["success"] is True
        s = api.inbox.get(result["id"])
        assert s.suggestion_type == "mission"
        assert s.domain == "infrastructure"
        assert s.priority == "high"

    def test_add_suggestion_persists(self, api):
        result = api.add_suggestion(
            agent_name="engineer",
            title="Persist me",
            description="Check persistence",
        )
        s = api.inbox.get(result["id"])
        assert s is not None
        assert s.title == "Persist me"

    def test_add_suggestion_default_params(self, api):
        result = api.add_suggestion(
            agent_name="engineer",
            title="Defaults test",
            description="Testing defaults",
        )
        s = api.inbox.get(result["id"])
        assert s.suggestion_type == "improvement"
        assert s.domain == ""
        assert s.priority == "medium"


# ===================================================================
# Scheduler Endpoints
# ===================================================================

class TestListScheduledMissions:
    def test_list_empty(self, api):
        result = api.list_scheduled_missions()
        assert result["missions"] == []
        assert result["total"] == 0

    def test_list_with_missions(self, api_with_mission):
        result = api_with_mission.list_scheduled_missions()
        assert result["total"] == 1
        assert result["missions"][0]["name"] == "nightly_build"

    def test_list_multiple_missions(self, api):
        api.kernel.scheduler.add_mission(ScheduledMission(name="m1", agent_name="a"))
        api.kernel.scheduler.add_mission(ScheduledMission(name="m2", agent_name="b"))
        result = api.list_scheduled_missions()
        assert result["total"] == 2

    def test_list_missions_returns_dicts(self, api_with_mission):
        result = api_with_mission.list_scheduled_missions()
        for m in result["missions"]:
            assert "id" in m
            assert "name" in m
            assert "agent_name" in m


class TestAddScheduledMission:
    def test_add_mission(self, api):
        result = api.add_scheduled_mission(
            name="daily_report",
            agent_name="engineer",
        )
        assert result["success"] is True
        assert "id" in result

    def test_add_mission_with_all_params(self, api):
        result = api.add_scheduled_mission(
            name="weekly_sync",
            agent_name="architect",
            description="Sync all modules",
            interval_seconds=604800,
            enabled=False,
        )
        assert result["success"] is True
        mission = api.kernel.scheduler.get_mission(result["id"])
        assert mission.name == "weekly_sync"
        assert mission.interval_seconds == 604800
        assert mission.enabled is False

    def test_add_mission_persists(self, api):
        result = api.add_scheduled_mission(name="persist_test", agent_name="eng")
        mission = api.kernel.scheduler.get_mission(result["id"])
        assert mission is not None

    def test_add_mission_default_params(self, api):
        result = api.add_scheduled_mission(name="defaults", agent_name="eng")
        mission = api.kernel.scheduler.get_mission(result["id"])
        assert mission.interval_seconds == 3600
        assert mission.enabled is True
        assert mission.description == ""


class TestGetDueMissions:
    def test_get_due_empty(self, api):
        result = api.get_due_missions()
        assert result["due"] == []
        assert result["total"] == 0

    def test_get_due_with_due_mission(self, api):
        past = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        from datetime import timedelta
        past = past - timedelta(hours=2)
        m = ScheduledMission(
            name="overdue",
            agent_name="eng",
            interval_seconds=60,
            next_run=past.isoformat(),
        )
        api.kernel.scheduler.add_mission(m)
        result = api.get_due_missions()
        assert result["total"] >= 1
        assert result["due"][0]["name"] == "overdue"


# ===================================================================
# Kernel Status & Dashboard
# ===================================================================

class TestGetKernelStatus:
    def test_get_kernel_status(self, populated_api):
        result = populated_api.get_kernel_status()
        assert "project_root" in result
        assert "suggestion_stats" in result
        assert "orchestrator" in result

    def test_get_kernel_status_includes_suggestion_stats(self, populated_api):
        result = populated_api.get_kernel_status()
        stats = result["suggestion_stats"]
        assert "total" in stats
        assert stats["total"] == 2

    def test_get_kernel_status_includes_orchestrator(self, populated_api):
        result = populated_api.get_kernel_status()
        orch = result["orchestrator"]
        assert isinstance(orch, dict)


class TestGetDashboardData:
    def test_dashboard_data_structure(self, populated_api):
        result = populated_api.get_dashboard_data()
        assert "agents" in result
        assert "tasks" in result
        assert "suggestions" in result
        assert "scheduler" in result

    def test_dashboard_agents_count(self, populated_api):
        result = populated_api.get_dashboard_data()
        assert result["agents"]["total"] >= 2

    def test_dashboard_agents_online(self, populated_api):
        """Online = agents not in MANUAL mode."""
        result = populated_api.get_dashboard_data()
        assert result["agents"]["online"] >= 2

    def test_dashboard_agents_busy(self, populated_api):
        result = populated_api.get_dashboard_data()
        assert "busy" in result["agents"]

    def test_dashboard_tasks_structure(self, populated_api):
        result = populated_api.get_dashboard_data()
        tasks = result["tasks"]
        assert "pending" in tasks
        assert "completed" in tasks
        assert "total" in tasks

    def test_dashboard_suggestions_stats(self, populated_api):
        result = populated_api.get_dashboard_data()
        assert result["suggestions"]["total"] == 2

    def test_dashboard_scheduler_info(self, populated_api):
        result = populated_api.get_dashboard_data()
        assert "total_missions" in result["scheduler"]
        assert "due_now" in result["scheduler"]

    def test_dashboard_stale_agents(self, populated_api):
        result = populated_api.get_dashboard_data()
        assert "stale_agents" in result
        assert isinstance(result["stale_agents"], list)

    def test_dashboard_empty_api(self, api):
        result = api.get_dashboard_data()
        default_count = len(api.kernel.agent_manager.get_all())
        assert result["agents"]["total"] == default_count
        assert result["agents"]["online"] >= 0
        assert result["suggestions"]["total"] == 0
        assert result["scheduler"]["total_missions"] == 0


# ===================================================================
# generate_api_json
# ===================================================================

class TestGenerateApiJson:
    def test_agents_endpoint(self, populated_api):
        result = generate_api_json(populated_api, "agents")
        data = json.loads(result)
        assert "agents" in data
        assert data["total"] >= 2

    def test_agent_endpoint(self, populated_api):
        result = generate_api_json(populated_api, "agent", name="test_agent")
        data = json.loads(result)
        assert data["name"] == "test_agent"

    def test_agent_endpoint_not_found(self, populated_api):
        result = generate_api_json(populated_api, "agent", name="ghost")
        assert result == "null"

    def test_suggestions_endpoint(self, populated_api):
        result = generate_api_json(populated_api, "suggestions")
        data = json.loads(result)
        assert "suggestions" in data

    def test_suggestions_with_status_filter(self, populated_api):
        result = generate_api_json(populated_api, "suggestions", status="pending")
        data = json.loads(result)
        assert data["total"] == 2

    def test_kernel_status_endpoint(self, populated_api):
        result = generate_api_json(populated_api, "kernel_status")
        data = json.loads(result)
        assert "project_root" in data

    def test_dashboard_endpoint(self, populated_api):
        result = generate_api_json(populated_api, "dashboard")
        data = json.loads(result)
        assert "agents" in data

    def test_scheduled_missions_endpoint(self, populated_api):
        result = generate_api_json(populated_api, "scheduled_missions")
        data = json.loads(result)
        assert "missions" in data

    def test_due_missions_endpoint(self, api):
        result = generate_api_json(api, "due_missions")
        data = json.loads(result)
        assert "due" in data

    def test_unknown_endpoint(self, populated_api):
        result = generate_api_json(populated_api, "nonexistent")
        data = json.loads(result)
        assert "error" in data
        assert "Unknown endpoint" in data["error"]

    def test_json_output_is_valid(self, populated_api):
        result = generate_api_json(populated_api, "dashboard")
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_json_default_str_serializer(self, populated_api):
        """Ensure datetime objects are serialized via default=str."""
        result = generate_api_json(populated_api, "kernel_status")
        parsed = json.loads(result)
        assert parsed is not None


# ===================================================================
# Error Handling & Edge Cases
# ===================================================================

class TestEdgeCases:
    def test_list_agents_after_unregister(self, api):
        initial_count = api.list_agents()["total"]
        api.kernel.agent_manager.register(AgentConfig(name="temp"))
        assert api.list_agents()["total"] == initial_count + 1
        api.kernel.agent_manager.unregister("temp")
        assert api.list_agents()["total"] == initial_count

    def test_approve_already_approved(self, api, sample_suggestion):
        api.inbox.add(sample_suggestion)
        api.approve_suggestion(sample_suggestion.id)
        result = api.approve_suggestion(sample_suggestion.id)
        assert result["success"] is False

    def test_reject_after_approve(self, api, sample_suggestion):
        api.inbox.add(sample_suggestion)
        api.approve_suggestion(sample_suggestion.id)
        result = api.reject_suggestion(sample_suggestion.id)
        assert result["success"] is False

    def test_empty_project_root(self):
        api = KernelAPI("")
        assert api.project_root == ""

    def test_concurrent_suggestion_add(self, api):
        """Adding multiple suggestions maintains correct count."""
        for i in range(10):
            api.add_suggestion(
                agent_name=f"agent_{i}",
                title=f"Suggestion {i}",
                description=f"Description {i}",
            )
        result = api.list_suggestions()
        assert result["total"] == 10

    def test_mission_id_uniqueness(self, api):
        """Each added mission gets a unique ID."""
        r1 = api.add_scheduled_mission(name="m1", agent_name="a")
        r2 = api.add_scheduled_mission(name="m2", agent_name="b")
        assert r1["id"] != r2["id"]

    def test_suggestion_id_uniqueness(self, api):
        """Each added suggestion gets a unique ID."""
        r1 = api.add_suggestion(agent_name="a", title="t1", description="d1")
        r2 = api.add_suggestion(agent_name="b", title="t2", description="d2")
        assert r1["id"] != r2["id"]

    def test_dashboard_with_busy_agent(self, api):
        """Dashboard correctly counts busy agents from orchestrator."""
        mock_orch_agent = MagicMock()
        mock_orch_agent.status.value = "busy"
        api.orchestrator.agents = {"test_agent": mock_orch_agent}
        result = api.get_dashboard_data()
        assert result["agents"]["busy"] == 1

    def test_dashboard_all_idle_agents(self, api):
        """Dashboard counts 0 busy when all agents are idle."""
        mock_orch_agent = MagicMock()
        mock_orch_agent.status.value = "idle"
        api.orchestrator.agents = {"test_agent": mock_orch_agent}
        result = api.get_dashboard_data()
        assert result["agents"]["busy"] == 0

    def test_remove_scheduled_mission(self, api):
        """Can remove a scheduled mission via scheduler directly."""
        r = api.add_scheduled_mission(name="to_remove", agent_name="a")
        assert api.kernel.scheduler.remove_mission(r["id"]) is True
        result = api.list_scheduled_missions()
        assert result["total"] == 0


# ===================================================================
# Browser Agent Endpoints
# ===================================================================

class TestBrowserAgentEndpoints:
    def test_get_browser_agent(self, api):
        result = api.get_browser_agent()
        assert "name" in result or "error" in result

    def test_get_browser_agent_when_registered(self, api):
        """Browser agent should be registered by default."""
        result = api.get_browser_agent()
        assert result["name"] == "browser"
        assert result["mode"] == "autonomous"

    def test_execute_browser_task_invalid_type(self, api):
        result = api.execute_browser_task("invalid_type", {})
        assert result["success"] is False
        assert "Invalid task type" in result["error"]

    def test_execute_browser_task_valid_types(self, api):
        for task_type in ["browse", "scrape", "ocr", "screenshot", "download", "search", "extract_json"]:
            result = api.execute_browser_task(task_type, {"url": "http://example.com"})
            assert "success" in result

    def test_schedule_browser_task(self, api):
        result = api.schedule_browser_task(
            name="nightly_scrape",
            task_type="scrape",
            params={"url": "http://example.com"},
            interval_seconds=7200,
        )
        assert result["success"] is True
        assert result["task_type"] == "scrape"

    def test_get_browser_memories(self, api):
        result = api.get_browser_memories()
        assert "memories" in result
        assert "total" in result

    def test_get_browser_memories_with_query(self, api):
        result = api.get_browser_memories(query="scrape")
        assert "memories" in result


class TestBrowserAgentInDashboard:
    def test_dashboard_includes_browser_agent(self, api):
        result = api.get_dashboard_data()
        assert result["agents"]["total"] >= 9

    def test_list_agents_includes_browser(self, api):
        result = api.list_agents()
        names = [a["name"] for a in result["agents"]]
        assert "browser" in names


class TestGenerateApiJsonBrowser:
    def test_browser_endpoint(self, api):
        result = generate_api_json(api, "browser")
        data = json.loads(result)
        assert data["name"] == "browser"

    def test_browser_memories_endpoint(self, api):
        result = generate_api_json(api, "browser_memories")
        data = json.loads(result)
        assert "memories" in data
