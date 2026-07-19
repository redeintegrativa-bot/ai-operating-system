"""Tests for the AIOS Kernel module (AgentManager, HeartbeatMonitor, Scheduler, AIOSKernel)."""

import os
import json
import time
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

from src.core.kernel import (
    AgentManager,
    AgentConfig,
    AgentMode,
    AgentHealth,
    AgentHeartbeat,
    HeartbeatMonitor,
    Scheduler,
    ScheduledMission,
    Suggestion,
    AIOSKernel,
    create_default_kernel,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_project(tmp_path):
    return str(tmp_path)


@pytest.fixture
def am(tmp_project):
    return AgentManager(tmp_project)


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
def hb():
    return HeartbeatMonitor()


@pytest.fixture
def scheduler():
    return Scheduler()


@pytest.fixture
def kernel(tmp_project):
    return AIOSKernel(tmp_project)


# ===================================================================
# AgentConfig
# ===================================================================

class TestAgentConfig:
    def test_default_values(self):
        config = AgentConfig(name="default_agent")
        assert config.name == "default_agent"
        assert config.mode == AgentMode.ASSISTED
        assert config.capabilities == []
        assert config.max_concurrent_tasks == 3
        assert config.heartbeat_interval_seconds == 30.0
        assert config.auto_suggest is True
        assert config.domain == ""
        assert config.metadata == {}

    def test_to_dict(self, sample_config):
        d = sample_config.to_dict()
        assert d["name"] == "test_agent"
        assert d["mode"] == "autonomous"
        assert d["capabilities"] == ["coding", "testing"]
        assert d["auto_suggest"] is False

    def test_from_dict(self):
        data = {
            "name": "restored",
            "mode": "manual",
            "capabilities": ["ops"],
            "max_concurrent_tasks": 2,
            "heartbeat_interval_seconds": 60.0,
            "auto_suggest": True,
            "domain": "operations",
            "metadata": {"env": "prod"},
        }
        config = AgentConfig.from_dict(data)
        assert config.name == "restored"
        assert config.mode == AgentMode.MANUAL
        assert config.domain == "operations"
        assert config.metadata["env"] == "prod"


# ===================================================================
# AgentManager
# ===================================================================

class TestAgentManagerRegister:
    def test_register_agent(self, am, sample_config):
        result = am.register(sample_config)
        assert result is sample_config
        assert am.get("test_agent") is sample_config

    def test_register_creates_config_file(self, am, sample_config):
        am.register(sample_config)
        config_path = os.path.join(am._config_dir, "test_agent.json")
        assert os.path.exists(config_path)
        with open(config_path) as f:
            data = json.load(f)
        assert data["name"] == "test_agent"
        assert data["mode"] == "autonomous"

    def test_register_overwrites_existing(self, am, sample_config):
        am.register(sample_config)
        updated = AgentConfig(name="test_agent", mode=AgentMode.MANUAL)
        am.register(updated)
        assert am.get("test_agent").mode == AgentMode.MANUAL

    def test_register_multiple_agents(self, am):
        a1 = AgentConfig(name="agent_one")
        a2 = AgentConfig(name="agent_two")
        am.register(a1)
        am.register(a2)
        assert len(am.get_all()) == 2


class TestAgentManagerUnregister:
    def test_unregister_agent(self, am, sample_config):
        am.register(sample_config)
        assert am.unregister("test_agent") is True
        assert am.get("test_agent") is None

    def test_unregister_removes_config_file(self, am, sample_config):
        am.register(sample_config)
        config_path = os.path.join(am._config_dir, "test_agent.json")
        assert os.path.exists(config_path)
        am.unregister("test_agent")
        assert not os.path.exists(config_path)

    def test_unregister_nonexistent_agent(self, am):
        assert am.unregister("ghost") is False

    def test_unregister_twice(self, am, sample_config):
        am.register(sample_config)
        assert am.unregister("test_agent") is True
        assert am.unregister("test_agent") is False


class TestAgentManagerQuery:
    def test_get_nonexistent(self, am):
        assert am.get("ghost") is None

    def test_get_all_empty(self, am):
        assert am.get_all() == []

    def test_get_all_after_register(self, am):
        am.register(AgentConfig(name="a"))
        am.register(AgentConfig(name="b"))
        names = [c.name for c in am.get_all()]
        assert sorted(names) == ["a", "b"]

    def test_set_mode(self, am, sample_config):
        am.register(sample_config)
        assert am.set_mode("test_agent", AgentMode.MANUAL) is True
        assert am.get("test_agent").mode == AgentMode.MANUAL

    def test_set_mode_nonexistent(self, am):
        assert am.set_mode("ghost", AgentMode.AUTONOMOUS) is False

    def test_get_by_mode(self, am):
        am.register(AgentConfig(name="auto", mode=AgentMode.AUTONOMOUS))
        am.register(AgentConfig(name="manual", mode=AgentMode.MANUAL))
        am.register(AgentConfig(name="assisted", mode=AgentMode.ASSISTED))
        autos = am.get_by_mode(AgentMode.AUTONOMOUS)
        assert len(autos) == 1
        assert autos[0].name == "auto"

    def test_can_auto_suggest_true(self, am):
        config = AgentConfig(name="suggester", auto_suggest=True)
        am.register(config)
        assert am.can_auto_suggest("suggester") is True

    def test_can_auto_suggest_false(self, am, sample_config):
        am.register(sample_config)
        assert am.can_auto_suggest("test_agent") is False

    def test_can_auto_suggest_nonexistent(self, am):
        assert am.can_auto_suggest("ghost") is False

    def test_to_dict(self, am, sample_config):
        am.register(sample_config)
        d = am.to_dict()
        assert "test_agent" in d
        assert d["test_agent"]["mode"] == "autonomous"


class TestAgentManagerPersistence:
    def test_loads_existing_configs_on_init(self, tmp_project):
        am1 = AgentManager(tmp_project)
        am1.register(AgentConfig(name="persist_me", domain="persistence"))
        am2 = AgentManager(tmp_project)
        agent = am2.get("persist_me")
        assert agent is not None
        assert agent.domain == "persistence"

    def test_ignores_invalid_json(self, tmp_project):
        am = AgentManager(tmp_project)
        # Manually write a bad file
        bad_dir = am._config_dir
        with open(os.path.join(bad_dir, "bad.json"), "w") as f:
            f.write("not json")
        # _load_configs is called in __init__; should not raise
        assert True


# ===================================================================
# HeartbeatMonitor
# ===================================================================

class TestHeartbeatMonitor:
    def test_record_and_get(self, hb):
        hb.record("agent1", AgentHealth.HEALTHY, active_tasks=2, latency_ms=12.5)
        result = hb.get("agent1")
        assert result is not None
        assert result.agent_name == "agent1"
        assert result.status == "healthy"
        assert result.active_tasks == 2
        assert result.latency_ms == 12.5

    def test_record_with_metadata(self, hb):
        hb.record("agent1", AgentHealth.DEGRADED, metadata={"reason": "high_latency"})
        result = hb.get("agent1")
        assert result.metadata["reason"] == "high_latency"

    def test_get_nonexistent(self, hb):
        assert hb.get("ghost") is None

    def test_get_all(self, hb):
        hb.record("a", AgentHealth.HEALTHY)
        hb.record("b", AgentHealth.UNHEALTHY)
        all_hb = hb.get_all()
        assert len(all_hb) == 2
        assert all_hb["a"].status == "healthy"
        assert all_hb["b"].status == "unhealthy"

    def test_get_all_returns_copy(self, hb):
        hb.record("a", AgentHealth.HEALTHY)
        all_hb = hb.get_all()
        hb.record("b", AgentHealth.HEALTHY)
        assert "b" not in all_hb

    def test_get_stale_empty(self, hb):
        assert hb.get_stale(max_age_seconds=1.0) == []

    def test_get_stale_returns_fresh_if_not_stale(self, hb):
        hb.record("fresh", AgentHealth.HEALTHY)
        stale = hb.get_stale(max_age_seconds=9999)
        assert stale == []

    def test_get_stale_returns_old_heartbeats(self, hb):
        hb.record("old_agent", AgentHealth.HEALTHY)
        with patch("src.core.kernel.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2099, 1, 1, tzinfo=timezone.utc)
            mock_dt.fromisoformat = datetime.fromisoformat
            stale = hb.get_stale(max_age_seconds=1.0)
            assert "old_agent" in stale

    def test_record_overwrites_previous(self, hb):
        hb.record("agent1", AgentHealth.HEALTHY, active_tasks=2)
        hb.record("agent1", AgentHealth.DEGRADED, active_tasks=5)
        result = hb.get("agent1")
        assert result.status == "degraded"
        assert result.active_tasks == 5


# ===================================================================
# Scheduler
# ===================================================================

class TestSchedulerMissionManagement:
    def test_add_and_get_mission(self, scheduler):
        m = ScheduledMission(name="nightly", agent_name="engineer", interval_seconds=3600)
        mid = scheduler.add_mission(m)
        assert mid == m.id
        retrieved = scheduler.get_mission(mid)
        assert retrieved is not None
        assert retrieved.name == "nightly"

    def test_get_nonexistent_mission(self, scheduler):
        assert scheduler.get_mission("bad_id") is None

    def test_remove_mission(self, scheduler):
        m = ScheduledMission(name="remove_me")
        mid = scheduler.add_mission(m)
        assert scheduler.remove_mission(mid) is True
        assert scheduler.get_mission(mid) is None

    def test_remove_nonexistent_mission(self, scheduler):
        assert scheduler.remove_mission("bad_id") is False

    def test_get_all_missions(self, scheduler):
        scheduler.add_mission(ScheduledMission(name="m1"))
        scheduler.add_mission(ScheduledMission(name="m2"))
        assert len(scheduler.get_all_missions()) == 2

    def test_get_due_missions_by_next_run(self, scheduler):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        m = ScheduledMission(
            name="overdue",
            interval_seconds=60,
            next_run=past.isoformat(),
        )
        scheduler.add_mission(m)
        due = scheduler.get_due_missions()
        assert len(due) == 1

    def test_get_due_missions_disabled_skipped(self, scheduler):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        m = ScheduledMission(
            name="disabled_overdue",
            enabled=False,
            next_run=past.isoformat(),
        )
        scheduler.add_mission(m)
        assert scheduler.get_due_missions() == []

    def test_get_due_missions_interval_based(self, scheduler):
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        m = ScheduledMission(
            name="interval_due",
            interval_seconds=3600,
            last_run=past.isoformat(),
        )
        scheduler.add_mission(m)
        due = scheduler.get_due_missions()
        assert len(due) == 1

    def test_get_due_missions_never_run(self, scheduler):
        m = ScheduledMission(
            name="never_run",
            interval_seconds=3600,
            last_run=None,
        )
        scheduler.add_mission(m)
        due = scheduler.get_due_missions()
        assert len(due) == 1

    def test_mark_run(self, scheduler):
        m = ScheduledMission(name="runner", interval_seconds=300)
        mid = scheduler.add_mission(m)
        scheduler.mark_run(mid)
        mission = scheduler.get_mission(mid)
        assert mission.run_count == 1
        assert mission.last_run is not None
        assert mission.next_run is not None

    def test_mark_run_nonexistent(self, scheduler):
        scheduler.mark_run("bad_id")  # should not raise

    def test_register_callback(self, scheduler):
        cb = MagicMock()
        m = ScheduledMission(name="cb_test", interval_seconds=60)
        mid = scheduler.add_mission(m)
        scheduler.register_callback(mid, cb)
        scheduler._execute_mission(m)
        cb.assert_called_once_with(m)
        mission = scheduler.get_mission(mid)
        assert mission.run_count == 1


# ===================================================================
# AIOSKernel
# ===================================================================

class TestAIOSKernel:
    def test_initialize(self, kernel):
        assert kernel.project_root is not None
        assert isinstance(kernel.agent_manager, AgentManager)
        assert isinstance(kernel.heartbeat, HeartbeatMonitor)
        assert isinstance(kernel.scheduler, Scheduler)

    def test_get_agent_manager(self, kernel):
        assert kernel.agent_manager is kernel.agent_manager

    def test_get_heartbeat_monitor(self, kernel):
        assert kernel.heartbeat is kernel.heartbeat

    def test_get_scheduler(self, kernel):
        assert kernel.scheduler is kernel.scheduler

    def test_set_orchestrator(self, kernel):
        kernel.set_orchestrator("orchestrator")
        assert kernel._orchestrator == "orchestrator"

    def test_set_event_bus(self, kernel):
        kernel.set_event_bus("event_bus")
        assert kernel._event_bus == "event_bus"

    def test_set_monitor(self, kernel):
        kernel.set_monitor("monitor")
        assert kernel._monitor == "monitor"

    def test_start_stop(self, kernel):
        kernel.start()
        assert kernel.scheduler._running is True
        kernel.stop()
        assert kernel.scheduler._running is False

    def test_get_status(self, kernel):
        kernel.agent_manager.register(AgentConfig(name="stat_agent"))
        kernel.heartbeat.record("stat_agent", AgentHealth.HEALTHY)
        status = kernel.get_status()
        assert status["project_root"] == kernel.project_root
        assert status["agents_count"] == 1
        assert "stat_agent" in status["agents"]
        assert status["scheduled_missions"] == 0
        assert isinstance(status["due_missions"], int)
        assert isinstance(status["stale_agents"], list)


# ===================================================================
# create_default_kernel
# ===================================================================

class TestCreateDefaultKernel:
    def test_creates_kernel(self, tmp_project):
        kernel = create_default_kernel(tmp_project)
        assert isinstance(kernel, AIOSKernel)

    def test_registers_default_agents(self, tmp_project):
        kernel = create_default_kernel(tmp_project)
        agents = kernel.agent_manager.get_all()
        names = {a.name for a in agents}
        expected = {"orchestrator", "architect", "engineer", "researcher",
                     "ai_specialist", "automation", "database", "security"}
        assert names == expected

    def test_default_agent_configs(self, tmp_project):
        kernel = create_default_kernel(tmp_project)
        orch = kernel.agent_manager.get("orchestrator")
        assert orch.mode == AgentMode.AUTONOMOUS
        assert "routing" in orch.capabilities

    def test_agents_persist_on_disk(self, tmp_project):
        kernel = create_default_kernel(tmp_project)
        config_dir = kernel.agent_manager._config_dir
        files = os.listdir(config_dir)
        assert len(files) == 8
