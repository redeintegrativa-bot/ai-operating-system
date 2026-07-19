"""Tests for the Memory system."""

import os
import json
import pytest
from datetime import datetime

from src.core.memory import MemorySystem, Memory, MemoryType


@pytest.fixture
def tmp_project(tmp_path):
    return str(tmp_path)


@pytest.fixture
def mem(tmp_project):
    return MemorySystem(tmp_project)


class TestMemoryAdd:
    def test_add_memory(self, mem):
        m = mem.add_memory("engineer", MemoryType.EPISODIC, {"task": "login"}, importance=0.8)
        assert m.agent_name == "engineer"
        assert m.memory_type == MemoryType.EPISODIC
        assert m.importance == 0.8
        assert m.id is not None
        assert m.access_count == 0

    def test_add_memory_defaults(self, mem):
        m = mem.add_memory("researcher", MemoryType.SEMANTIC, {"topic": "AI"})
        assert m.importance == 0.5
        assert m.keywords == []

    def test_add_memory_with_keywords(self, mem):
        m = mem.add_memory("ai", MemoryType.PROCEDURAL, {"step": 1}, keywords=["python", "async"])
        assert m.keywords == ["python", "async"]

    def test_add_memory_importance_validation(self, mem):
        with pytest.raises(ValueError, match="importance must be between"):
            mem.add_memory("x", MemoryType.EPISODIC, {}, importance=1.5)
        with pytest.raises(ValueError, match="importance must be between"):
            mem.add_memory("x", MemoryType.EPISODIC, {}, importance=-0.1)

    def test_add_multiple_memories(self, mem):
        for i in range(5):
            mem.add_memory("agent", MemoryType.EPISODIC, {"n": i})
        assert len(mem.get_memories("agent")) == 5


class TestMemoryRetrieval:
    def test_get_memories(self, mem):
        mem.add_memory("eng", MemoryType.EPISODIC, {"t": 1})
        mem.add_memory("eng", MemoryType.SEMANTIC, {"t": 2})
        mem.add_memory("res", MemoryType.EPISODIC, {"t": 3})

        eng = mem.get_memories("eng")
        assert len(eng) == 2

        episodic = mem.get_memories("eng", MemoryType.EPISODIC)
        assert len(episodic) == 1

    def test_get_memories_empty(self, mem):
        assert mem.get_memories("nobody") == []

    def test_get_memories_ordering(self, mem):
        m1 = mem.add_memory("a", MemoryType.EPISODIC, {"v": 1})
        m2 = mem.add_memory("a", MemoryType.EPISODIC, {"v": 2})
        memories = mem.get_memories("a")
        assert memories[0].id == m2.id  # most recent first


class TestMemorySearch:
    def test_search_by_keyword(self, mem):
        mem.add_memory("eng", MemoryType.SEMANTIC, {"topic": "python"}, keywords=["python", "programming"])
        mem.add_memory("eng", MemoryType.SEMANTIC, {"topic": "rust"}, keywords=["rust", "systems"])

        results = mem.search_memories("python programming")
        assert len(results) >= 1
        assert any("python" in m.keywords for m in results)

    def test_search_no_match(self, mem):
        mem.add_memory("eng", MemoryType.SEMANTIC, {"t": 1}, keywords=["python"], importance=0.0)
        results = mem.search_memories("blockchain solidity")
        assert len(results) == 0

    def test_search_filtered_by_agent(self, mem):
        mem.add_memory("eng", MemoryType.SEMANTIC, {"t": 1}, keywords=["python"])
        mem.add_memory("res", MemoryType.SEMANTIC, {"t": 2}, keywords=["python"])
        results = mem.search_memories("python", agent_name="eng")
        assert all(m.agent_name == "eng" for m in results)


class TestMemoryUpdate:
    def test_update_memory(self, mem):
        m = mem.add_memory("eng", MemoryType.EPISODIC, {"old": 1})
        updated = mem.update_memory(m.id, {"new": 2})
        assert updated.content == {"new": 2}

    def test_update_memory_not_found(self, mem):
        assert mem.update_memory("nonexistent", {"x": 1}) is None


class TestMemoryDelete:
    def test_delete_memory(self, mem):
        m = mem.add_memory("eng", MemoryType.EPISODIC, {"t": 1})
        assert mem.delete_memory(m.id) is True
        assert mem.get_memories("eng") == []

    def test_delete_memory_not_found(self, mem):
        assert mem.delete_memory("nonexistent") is False


class TestMemorySharing:
    def test_share_memory(self, mem):
        m = mem.add_memory("eng", MemoryType.SEMANTIC, {"knowledge": "python"}, keywords=["python"])
        shared = mem.share_memory(m.id, "res")
        assert shared.agent_name == "res"
        assert shared.content["_shared_from"] == "eng"
        assert shared.content["_original_id"] == m.id

    def test_share_memory_not_found(self, mem):
        assert mem.share_memory("nonexistent", "res") is None

    def test_get_shared_memories(self, mem):
        m = mem.add_memory("eng", MemoryType.EPISODIC, {"t": 1})
        mem.share_memory(m.id, "res")
        shared = mem.get_shared_memories("res")
        assert len(shared) == 1
        assert shared[0].content["_shared_from"] == "eng"


class TestMemoryConsolidation:
    def test_consolidate_similar_memories(self, mem):
        m1 = mem.add_memory("eng", MemoryType.SEMANTIC, {"a": 1}, keywords=["python", "async", "fastapi"])
        m2 = mem.add_memory("eng", MemoryType.SEMANTIC, {"a": 2}, keywords=["python", "async", "uvicorn"])
        count = mem.consolidate_memories("eng", threshold=0.3)
        assert count >= 1
        remaining = mem.get_memories("eng")
        assert len(remaining) == 1

    def test_consolidate_no_similar(self, mem):
        mem.add_memory("eng", MemoryType.SEMANTIC, {"a": 1}, keywords=["python"])
        mem.add_memory("eng", MemoryType.EPISODIC, {"a": 2}, keywords=["rust"])
        count = mem.consolidate_memories("eng")
        assert count == 0


class TestMemoryStats:
    def test_get_stats_empty(self, mem):
        stats = mem.get_stats()
        assert stats["total_memories"] == 0
        assert stats["avg_importance"] == 0

    def test_get_stats(self, mem):
        mem.add_memory("eng", MemoryType.EPISODIC, {"t": 1}, importance=0.6)
        mem.add_memory("eng", MemoryType.SEMANTIC, {"t": 2}, importance=0.8)
        mem.add_memory("res", MemoryType.EPISODIC, {"t": 3})
        stats = mem.get_stats()
        assert stats["total_memories"] == 3
        assert stats["by_agent"]["eng"] == 2
        assert stats["by_agent"]["res"] == 1


class TestMemoryPersistence:
    def test_persistence_across_instances(self, tmp_project):
        mem1 = MemorySystem(tmp_project)
        m = mem1.add_memory("eng", MemoryType.SEMANTIC, {"k": "v"}, keywords=["test"])

        mem2 = MemorySystem(tmp_project)
        loaded = mem2.get_memories("eng")
        assert len(loaded) == 1
        assert loaded[0].content["k"] == "v"
        assert loaded[0].keywords == ["test"]
