"""System Core — Initializes and manages the AI Operating System.

Ties together all subsystems: config, logging, kernel, orchestrator,
memory, task manager, event bus, monitoring, and context.
Handles system startup, shutdown, health monitoring, and graceful
degradation.
"""

import os
import sys
import time
import argparse
import signal
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.config_manager import ConfigManager
from src.utils.logger import setup_logging, get_logger
from src.core.kernel import AIOSKernel, create_default_kernel
from src.core.orchestrator import Orchestrator
from src.core.events import EventBus
from src.core.task_manager import TaskManager
from src.core.memory import MemorySystem
from src.core.monitoring import Monitor
from src.core.suggestions import SuggestionInbox


class AIOS:
    """Top-level system orchestrator.

    Initializes all subsystems, wires them together, and manages
    the system lifecycle. On startup, it loads persisted state
    (agent configs, memories, tasks, suggestions, session context)
    so new agent sessions resume with maximum context.
    """

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd()).resolve()
        self._running = False
        self._start_time: float = 0.0

        # Load config first
        self.config = ConfigManager(str(self.project_root))

        # Setup logging
        log_level = self.config.get("system.log_level", "INFO")
        setup_logging(str(self.project_root), log_level)
        self.logger = get_logger("system")

        # Initialize subsystems
        self.logger.info("Initializing AIOS subsystems...")

        # Context scripts dir for reconstruct_context.py
        self._context_scripts = self.project_root / "context" / "scripts"
        self._generated_dir = self.project_root / "context" / "generated"

        # Agent kernel (modes, heartbeats, scheduler)
        self.kernel = create_default_kernel(str(self.project_root))

        # Task router (keyword-based routing)
        self.orchestrator = Orchestrator(str(self.project_root))

        # Wire kernel <-> orchestrator
        self.kernel.set_orchestrator(self.orchestrator)

        # Event bus
        self.event_bus = EventBus()
        self.kernel.set_event_bus(self.event_bus)

        # Task manager (persistent tasks)
        self.task_manager = TaskManager(str(self.project_root))

        # Memory system (agent memories)
        self.memory = MemorySystem(str(self.project_root))

        # Monitoring
        self.monitor = Monitor(str(self.project_root))
        self.kernel.set_monitor(self.monitor)

        # Suggestion inbox
        self.suggestions = SuggestionInbox(str(self.project_root))

        # Ensure context/generated dir exists
        self._generated_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(
            "AIOS initialized: agents=%d, tasks=%d, memories=%d, suggestions=%d",
            len(self.kernel.agent_manager.get_all()),
            len(self.task_manager.list_all_tasks()),
            len(self.memory.memories),
            len(self.suggestions.get_all()),
        )

    # ------------------------------------------------------------------
    # Startup — refresh context and prune stale data
    # ------------------------------------------------------------------

    def _refresh_context(self) -> bool:
        """Run reconstruct_context.py to regenerate project snapshot."""
        reconstruct = self._context_scripts / "reconstruct_context.py"
        if not reconstruct.exists():
            self.logger.warning("reconstruct_context.py not found, skipping context refresh")
            return False
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(reconstruct),
                 "--project-root", str(self.project_root),
                 "--quiet"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                self.logger.info("Project context refreshed")
                return True
            self.logger.warning("Context refresh failed: %s", result.stderr[:200])
            return False
        except Exception as e:
            self.logger.warning("Context refresh error: %s", e)
            return False

    def _prune_stale_memories(self) -> int:
        """Remove memories not accessed in 90 days, consolidate similar."""
        count = self.memory.consolidate_memories("system", threshold=0.75)
        stale = 0
        for mem_id in list(self.memory.memories.keys()):
            mem = self.memory.memories[mem_id]
            age = (time.time() - mem.last_accessed.timestamp()) / 86400
            if age > 90:
                self.memory.delete_memory(mem_id)
                stale += 1
        if stale:
            self.logger.info("Pruned %d stale memories (90+ days)", stale)
        if count:
            self.logger.info("Consolidated %d similar memories", count)
        return stale + count

    def _prune_stale_tasks(self) -> int:
        """Archive completed tasks older than 7 days."""
        import datetime
        now = datetime.datetime.now()
        purged = 0
        for task in self.task_manager.list_all_tasks():
            age = (now - task.created_at).total_seconds() / 86400
            if age > 7 and task.status.value in ("completed", "failed", "cancelled"):
                self.task_manager.delete_task(task.id)
                purged += 1
        if purged:
            self.logger.info("Purged %d stale completed/failed tasks (>7 days)", purged)
        return purged

    def start(self) -> None:
        """Start the system — loads persisted state and starts subsystems."""
        if self._running:
            self.logger.warning("AIOS already running")
            return

        self._start_time = time.time()

        # Refresh context snapshot
        self._refresh_context()

        # Prune stale data on startup
        self._prune_stale_memories()
        self._prune_stale_tasks()

        # Start subsystems
        self.event_bus.start()
        self.kernel.start()

        self._running = True
        self.logger.info(
            "AIOS started — project=%s, agents=%d, active_memories=%d, pending_tasks=%d",
            self.project_root.name,
            len(self.kernel.agent_manager.get_all()),
            len(self.memory.memories),
            len(self.task_manager.get_pending_tasks()),
        )

    def stop(self) -> None:
        """Gracefully stop all subsystems."""
        if not self._running:
            return
        self.logger.info("AIOS shutting down...")
        self.kernel.stop()
        self.event_bus.stop()
        self._running = False
        self.logger.info("AIOS stopped (uptime=%.0fs)", time.time() - self._start_time)

    # ------------------------------------------------------------------
    # Task submission
    # ------------------------------------------------------------------

    def submit_task(
        self,
        description: str,
        priority: str = "medium",
        agents: Optional[List[str]] = None,
    ) -> Any:
        priority_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        from src.core.task_manager import TaskPriority as TMPriority

        prio = TMPriority(priority_map.get(priority, 2))

        task = self.task_manager.create_task(
            description=description,
            priority=prio,
        )
        self.monitor.record_metric("task.created", 1, {"priority": priority})

        if agents:
            task.assigned_agent = agents[0]

        self.event_bus.create_and_publish(
            event_type="task.created",
            source="system",
            data={"task_id": task.id, "description": description},
            async_mode=True,
        )
        return task

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "uptime_seconds": time.time() - self._start_time if self._start_time else 0,
            "project": self.project_root.name,
            "kernel": self.kernel.get_status(),
            "orchestrator": self.orchestrator.get_status(),
            "event_bus": self.event_bus.get_stats(),
            "task_manager": self.task_manager.get_task_stats(),
            "memory": self.memory.get_stats(),
            "suggestions": self.suggestions.get_stats(),
            "monitor": self.monitor.generate_report(),
        }


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="AI Operating System")
    parser.add_argument("--project-root", default=os.getcwd(), help="Project root directory")
    parser.add_argument("--interactive", action="store_true", help="Start in interactive mode")
    parser.add_argument("--task", type=str, help="Execute a single task and exit")
    parser.add_argument("--status", action="store_true", help="Show system status and exit")

    args = parser.parse_args()

    aios = AIOS(project_root=args.project_root)

    if args.status:
        import json
        print(json.dumps(aios.get_status(), indent=2, default=str))
        return

    if args.task:
        aios.start()
        result = aios.submit_task(args.task)
        print(f"Task {result.id[:8]} created: {result.description[:60]}")
        aios.stop()
        return

    if args.interactive:
        aios.start()
        try:
            while True:
                cmd = input("aios> ").strip()
                if cmd in ("exit", "quit", "q"):
                    break
                if cmd == "status":
                    import json
                    print(json.dumps(aios.get_status(), indent=2, default=str))
                    continue
                if cmd.startswith("task "):
                    desc = cmd[5:]
                    t = aios.submit_task(desc)
                    print(f"Task {t.id[:8]} created")
                    continue
                if cmd == "help":
                    print("Commands: status, task <description>, help, exit")
                    continue
                print(f"Unknown command: {cmd}")
        except (EOFError, KeyboardInterrupt):
            pass
        finally:
            aios.stop()
        return

    # Default: start and detach
    aios.start()
    print(f"AIOS running. PID: {os.getpid()}")
    print(f"Project: {aios.project_root}")
    print("Press Ctrl+C to stop.")

    def _signal_handler(sig, frame):
        aios.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        signal.pause()
    except AttributeError:
        import threading
        threading.Event().wait()


if __name__ == "__main__":
    main()
