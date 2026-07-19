"""Tests for the Event System."""

import os
import json
import tempfile
import threading
import time
import pytest
from datetime import datetime

from src.core.events import EventBus, Event, EventType, EventFilter, Subscription, create_event


@pytest.fixture
def bus():
    return EventBus(max_history=100)


@pytest.fixture
def tmp_file(tmp_path):
    return str(tmp_path / "events.json")


class TestEventCreation:
    def test_create_event(self):
        e = create_event(EventType.TASK_CREATED, "test", {"id": "123"})
        assert e.event_type == EventType.TASK_CREATED
        assert e.source == "test"
        assert e.data == {"id": "123"}
        assert e.id is not None
        assert isinstance(e.timestamp, datetime)

    def test_create_event_with_metadata(self):
        e = create_event(EventType.AGENT_STARTED, "agent", {"name": "eng"}, metadata={"env": "prod"})
        assert e.metadata["env"] == "prod"

    def test_event_to_dict(self):
        e = create_event(EventType.TASK_COMPLETED, "test", {"result": "ok"})
        d = e.to_dict()
        assert d["event_type"] == "task.completed"
        assert d["source"] == "test"

    def test_event_from_dict(self):
        original = create_event(EventType.TASK_FAILED, "test", {"error": "timeout"})
        d = original.to_dict()
        restored = Event.from_dict(d)
        assert restored.event_type == EventType.TASK_FAILED
        assert restored.data == {"error": "timeout"}
        assert restored.source == "test"


class TestEventBusPublishing:
    def test_publish_sync(self, bus):
        e = create_event(EventType.TASK_CREATED, "test", {})
        bus.publish(e)
        history = bus.get_history()
        assert len(history) == 1
        assert history[0].id == e.id

    def test_publish_async(self, bus):
        bus.start()
        e = create_event(EventType.TASK_CREATED, "test", {})
        bus.publish(e, async_mode=True)
        time.sleep(0.2)
        bus.stop()
        history = bus.get_history()
        assert len(history) == 1

    def test_create_and_publish(self, bus):
        eid = bus.create_and_publish(EventType.TASK_COMPLETED, "test", {"ok": True})
        assert eid is not None
        history = bus.get_history()
        assert len(history) == 1

    def test_publish_increments_stats(self, bus):
        e = create_event(EventType.TASK_CREATED, "test", {})
        bus.publish(e)
        stats = bus.get_stats()
        assert stats["published"] == 1
        assert stats["processed"] == 1


class TestEventBusSubscribing:
    def test_subscribe_and_receive(self, bus):
        received = []
        bus.subscribe(EventType.TASK_CREATED.value, lambda e: received.append(e))
        bus.create_and_publish(EventType.TASK_CREATED, "test", {"id": "1"})
        assert len(received) == 1
        assert received[0].data["id"] == "1"

    def test_wildcard_subscription(self, bus):
        received = []
        bus.subscribe("*", lambda e: received.append(e))
        bus.create_and_publish(EventType.TASK_CREATED, "test", {})
        bus.create_and_publish(EventType.AGENT_STARTED, "test", {})
        assert len(received) == 2

    def test_unsubscribe(self, bus):
        received = []
        sub_id = bus.subscribe(EventType.TASK_CREATED.value, lambda e: received.append(e))
        bus.create_and_publish(EventType.TASK_CREATED, "test", {})
        assert len(received) == 1
        bus.unsubscribe(EventType.TASK_CREATED.value, sub_id)
        bus.create_and_publish(EventType.TASK_CREATED, "test", {})
        assert len(received) == 1  # no new event

    def test_priority_ordering(self, bus):
        order = []
        bus.subscribe(EventType.TASK_CREATED.value, lambda e: order.append("low"), priority=1)
        bus.subscribe(EventType.TASK_CREATED.value, lambda e: order.append("high"), priority=10)
        bus.create_and_publish(EventType.TASK_CREATED, "test", {})
        assert order == ["high", "low"]


class TestEventBusFiltering:
    def test_event_filter_by_source(self, bus):
        received = []
        f = EventFilter(source_pattern="agent")
        bus.subscribe(EventType.TASK_CREATED.value, lambda e: received.append(e), event_filter=f)
        bus.create_and_publish(EventType.TASK_CREATED, "agent-engineer", {})
        bus.create_and_publish(EventType.TASK_CREATED, "cli", {})
        assert len(received) == 1

    def test_event_filter_by_type_set(self, bus):
        received = []
        f = EventFilter(event_types={EventType.TASK_CREATED, EventType.TASK_FAILED})
        bus.subscribe("*", lambda e: received.append(e), event_filter=f)
        bus.create_and_publish(EventType.TASK_CREATED, "test", {})   # matches filter
        bus.create_and_publish(EventType.AGENT_STARTED, "test", {})  # filtered out
        bus.create_and_publish(EventType.TASK_FAILED, "test", {})    # matches filter
        assert len(received) == 2

    def test_event_filter_by_data(self, bus):
        received = []
        f = EventFilter(data_filter=lambda d: d.get("priority") == "high")
        bus.subscribe(EventType.TASK_CREATED.value, lambda e: received.append(e), event_filter=f)
        bus.create_and_publish(EventType.TASK_CREATED, "test", {"priority": "low"})
        bus.create_and_publish(EventType.TASK_CREATED, "test", {"priority": "high"})
        assert len(received) == 1


class TestEventBusHistory:
    def test_history_limit(self):
        small_bus = EventBus(max_history=5)
        for i in range(10):
            small_bus.create_and_publish(EventType.TASK_CREATED, "test", {"i": i})
        history = small_bus.get_history()
        assert len(history) == 5

    def test_history_filter_by_type(self, bus):
        bus.create_and_publish(EventType.TASK_CREATED, "test", {})
        bus.create_and_publish(EventType.AGENT_STARTED, "test", {})
        bus.create_and_publish(EventType.TASK_CREATED, "test", {})
        task_events = bus.get_history(event_type=EventType.TASK_CREATED)
        assert len(task_events) == 2

    def test_history_with_limit(self, bus):
        for i in range(10):
            bus.create_and_publish(EventType.TASK_CREATED, "test", {"i": i})
        limited = bus.get_history(limit=3)
        assert len(limited) == 3

    def test_clear_history(self, bus):
        bus.create_and_publish(EventType.TASK_CREATED, "test", {})
        bus.clear_history()
        assert bus.get_history() == []


class TestEventBusArchive:
    def test_archive_and_load(self, bus, tmp_file):
        bus.create_and_publish(EventType.TASK_CREATED, "test", {"id": 1})
        bus.create_and_publish(EventType.AGENT_STARTED, "test", {"name": "eng"})
        count = bus.archive_events(tmp_file)
        assert count == 2

        new_bus = EventBus()
        loaded = new_bus.load_archive(tmp_file)
        assert loaded == 2
        assert len(new_bus.get_history()) == 2

    def test_archive_empty(self, bus, tmp_file):
        count = bus.archive_events(tmp_file)
        assert count == 0


class TestEventBusLifecycle:
    def test_start_stop(self, bus):
        bus.start()
        assert bus.running is True
        bus.stop()
        assert bus.running is False

    def test_start_already_running(self, bus):
        bus.start()
        bus.start()  # should not raise
        bus.stop()

    def test_async_processing(self, bus):
        bus.start()
        results = []

        def handler(e):
            results.append(e.data["value"])

        bus.subscribe(EventType.TASK_CREATED.value, handler)
        for i in range(5):
            bus.publish(
                create_event(EventType.TASK_CREATED, "test", {"value": i}),
                async_mode=True,
            )
        time.sleep(0.5)
        bus.stop()
        assert sorted(results) == [0, 1, 2, 3, 4]


class TestEventBusStats:
    def test_get_stats(self, bus):
        bus.subscribe(EventType.TASK_CREATED.value, lambda e: None)
        bus.create_and_publish(EventType.TASK_CREATED, "test", {})
        stats = bus.get_stats()
        assert stats["published"] == 1
        assert stats["processed"] == 1
        assert stats["subscribers"] == 1
        assert stats["history_size"] == 1

    def test_stats_reflect_errors(self, bus):
        def bad_handler(e):
            raise RuntimeError("boom")

        bus.subscribe(EventType.TASK_CREATED.value, bad_handler)
        bus.create_and_publish(EventType.TASK_CREATED, "test", {})
        stats = bus.get_stats()
        assert stats["errors"] == 1


class TestEventBusReplay:
    def test_replay(self, bus):
        received = []
        bus.subscribe(EventType.TASK_CREATED.value, lambda e: received.append(e))
        # Create events manually
        for i in range(3):
            e = create_event(EventType.TASK_CREATED, "test", {"i": i})
            bus._add_to_history(e)
        bus.replay_events(delay=0.01)
        assert len(received) == 3
