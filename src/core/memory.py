#!/usr/bin/env python3
"""Memory system for the AI Operating System.

Provides persistent memory for agents across sessions with support
for different memory types, search, consolidation, and sharing.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
from collections import Counter
from pathlib import Path
import json
import os
import uuid
import logging
import argparse
import sys
import textwrap


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("memory")


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

    def __str__(self) -> str:
        return self.value


@dataclass
class Memory:
    id: str
    agent_name: str
    memory_type: MemoryType
    content: Dict
    keywords: List[str]
    importance: float
    created_at: datetime
    last_accessed: datetime
    access_count: int

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["memory_type"] = self.memory_type.value
        d["created_at"] = self.created_at.isoformat()
        d["last_accessed"] = self.last_accessed.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "Memory":
        data["memory_type"] = MemoryType(data["memory_type"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["last_accessed"] = datetime.fromisoformat(data["last_accessed"])
        return cls(**data)

    def touch(self):
        self.last_accessed = datetime.now()
        self.access_count += 1

    def relevance_score(self, query_keywords: Set[str]) -> float:
        kw_set = set(k.lower() for k in self.keywords)
        if not query_keywords:
            return 0.0
        matches = len(kw_set & query_keywords)
        if matches == 0:
            return 0.0
        score = matches / max(len(query_keywords), 1)
        score += self.importance * 0.3
        recency = min((datetime.now() - self.last_accessed).total_seconds() / 86400, 365)
        score += (1 - recency / 365) * 0.1
        frequency = min(self.access_count / 100, 1) * 0.1
        return score + frequency


class MemorySystem:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.memory_dir = os.path.join(project_root, "memory")
        self.memories: Dict[str, Memory] = {}
        self._ensure_dirs()
        self.load_from_disk()

    def _ensure_dirs(self):
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(os.path.join(self.memory_dir, "agents"), exist_ok=True)
        os.makedirs(os.path.join(self.memory_dir, "shared"), exist_ok=True)

    def add_memory(
        self,
        agent_name: str,
        memory_type: MemoryType,
        content: Dict,
        keywords: Optional[List[str]] = None,
        importance: float = 0.5,
    ) -> Memory:
        if not 0.0 <= importance <= 1.0:
            raise ValueError("importance must be between 0.0 and 1.0")
        now = datetime.now()
        memory = Memory(
            id=str(uuid.uuid4()),
            agent_name=agent_name,
            memory_type=memory_type,
            content=content,
            keywords=keywords or [],
            importance=importance,
            created_at=now,
            last_accessed=now,
            access_count=0,
        )
        self.memories[memory.id] = memory
        self.save_to_disk()
        logger.info("Added memory %s for agent '%s' (type=%s, importance=%.2f)", memory.id, agent_name, memory_type, importance)
        return memory

    def get_memories(
        self, agent_name: str, memory_type: Optional[MemoryType] = None
    ) -> List[Memory]:
        result = []
        for m in self.memories.values():
            if m.agent_name == agent_name:
                if memory_type is None or m.memory_type == memory_type:
                    m.touch()
                    result.append(m)
        self.save_to_disk()
        return sorted(result, key=lambda m: m.created_at, reverse=True)

    def search_memories(
        self, query: str, agent_name: Optional[str] = None
    ) -> List[Memory]:
        query_keywords = set(k.lower().strip() for k in query.split() if k.strip())
        scored: List[Tuple[float, Memory]] = []
        for m in self.memories.values():
            if agent_name is not None and m.agent_name != agent_name:
                continue
            score = m.relevance_score(query_keywords)
            if score > 0:
                m.touch()
                scored.append((score, m))
        self.save_to_disk()
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    def update_memory(self, memory_id: str, content: Dict) -> Optional[Memory]:
        memory = self.memories.get(memory_id)
        if memory is None:
            logger.warning("Memory %s not found for update", memory_id)
            return None
        memory.content = content
        memory.touch()
        self.save_to_disk()
        logger.info("Updated memory %s", memory_id)
        return memory

    def delete_memory(self, memory_id: str) -> bool:
        if memory_id not in self.memories:
            logger.warning("Memory %s not found for deletion", memory_id)
            return False
        del self.memories[memory_id]
        self.save_to_disk()
        logger.info("Deleted memory %s", memory_id)
        return True

    def share_memory(self, memory_id: str, target_agent: str) -> Optional[Memory]:
        original = self.memories.get(memory_id)
        if original is None:
            logger.warning("Memory %s not found for sharing", memory_id)
            return None
        shared = Memory(
            id=str(uuid.uuid4()),
            agent_name=target_agent,
            memory_type=original.memory_type,
            content=original.content.copy(),
            keywords=original.keywords.copy(),
            importance=original.importance,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=0,
        )
        shared.content["_shared_from"] = original.agent_name
        shared.content["_original_id"] = memory_id
        self.memories[shared.id] = shared
        self.save_to_disk()
        logger.info("Shared memory %s from '%s' to '%s'", memory_id, original.agent_name, target_agent)
        return shared

    def get_shared_memories(self, agent_name: str) -> List[Memory]:
        return [m for m in self.memories.values() if m.agent_name == agent_name and "_shared_from" in m.content]

    def _compute_similarity(self, a: Memory, b: Memory) -> float:
        if a.memory_type != b.memory_type:
            return 0.0
        kw_a = set(k.lower() for k in a.keywords)
        kw_b = set(k.lower() for k in b.keywords)
        if not kw_a or not kw_b:
            return 0.0
        intersection = kw_a & kw_b
        union = kw_a | kw_b
        return len(intersection) / max(len(union), 1)

    def consolidate_memories(self, agent_name: str, threshold: float = 0.7):
        agent_memories = [
            m for m in self.memories.values()
            if m.agent_name == agent_name
        ]
        merged_ids: Set[str] = set()
        consolidations = 0

        for i, a in enumerate(agent_memories):
            if a.id in merged_ids:
                continue
            for b in agent_memories[i + 1 :]:
                if b.id in merged_ids:
                    continue
                if self._compute_similarity(a, b) >= threshold:
                    a.keywords = list(set(k.lower() for k in a.keywords + b.keywords))
                    a.content["_consolidated_from"] = a.content.get("_consolidated_from", []) + [b.id]
                    a.content["_merged_count"] = a.content.get("_merged_count", 1) + b.content.get("_merged_count", 1)
                    a.importance = max(a.importance, b.importance)
                    if b.access_count > a.access_count:
                        a.access_count = b.access_count
                    merged_ids.add(b.id)
                    consolidations += 1

        for mid in merged_ids:
            del self.memories[mid]

        if consolidations > 0:
            self.save_to_disk()
            logger.info("Consolidated %d memories for agent '%s'", consolidations, agent_name)
        return consolidations

    def get_stats(self) -> Dict:
        counts = Counter(m.memory_type.value for m in self.memories.values())
        agents = Counter(m.agent_name for m in self.memories.values())
        shared_count = sum(1 for m in self.memories.values() if "_shared_from" in m.content)
        now = datetime.now()
        old_memories = sum(
            1 for m in self.memories.values()
            if (now - m.last_accessed).total_seconds() > 7776000  # 90 days
        )
        return {
            "total_memories": len(self.memories),
            "by_type": dict(counts),
            "by_agent": dict(agents),
            "shared_memories": shared_count,
            "unused_90_days": old_memories,
            "avg_importance": round(
                sum(m.importance for m in self.memories.values()) / max(len(self.memories), 1), 3
            ),
            "total_access_count": sum(m.access_count for m in self.memories.values()),
        }

    def _memory_file_path(self, agent_name: str) -> str:
        return os.path.join(self.memory_dir, "agents", f"{agent_name}.json")

    def save_to_disk(self):
        agents_map: Dict[str, List[Dict]] = {}
        for memory in self.memories.values():
            agents_map.setdefault(memory.agent_name, []).append(memory.to_dict())

        for agent_name, memories_data in agents_map.items():
            filepath = self._memory_file_path(agent_name)
            try:
                with open(filepath, "w") as f:
                    json.dump(memories_data, f, indent=2, default=str)
            except (IOError, OSError) as e:
                logger.error("Failed to save memories for '%s': %s", agent_name, e)

        shared_memories = self._collect_shared()
        shared_path = os.path.join(self.memory_dir, "shared", "index.json")
        try:
            with open(shared_path, "w") as f:
                json.dump(shared_memories, f, indent=2, default=str)
        except (IOError, OSError) as e:
            logger.error("Failed to save shared index: %s", e)

    def _collect_shared(self) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        for memory in self.memories.values():
            src = memory.content.get("_shared_from")
            if src:
                result.setdefault(src, []).append(memory.id)
        return result

    def load_from_disk(self):
        agents_dir = os.path.join(self.memory_dir, "agents")
        if not os.path.isdir(agents_dir):
            return
        loaded = 0
        corrupted = 0
        for filename in os.listdir(agents_dir):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(agents_dir, filename)
            try:
                with open(filepath) as f:
                    data = json.load(f)
                for item in data:
                    try:
                        memory = Memory.from_dict(item)
                        self.memories[memory.id] = memory
                        loaded += 1
                    except (KeyError, ValueError, TypeError) as e:
                        corrupted += 1
                        logger.warning("Corrupted memory entry in %s: %s", filename, e)
            except (json.JSONDecodeError, IOError, OSError) as e:
                corrupted += 1
                logger.error("Failed to load %s: %s", filename, e)
        if loaded:
            logger.info("Loaded %d memories from disk (%d corrupted)", loaded, corrupted)


def cli_add(args):
    system = MemorySystem(args.root)
    try:
        mtype = MemoryType(args.memory_type)
    except ValueError:
        print(f"Invalid memory type. Choose from: {', '.join(t.value for t in MemoryType)}")
        return 1
    try:
        content = json.loads(args.content)
    except json.JSONDecodeError:
        content = {"text": args.content}
    memory = system.add_memory(args.agent_name, mtype, content, importance=args.importance)
    print(json.dumps({"id": memory.id, "agent_name": memory.agent_name, "type": str(mtype)}, indent=2))
    return 0


def cli_list(args):
    system = MemorySystem(args.root)
    mtype = MemoryType(args.memory_type) if args.memory_type else None
    memories = system.get_memories(args.agent_name, mtype)
    if not memories:
        print(f"No memories found for agent '{args.agent_name}'")
        return 0
    for m in memories:
        print(f"[{m.id[:8]}] {m.memory_type.value:12} imp={m.importance:.2f} "
              f"accessed={m.access_count:3d} keywords={m.keywords}")
        text = str(m.content.get("text", m.content))
        wrapped = textwrap.shorten(text, width=72, placeholder="...")
        print(f"      {wrapped}")
    return 0


def cli_search(args):
    system = MemorySystem(args.root)
    results = system.search_memories(args.query, args.agent_name)
    if not results:
        print("No matching memories found.")
        return 0
    print(f"Found {len(results)} memory result(s) for query: {args.query}\n")
    for m in results[: args.top]:
        print(f"[{m.id[:8]}] agent={m.agent_name:12} type={m.memory_type.value:12} imp={m.importance:.2f}")
        text = str(m.content.get("text", m.content))
        wrapped = textwrap.shorten(text, width=72, placeholder="...")
        print(f"      {wrapped}")
    return 0


def cli_stats(args):
    system = MemorySystem(args.root)
    stats = system.get_stats()
    print("=== Memory System Statistics ===")
    print(f"  Total memories:    {stats['total_memories']}")
    print(f"  By type:           {stats['by_type']}")
    print(f"  By agent:          {stats['by_agent']}")
    print(f"  Shared memories:   {stats['shared_memories']}")
    print(f"  Unused (90 days):  {stats['unused_90_days']}")
    print(f"  Avg importance:    {stats['avg_importance']}")
    print(f"  Total accesses:    {stats['total_access_count']}")
    return 0


def cli_delete(args):
    system = MemorySystem(args.root)
    if system.delete_memory(args.memory_id):
        print(f"Deleted memory {args.memory_id}")
    else:
        print(f"Memory {args.memory_id} not found", file=sys.stderr)
        return 1
    return 0


def cli_consolidate(args):
    system = MemorySystem(args.root)
    count = system.consolidate_memories(args.agent_name, args.threshold)
    print(f"Consolidated {count} memories for agent '{args.agent_name}'")
    return 0


def cli_share(args):
    system = MemorySystem(args.root)
    memory = system.share_memory(args.memory_id, args.target_agent)
    if memory:
        print(f"Shared memory {args.memory_id} with agent '{args.target_agent}'")
    else:
        print(f"Memory {args.memory_id} not found", file=sys.stderr)
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description="AI OS Memory System")
    parser.add_argument("--root", default=os.getcwd(), help="Project root directory (default: cwd)")

    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", aliases=["--add"])
    add_p.add_argument("agent_name", help="Agent name")
    add_p.add_argument("memory_type", help=f"Memory type: {', '.join(t.value for t in MemoryType)}")
    add_p.add_argument("content", help="Content (JSON string or plain text)")
    add_p.add_argument("--importance", type=float, default=0.5, help="Importance 0.0-1.0")
    add_p.set_defaults(func=cli_add)

    list_p = sub.add_parser("list", aliases=["--list"])
    list_p.add_argument("agent_name", help="Agent name")
    list_p.add_argument("--type", dest="memory_type", choices=[t.value for t in MemoryType], help="Filter by type")
    list_p.set_defaults(func=cli_list)

    search_p = sub.add_parser("search", aliases=["--search"])
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--agent", dest="agent_name", help="Filter by agent")
    search_p.add_argument("--top", type=int, default=10, help="Max results")
    search_p.set_defaults(func=cli_search)

    stats_p = sub.add_parser("stats", aliases=["--stats"])
    stats_p.set_defaults(func=cli_stats)

    delete_p = sub.add_parser("delete", aliases=["--delete"])
    delete_p.add_argument("memory_id", help="Memory ID to delete")
    delete_p.set_defaults(func=cli_delete)

    consolidate_p = sub.add_parser("consolidate", aliases=["--consolidate"])
    consolidate_p.add_argument("agent_name", help="Agent name")
    consolidate_p.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold 0.0-1.0")
    consolidate_p.set_defaults(func=cli_consolidate)

    share_p = sub.add_parser("share", aliases=["--share"])
    share_p.add_argument("memory_id", help="Memory ID to share")
    share_p.add_argument("target_agent", help="Target agent name")
    share_p.set_defaults(func=cli_share)

    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        logger.exception("Command failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
