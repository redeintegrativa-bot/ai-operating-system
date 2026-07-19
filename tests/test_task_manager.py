"""Tests for the TaskManager core module."""

import os
import json
import tempfile
import shutil
import pytest
from datetime import datetime, timedelta

from src.core.task_manager import TaskManager, Task, TaskStatus, TaskPriority


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory."""
    return str(tmp_path)


@pytest.fixture
def tm(tmp_project):
    """Create a TaskManager instance with temp directory."""
    return TaskManager(tmp_project)


class TestTaskCreation:
    def test_create_task_defaults(self, tm):
        task = tm.create_task("Build login page")
        assert task.description == "Build login page"
        assert task.status == TaskStatus.CREATED
        assert task.priority == TaskPriority.MEDIUM
        assert task.id is not None
        assert task.assigned_agent is None
        assert task.result is None
        assert task.errors == []
        assert task.metadata == {}
        assert task.retry_count == 0
        assert task.max_retries == 3

    def test_create_task_with_priority(self, tm):
        task = tm.create_task("Critical fix", priority=TaskPriority.CRITICAL)
        assert task.priority == TaskPriority.CRITICAL

    def test_create_task_with_metadata(self, tm):
        task = tm.create_task("Task", metadata={"sprint": 42, "story_points": 5})
        assert task.metadata["sprint"] == 42
        assert task.metadata["story_points"] == 5

    def test_create_task_with_deadline(self, tm):
        dl = datetime.now() + timedelta(days=7)
        task = tm.create_task("Task", deadline=dl)
        assert task.deadline is not None

    def test_create_task_with_dependencies(self, tm):
        dep = tm.create_task("Setup DB")
        task = tm.create_task("Migrate data", dependencies=[dep.id])
        assert task.dependencies == [dep.id]

    def test_create_task_with_timeout(self, tm):
        task = tm.create_task("Long task", timeout_seconds=300)
        assert task.timeout_seconds == 300

    def test_create_task_persists(self, tmp_project):
        tm1 = TaskManager(tmp_project)
        t1 = tm1.create_task("Persistent task")
        tm2 = TaskManager(tmp_project)
        loaded = tm2.get_task(t1.id)
        assert loaded is not None
        assert loaded.description == "Persistent task"

    def test_multiple_tasks_unique_ids(self, tm):
        ids = set()
        for i in range(10):
            t = tm.create_task(f"Task {i}")
            ids.add(t.id)
        assert len(ids) == 10


class TestTaskQueries:
    def test_get_task(self, tm):
        task = tm.create_task("Find me")
        found = tm.get_task(task.id)
        assert found.id == task.id

    def test_get_task_not_found(self, tm):
        assert tm.get_task("nonexistent") is None

    def test_find_task_by_prefix(self, tm):
        task = tm.create_task("Prefix test")
        found = tm.find_task_by_prefix(task.id[:8])
        assert found.id == task.id

    def test_find_task_by_prefix_not_found(self, tm):
        assert tm.find_task_by_prefix("zzzzzzzz") is None

    def test_get_pending_tasks(self, tm):
        tm.create_task("A")
        tm.create_task("B")
        pending = tm.get_pending_tasks()
        assert len(pending) == 2

    def test_get_tasks_by_status(self, tm):
        tm.create_task("A")
        tasks = tm.get_tasks_by_status(TaskStatus.CREATED)
        assert len(tasks) == 1

    def test_get_tasks_by_priority(self, tm):
        tm.create_task("Low", priority=TaskPriority.LOW)
        tm.create_task("High", priority=TaskPriority.HIGH)
        high = tm.get_tasks_by_priority(TaskPriority.HIGH)
        assert len(high) == 1
        assert high[0].description == "High"

    def test_get_tasks_by_agent(self, tm):
        t = tm.create_task("Agent task")
        tm.assign_task(t.id, "engineer")
        tasks = tm.get_tasks_by_agent("engineer")
        assert len(tasks) == 1

    def test_list_all_tasks(self, tm):
        for i in range(5):
            tm.create_task(f"Task {i}")
        assert len(tm.list_all_tasks()) == 5


class TestTaskUpdates:
    def test_update_task_status(self, tm):
        task = tm.create_task("Update me")
        tm.update_task_status(task.id, TaskStatus.RUNNING)
        updated = tm.get_task(task.id)
        assert updated.status == TaskStatus.RUNNING

    def test_update_task_status_not_found(self, tm):
        with pytest.raises(ValueError, match="Task not found"):
            tm.update_task_status("bad_id", TaskStatus.RUNNING)

    def test_update_task_with_result(self, tm):
        task = tm.create_task("Result task")
        tm.update_task_status(task.id, TaskStatus.COMPLETED, result={"output": "done"})
        updated = tm.get_task(task.id)
        assert updated.result == {"output": "done"}

    def test_update_task_with_error(self, tm):
        task = tm.create_task("Error task")
        tm.update_task_status(task.id, TaskStatus.FAILED, error="oops")
        updated = tm.get_task(task.id)
        assert "oops" in updated.errors

    def test_assign_task(self, tm):
        task = tm.create_task("Assign me")
        tm.assign_task(task.id, "engineer")
        assigned = tm.get_task(task.id)
        assert assigned.assigned_agent == "engineer"
        assert assigned.status == TaskStatus.ASSIGNED

    def test_assign_task_not_found(self, tm):
        with pytest.raises(ValueError, match="Task not found"):
            tm.assign_task("bad_id", "engineer")

    def test_assign_task_with_unmet_deps(self, tm):
        dep = tm.create_task("Dep")
        task = tm.create_task("Blocked", dependencies=[dep.id])
        with pytest.raises(ValueError, match="unmet dependencies"):
            tm.assign_task(task.id, "engineer")

    def test_cancel_task(self, tm):
        task = tm.create_task("Cancel me")
        tm.cancel_task(task.id)
        assert tm.get_task(task.id).status == TaskStatus.CANCELLED


class TestTaskExecution:
    def test_start_task(self, tm):
        task = tm.create_task("Start me")
        tm.assign_task(task.id, "engineer")
        tm.start_task(task.id)
        assert tm.get_task(task.id).status == TaskStatus.RUNNING

    def test_start_task_not_assigned(self, tm):
        task = tm.create_task("Not assigned")
        with pytest.raises(ValueError, match="not assigned"):
            tm.start_task(task.id)

    def test_complete_task(self, tm):
        task = tm.create_task("Complete me")
        tm.complete_task(task.id, result={"output": "success"})
        completed = tm.get_task(task.id)
        assert completed.status == TaskStatus.COMPLETED
        assert completed.result == {"output": "success"}

    def test_fail_task_retries(self, tm):
        task = tm.create_task("Fail me")
        # First failure -> PENDING (retry)
        tm.fail_task(task.id, "error 1")
        assert tm.get_task(task.id).status == TaskStatus.PENDING
        assert tm.get_task(task.id).retry_count == 1

    def test_fail_task_permanent_after_max_retries(self, tm):
        task = tm.create_task("Fail permanently")
        for i in range(task.max_retries):
            tm.fail_task(task.id, f"error {i+1}")
        final = tm.get_task(task.id)
        assert final.status == TaskStatus.FAILED
        assert final.retry_count == task.max_retries

    def test_retry_task(self, tm):
        task = tm.create_task("Retry me")
        for i in range(task.max_retries):
            tm.fail_task(task.id, f"error {i+1}")
        tm.retry_task(task.id)
        retried = tm.get_task(task.id)
        assert retried.status == TaskStatus.PENDING
        assert retried.retry_count == 0

    def test_retry_task_not_failed(self, tm):
        task = tm.create_task("Not failed")
        with pytest.raises(ValueError, match="not in FAILED status"):
            tm.retry_task(task.id)

    def test_get_executable_tasks(self, tm):
        dep = tm.create_task("Dep")
        t1 = tm.create_task("Ready", dependencies=[dep.id])
        t2 = tm.create_task("Also ready")
        # dep not completed -> t1 not executable
        executable = tm.get_executable_tasks()
        assert len(executable) == 1
        assert executable[0].id == t2.id
        # complete dep
        tm.complete_task(dep.id)
        executable = tm.get_executable_tasks()
        assert len(executable) == 2


class TestTaskStats:
    def test_get_task_stats_empty(self, tm):
        stats = tm.get_task_stats()
        assert stats["total_tasks"] == 0
        assert stats["completion_rate_pct"] == 0

    def test_get_task_stats(self, tm):
        tm.create_task("A")
        tm.create_task("B")
        t = tm.create_task("C")
        tm.complete_task(t.id)
        stats = tm.get_task_stats()
        assert stats["total_tasks"] == 3
        assert stats["total_completed"] == 1
        assert stats["completion_rate_pct"] == pytest.approx(33.33, abs=0.1)

    def test_generate_report(self, tm):
        report = tm.generate_report()
        assert "Task Manager Report" in report


class TestTaskPersistence:
    def test_persistence_across_restarts(self, tmp_project):
        tm1 = TaskManager(tmp_project)
        t = tm1.create_task("Persist me")
        tm1.assign_task(t.id, "agent")
        tm1.start_task(t.id)

        tm2 = TaskManager(tmp_project)
        loaded = tm2.get_task(t.id)
        assert loaded is not None
        assert loaded.status == TaskStatus.RUNNING
        assert loaded.assigned_agent == "agent"

    def test_export_tasks(self, tm, tmp_path):
        tm.create_task("Export me")
        filepath = str(tmp_path / "export.json")
        tm.export_tasks(filepath)
        with open(filepath) as f:
            data = json.load(f)
        assert "tasks" in data
        assert len(data["tasks"]) == 1
        assert "stats" in data

    def test_history_tracking(self, tm):
        task = tm.create_task("History task")
        tm.assign_task(task.id, "agent")
        tm.complete_task(task.id)
        history = tm.get_task_history(task.id)
        actions = [h["action"] for h in history]
        assert "created" in actions
        assert "assigned" in actions
        assert "completed" in actions


class TestTaskCleanup:
    def test_delete_task(self, tm):
        task = tm.create_task("Delete me")
        tm.delete_task(task.id)
        assert tm.get_task(task.id) is None

    def test_delete_task_not_found(self, tm):
        with pytest.raises(ValueError, match="Task not found"):
            tm.delete_task("nonexistent")

    def test_purge_completed(self, tm):
        t1 = tm.create_task("Completed 1")
        t2 = tm.create_task("Completed 2")
        tm.complete_task(t1.id)
        tm.complete_task(t2.id)
        tm.create_task("Pending")
        count = tm.purge_completed()
        assert count == 2
        assert len(tm.list_all_tasks()) == 1
