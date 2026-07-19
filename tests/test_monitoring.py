"""Tests for the Monitoring system."""

import os
import json
import time
import pytest
from datetime import datetime

from src.core.monitoring import Monitor, LogLevel, HealthStatus, Metric, HealthCheck, Alert


@pytest.fixture
def tmp_project(tmp_path):
    return str(tmp_path)


@pytest.fixture
def mon(tmp_project):
    return Monitor(tmp_project)


class TestMonitorLogging:
    def test_log_info(self, mon):
        mon.log(LogLevel.INFO, "System started")
        # Should not raise
        assert True

    def test_log_all_levels(self, mon):
        for level in LogLevel:
            mon.log(level, f"Test {level.value}")

    def test_log_with_context(self, mon):
        mon.log(LogLevel.INFO, "Task created", context={"task_id": "123", "priority": "high"})


class TestMonitorMetrics:
    def test_record_metric(self, mon):
        mon.record_metric("cpu_usage", 45.5)
        metrics = mon.get_metrics("cpu_usage")
        assert len(metrics) == 1
        assert metrics[0].value == 45.5

    def test_record_metric_with_labels(self, mon):
        mon.record_metric("task_duration", 12.3, labels={"agent": "engineer"})
        metrics = mon.get_metrics("task_duration")
        assert metrics[0].labels["agent"] == "engineer"

    def test_get_all_metrics(self, mon):
        mon.record_metric("m1", 1.0)
        mon.record_metric("m2", 2.0)
        all_metrics = mon.get_metrics()
        assert len(all_metrics) == 2

    def test_get_metrics_by_name(self, mon):
        mon.record_metric("cpu", 50.0)
        mon.record_metric("memory", 60.0)
        cpu = mon.get_metrics("cpu")
        assert len(cpu) == 1
        assert cpu[0].name == "cpu"


class TestMonitorHealth:
    def test_health_check(self, mon):
        status = mon.health_check()
        assert isinstance(status, HealthStatus)

    def test_health_check_records_results(self, mon):
        mon.health_check()
        assert len(mon.health_checks) > 0


class TestMonitorSystemMetrics:
    def test_get_system_metrics(self, mon):
        metrics = mon.get_system_metrics()
        assert "uptime_seconds" in metrics
        assert "timestamp" in metrics

    def test_get_task_metrics_empty(self, mon):
        metrics = mon.get_task_metrics()
        assert metrics["created"] == 0
        assert metrics["completed"] == 0
        assert metrics["success_rate"] == 0

    def test_get_agent_metrics_empty(self, mon):
        metrics = mon.get_agent_metrics()
        assert metrics["total_agents"] == 0


class TestMonitorTaskMetrics:
    def test_task_metrics_after_recording(self, mon):
        mon.record_metric("task.created", 1)
        mon.record_metric("task.created", 1)
        mon.record_metric("task.completed", 1)
        mon.record_metric("task.failed", 1)
        metrics = mon.get_task_metrics()
        assert metrics["created"] == 2
        assert metrics["completed"] == 1
        assert metrics["failed"] == 1
        assert metrics["success_rate"] == pytest.approx(50.0)


class TestMonitorAgentMetrics:
    def test_agent_metrics(self, mon):
        mon.record_metric("task.completed", 1, labels={"agent_id": "engineer"})
        mon.record_metric("task.completed", 1, labels={"agent_id": "engineer"})
        mon.record_metric("task.failed", 1, labels={"agent_id": "engineer"})
        metrics = mon.get_agent_metrics()
        assert metrics["total_agents"] == 1
        eng = metrics["agents"]["engineer"]
        assert eng["total_tasks"] == 3
        assert eng["completed"] == 2
        assert eng["failed"] == 1


class TestMonitorAlerts:
    def test_error_log_triggers_alert(self, mon):
        mon.log(LogLevel.ERROR, "Disk full")
        assert len(mon.alerts) == 1
        assert mon.alerts[0].level == "error"

    def test_critical_log_triggers_alert(self, mon):
        mon.log(LogLevel.CRITICAL, "System crash")
        assert len(mon.alerts) == 1

    def test_info_no_alert(self, mon):
        mon.log(LogLevel.INFO, "Normal operation")
        assert len(mon.alerts) == 0


class TestMonitorReport:
    def test_generate_report(self, mon):
        mon.record_metric("task.created", 1)
        report = mon.generate_report()
        assert "timestamp" in report
        assert "system" in report
        assert "tasks" in report
        assert "health_status" in report
        assert report["total_metrics_recorded"] == 1


class TestMonitorPersistence:
    def test_save_and_load_metrics(self, mon):
        mon.record_metric("test.metric", 42.0, labels={"env": "test"})
        mon.save_metrics()
        # Load into new instance
        mon2 = Monitor(mon.project_root)
        mon2.load_metrics()
        loaded = mon2.get_metrics("test.metric")
        assert len(loaded) == 1
        assert loaded[0].value == 42.0


class TestMonitorDirectories:
    def test_creates_directories(self, tmp_project):
        Monitor(tmp_project)
        assert os.path.isdir(os.path.join(tmp_project, "logs"))
        assert os.path.isdir(os.path.join(tmp_project, "metrics"))
