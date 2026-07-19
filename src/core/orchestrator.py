"""Core Orchestrator Engine for the AI Operating System.

Routes tasks to appropriate agents, manages agent lifecycle,
tracks task execution, and integrates with the context system.
"""

import argparse
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("orchestrator")
logger.setLevel(logging.DEBUG)

_console = logging.StreamHandler(sys.stdout)
_console.setLevel(logging.INFO)
_console.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(_console)

_file_handler = logging.FileHandler(LOG_DIR / "orchestrator.log")
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
)
logger.addHandler(_file_handler)


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------

class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Agent:
    name: str
    capabilities: list[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    fallback: Optional[str] = None
    handler: Optional[Callable] = None
    tasks_completed: int = 0
    tasks_failed: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "fallback": self.fallback,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
        }


@dataclass
class Task:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    agent: Optional[str] = None
    result: Optional["TaskResult"] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    timeout: float = 300.0  # seconds

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "agent": self.agent,
            "result": self.result.to_dict() if self.result else None,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class TaskResult:
    success: bool = False
    output: Any = None
    errors: list[str] = field(default_factory=list)
    duration: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "errors": self.errors,
            "duration": self.duration,
        }


# ---------------------------------------------------------------------------
# Default agent definitions
# ---------------------------------------------------------------------------

DEFAULT_AGENTS: list[dict] = [
    {
        "name": "analyzer",
        "capabilities": ["analyze", "explore", "search", "inspect", "read"],
        "fallback": "coder",
    },
    {
        "name": "coder",
        "capabilities": [
            "implement", "fix", "code", "create", "write",
            "generate", "scaffold", "build", "develop", "refactor",
        ],
        "fallback": None,
    },
    {
        "name": "reviewer",
        "capabilities": ["review", "quality", "check", "audit", "validate"],
        "fallback": "analyzer",
    },
    {
        "name": "tester",
        "capabilities": ["test", "debug", "qa", "unit", "mock", "pytest"],
        "fallback": "analyzer",
    },
    {
        "name": "devops",
        "capabilities": [
            "deploy", "ci", "cd", "pipeline", "docker", "kubernetes",
            "git", "commit", "branch", "merge", "pr",
        ],
        "fallback": "coder",
    },
    {
        "name": "documenter",
        "capabilities": ["document", "changelog", "readme", "docs", "comment"],
        "fallback": "coder",
    },
    {
        "name": "security",
        "capabilities": ["security", "encrypt", "auth", "jwt", "session", "sanitize"],
        "fallback": "coder",
    },
    {
        "name": "architect",
        "capabilities": [
            "architect", "design", "system", "pattern", "structure", "ddd",
        ],
        "fallback": "coder",
    },
]


# ---------------------------------------------------------------------------
# Context System (lightweight)
# ---------------------------------------------------------------------------

class ContextSystem:
    """Loads and manages project context for agents."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self._cache: dict[str, Any] = {}

    def load_project_context(self) -> dict[str, Any]:
        if "project_context" in self._cache:
            return self._cache["project_context"]

        context: dict[str, Any] = {
            "project_root": str(self.project_root),
            "files": [],
            "config": {},
        }

        # Gather top-level files
        if self.project_root.exists():
            for item in sorted(self.project_root.iterdir()):
                context["files"].append(item.name)

        # Try loading common config files
        for cfg_name in ("config.json", "config.yaml", "config.toml"):
            cfg_path = self.project_root / cfg_name
            if cfg_path.exists():
                try:
                    if cfg_name.endswith(".json"):
                        context["config"] = json.loads(cfg_path.read_text())
                    else:
                        context["config"]["_raw"] = cfg_path.read_text()
                except Exception as exc:
                    logger.warning("Could not parse %s: %s", cfg_name, exc)

        self._cache["project_context"] = context
        return context

    def build_prompt_context(self) -> str:
        ctx = self.load_project_context()
        parts = [f"Project root: {ctx['project_root']}"]
        if ctx["files"]:
            parts.append(f"Top-level items: {', '.join(ctx['files'][:30])}")
        if ctx["config"]:
            parts.append(f"Config keys: {', '.join(ctx['config'].keys())}")
        return "\n".join(parts)

    def update_after_task(self, task: Task) -> None:
        self._cache.pop("project_context", None)
        logger.debug("Context cache invalidated after task %s", task.id)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    """Main engine that routes tasks to the appropriate agents."""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.agents: dict[str, Agent] = {}
        self.task_queue: list[Task] = []
        self.completed_tasks: list[Task] = []
        self.context_system = ContextSystem(project_root)
        self._load_agents()

    # -- Agent Management ---------------------------------------------------

    def _load_agents(self) -> None:
        """Load available agents from default definitions or config file."""
        config_path = Path(self.project_root) / "agents.json"
        agent_defs: list[dict] = []

        if config_path.exists():
            try:
                agent_defs = json.loads(config_path.read_text())
                logger.info("Loaded agent definitions from %s", config_path)
            except Exception as exc:
                logger.warning("Failed to parse agents.json: %s – using defaults", exc)

        if not agent_defs:
            agent_defs = DEFAULT_AGENTS

        for defn in agent_defs:
            agent = Agent(
                name=defn["name"],
                capabilities=defn.get("capabilities", []),
                fallback=defn.get("fallback"),
            )
            self.agents[agent.name] = agent

        logger.info(
            "Loaded %d agents: %s",
            len(self.agents),
            ", ".join(self.agents.keys()),
        )

    def get_agent(self, name: str) -> Optional[Agent]:
        return self.agents.get(name)

    def set_agent_status(self, name: str, status: AgentStatus) -> None:
        agent = self.agents.get(name)
        if agent:
            agent.status = status
            logger.debug("Agent %s status -> %s", name, status.value)

    # -- Task Routing -------------------------------------------------------

    def route_task(self, task: Task) -> Agent:
        """Determine which agent should handle this task based on keywords."""
        description_lower = task.description.lower()
        scores: dict[str, int] = {name: 0 for name in self.agents}

        for agent_name, agent in self.agents.items():
            for cap in agent.capabilities:
                if cap in description_lower:
                    scores[agent_name] += 1

        # Pick highest-scoring agent; prefer idle agents
        candidates = sorted(
            scores.items(), key=lambda kv: kv[1], reverse=True
        )

        best_agent: Optional[Agent] = None
        for name, score in candidates:
            if score == 0:
                continue
            agent = self.agents[name]
            if agent.status == AgentStatus.FAILED:
                continue
            if agent.status == AgentStatus.IDLE:
                best_agent = agent
                break
            # If best match is busy, still pick it (queue semantics)
            if best_agent is None:
                best_agent = agent

        if best_agent is None:
            # Fallback to coder
            best_agent = self.agents.get("coder")
            if best_agent is None:
                raise RuntimeError("No agents available and no fallback defined")
            logger.warning(
                "No matching agent for '%s' – falling back to '%s'",
                task.description[:60],
                best_agent.name,
            )

        task.agent = best_agent.name
        logger.info(
            "Task %s routed to agent '%s' (score=%d)",
            task.id,
            best_agent.name,
            scores.get(best_agent.name, 0),
        )
        return best_agent

    def _handle_agent_failure(self, task: Task, agent: Agent) -> Agent:
        """Attempt to recover by switching to the fallback agent."""
        agent.status = AgentStatus.FAILED
        agent.tasks_failed += 1
        logger.error("Agent '%s' failed task %s", agent.name, task.id)

        if agent.fallback and agent.fallback in self.agents:
            fallback = self.agents[agent.fallback]
            if fallback.status != AgentStatus.FAILED:
                task.agent = fallback.name
                logger.info(
                    "Task %s reassigned to fallback agent '%s'",
                    task.id,
                    fallback.name,
                )
                return fallback

        logger.error("No fallback available for agent '%s'", agent.name)
        return agent

    # -- Task Execution -----------------------------------------------------

    def execute_task(self, task: Task) -> TaskResult:
        """Execute a task through the assigned agent."""
        start = time.monotonic()
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc).isoformat()

        agent = self.agents.get(task.agent)
        if agent is None:
            task.status = TaskStatus.FAILED
            result = TaskResult(
                success=False, errors=[f"Agent '{task.agent}' not found"]
            )
            task.result = result
            return result

        self.set_agent_status(task.agent, AgentStatus.BUSY)

        # Build context
        prompt_ctx = self.context_system.build_prompt_context()
        logger.debug("Context for task %s:\n%s", task.id, prompt_ctx)

        # Simulate execution via handler or default behavior
        try:
            if agent.handler and callable(agent.handler):
                output = agent.handler(task.description, context=prompt_ctx)
            else:
                output = self._default_execute(agent, task, prompt_ctx)

            elapsed = time.monotonic() - start
            if elapsed > task.timeout:
                raise TimeoutError(
                    f"Task {task.id} exceeded timeout of {task.timeout}s"
                )

            result = TaskResult(success=True, output=output, duration=elapsed)
            task.status = TaskStatus.COMPLETED
            agent.tasks_completed += 1
            logger.info(
                "Task %s completed by '%s' in %.2fs",
                task.id,
                agent.name,
                elapsed,
            )

        except TimeoutError as exc:
            elapsed = time.monotonic() - start
            result = TaskResult(
                success=False,
                errors=[str(exc)],
                duration=elapsed,
            )
            task.status = TaskStatus.FAILED
            agent = self._handle_agent_failure(task, agent)

        except Exception as exc:
            elapsed = time.monotonic() - start
            result = TaskResult(
                success=False,
                errors=[str(exc)],
                duration=elapsed,
            )
            task.status = TaskStatus.FAILED
            agent = self._handle_agent_failure(task, agent)

        finally:
            self.set_agent_status(task.agent, AgentStatus.IDLE)
            task.completed_at = datetime.now(timezone.utc).isoformat()
            task.result = result
            self.context_system.update_after_task(task)

        return result

    def _default_execute(
        self, agent: Agent, task: Task, context: str
    ) -> str:
        """Default execution stub when no handler is registered."""
        return (
            f"[{agent.name}] Processed task '{task.description}' "
            f"with project context ({len(context)} chars)"
        )

    # -- Queue Management ---------------------------------------------------

    def submit_task(self, task: Task) -> Task:
        """Add a task to the queue and attempt routing."""
        self.route_task(task)
        self.task_queue.append(task)
        logger.info("Task %s enqueued (queue size: %d)", task.id, len(self.task_queue))
        return task

    def run_next(self) -> Optional[TaskResult]:
        """Execute the next pending task in the queue."""
        for task in self.task_queue:
            if task.status == TaskStatus.PENDING:
                result = self.execute_task(task)
                self.completed_tasks.append(task)
                return result
        logger.info("No pending tasks in queue")
        return None

    def run_all(self) -> list[TaskResult]:
        """Execute all pending tasks sequentially."""
        results: list[TaskResult] = []
        while True:
            result = self.run_next()
            if result is None:
                break
            results.append(result)
        return results

    # -- Status & Reporting -------------------------------------------------

    def get_status(self) -> dict:
        """Get orchestrator status overview."""
        return {
            "project_root": self.project_root,
            "agents": {name: a.to_dict() for name, a in self.agents.items()},
            "queue_size": len(self.task_queue),
            "pending": sum(
                1 for t in self.task_queue if t.status == TaskStatus.PENDING
            ),
            "completed": len(self.completed_tasks),
            "total_submitted": len(self.task_queue),
        }

    def get_task_history(self) -> list[dict]:
        """Return history of all completed/failed tasks."""
        all_tasks = self.completed_tasks + [
            t for t in self.task_queue if t.status == TaskStatus.FAILED
        ]
        return [t.to_dict() for t in all_tasks]

    def print_status(self) -> None:
        """Pretty-print orchestrator status."""
        status = self.get_status()
        print("\n=== AI Operating System — Orchestrator Status ===\n")
        print(f"  Project root : {status['project_root']}")
        print(f"  Queue size   : {status['queue_size']}")
        print(f"  Pending      : {status['pending']}")
        print(f"  Completed    : {status['completed']}")
        print(f"  Total        : {status['total_submitted']}")
        print()
        print("  Agents:")
        for name, info in status["agents"].items():
            caps = ", ".join(info["capabilities"][:5])
            if len(info["capabilities"]) > 5:
                caps += ", ..."
            fb = f" (fallback: {info['fallback']})" if info["fallback"] else ""
            print(
                f"    {name:<14} | status={info['status']:<6} "
                f"| done={info['tasks_completed']} fail={info['tasks_failed']}{fb}"
            )
            print(f"    {'':14} | caps: {caps}")
        print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI Operating System — Core Orchestrator Engine",
    )
    parser.add_argument(
        "--project-root",
        default=os.getcwd(),
        help="Path to the project root (default: cwd)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show orchestrator status and exit",
    )
    parser.add_argument(
        "--route",
        type=str,
        metavar="DESCRIPTION",
        help="Route a task description to an agent and print the result",
    )
    parser.add_argument(
        "--execute",
        type=str,
        metavar="DESCRIPTION",
        help="Route and execute a task, printing the result",
    )
    parser.add_argument(
        "--agents-json",
        type=str,
        help="Path to a custom agents.json configuration file",
    )
    return parser


def main() -> None:
    parser = _build_cli_parser()
    args = parser.parse_args()

    # If a custom agents.json is given, copy it to project root temporarily
    if args.agents_json:
        src = Path(args.agents_json).resolve()
        dst = Path(args.project_root) / "agents.json"
        dst.write_text(src.read_text())
        logger.info("Copied custom agents config from %s", src)

    orch = Orchestrator(args.project_root)

    if args.status:
        orch.print_status()
        return

    if args.route:
        task = Task(description=args.route)
        agent = orch.route_task(task)
        print(f"\nTask {task.id} routed to agent: {agent.name}")
        print(f"Description: {task.description}")
        print(f"Agent capabilities: {', '.join(agent.capabilities)}")
        return

    if args.execute:
        task = Task(description=args.execute)
        orch.submit_task(task)
        result = orch.run_next()
        if result:
            print(f"\nTask {task.id} result:")
            print(f"  Success : {result.success}")
            print(f"  Output  : {result.output}")
            print(f"  Errors  : {result.errors or 'none'}")
            print(f"  Duration: {result.duration:.3f}s")
        else:
            print("No result produced.")
        return

    # Default: show status
    orch.print_status()


if __name__ == "__main__":
    main()
