from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json
import os
import logging
import argparse
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("task_manager")


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    CREATED = "created"
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
    assigned_agent: Optional[str] = None
    result: Optional[Dict] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "assigned_agent": self.assigned_agent,
            "result": self.result,
            "errors": self.errors,
            "metadata": self.metadata,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "dependencies": self.dependencies,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        return cls(
            id=data["id"],
            description=data["description"],
            status=TaskStatus(data["status"]),
            priority=TaskPriority(data["priority"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            assigned_agent=data.get("assigned_agent"),
            result=data.get("result"),
            errors=data.get("errors", []),
            metadata=data.get("metadata", {}),
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            dependencies=data.get("dependencies", []),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds"),
        )


class TaskManager:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.tasks: Dict[str, Task] = {}
        self.task_history: List[Dict] = []
        self._data_dir = os.path.join(project_root, ".task_manager")
        self._tasks_file = os.path.join(self._data_dir, "tasks.json")
        self._history_file = os.path.join(self._data_dir, "history.json")
        os.makedirs(self._data_dir, exist_ok=True)
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self):
        if os.path.exists(self._tasks_file):
            try:
                with open(self._tasks_file, "r") as f:
                    raw = json.load(f)
                self.tasks = {k: Task.from_dict(v) for k, v in raw.items()}
                logger.info("Loaded %d tasks from %s", len(self.tasks), self._tasks_file)
            except Exception as exc:
                logger.error("Failed to load tasks: %s", exc)

        if os.path.exists(self._history_file):
            try:
                with open(self._history_file, "r") as f:
                    self.task_history = json.load(f)
                logger.info("Loaded %d history entries", len(self.task_history))
            except Exception as exc:
                logger.error("Failed to load history: %s", exc)

    def _save(self):
        try:
            with open(self._tasks_file, "w") as f:
                json.dump({k: v.to_dict() for k, v in self.tasks.items()}, f, indent=2)
            with open(self._history_file, "w") as f:
                json.dump(self.task_history, f, indent=2)
        except Exception as exc:
            logger.error("Failed to save tasks: %s", exc)

    # ------------------------------------------------------------------
    # Task Creation
    # ------------------------------------------------------------------

    def create_task(
        self,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        deadline: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Task:
        now = datetime.now()
        task = Task(
            id=str(uuid.uuid4()),
            description=description,
            status=TaskStatus.CREATED,
            priority=priority,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
            deadline=deadline,
            dependencies=dependencies or [],
            timeout_seconds=timeout_seconds,
        )
        self.tasks[task.id] = task
        self._log_history(task.id, "created", {"description": description, "priority": priority.name})
        self._save()
        logger.info("Created task %s [%s] priority=%s", task.id[:8], description[:40], priority.name)
        return task

    # ------------------------------------------------------------------
    # Task Queries
    # ------------------------------------------------------------------

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def find_task_by_prefix(self, prefix: str) -> Optional[Task]:
        for tid, task in self.tasks.items():
            if tid.startswith(prefix):
                return task
        return None

    def get_pending_tasks(self) -> List[Task]:
        return [
            t for t in self.tasks.values()
            if t.status in (TaskStatus.CREATED, TaskStatus.PENDING)
        ]

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        return [t for t in self.tasks.values() if t.status == status]

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        return [t for t in self.tasks.values() if t.priority == priority]

    def get_tasks_by_agent(self, agent_name: str) -> List[Task]:
        return [t for t in self.tasks.values() if t.assigned_agent == agent_name]

    def list_all_tasks(self) -> List[Task]:
        return list(self.tasks.values())

    # ------------------------------------------------------------------
    # Task Updates
    # ------------------------------------------------------------------

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ):
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        old_status = task.status
        task.status = status
        task.updated_at = datetime.now()

        if result is not None:
            task.result = result
        if error is not None:
            task.errors.append(error)

        self._log_history(task_id, "status_change", {
            "from": old_status.value,
            "to": status.value,
        })
        self._save()
        logger.info("Task %s status: %s -> %s", task_id[:8], old_status.value, status.value)

    def assign_task(self, task_id: str, agent_name: str):
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        unmet = [dep for dep in task.dependencies if dep in self.tasks and self.tasks[dep].status != TaskStatus.COMPLETED]
        if unmet:
            raise ValueError(f"Task {task_id[:8]} has unmet dependencies: {unmet}")

        task.assigned_agent = agent_name
        task.status = TaskStatus.ASSIGNED
        task.updated_at = datetime.now()
        self._log_history(task_id, "assigned", {"agent": agent_name})
        self._save()
        logger.info("Assigned task %s to agent %s", task_id[:8], agent_name)

    def cancel_task(self, task_id: str):
        self.update_task_status(task_id, TaskStatus.CANCELLED)

    # ------------------------------------------------------------------
    # Task Execution
    # ------------------------------------------------------------------

    def start_task(self, task_id: str):
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        if task.status != TaskStatus.ASSIGNED:
            raise ValueError(f"Task {task_id[:8]} is not assigned (status={task.status.value})")
        self.update_task_status(task_id, TaskStatus.RUNNING)

    def complete_task(self, task_id: str, result: Optional[Dict] = None):
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        self.update_task_status(task_id, TaskStatus.COMPLETED, result=result)
        self._log_history(task_id, "completed", {"result": result})

    def fail_task(self, task_id: str, error: str):
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        task.retry_count += 1
        if task.retry_count < task.max_retries:
            logger.warning("Task %s failed (retry %d/%d): %s", task_id[:8], task.retry_count, task.max_retries, error)
            self.update_task_status(task_id, TaskStatus.PENDING, error=error)
        else:
            logger.error("Task %s failed permanently after %d retries: %s", task_id[:8], task.retry_count, error)
            self.update_task_status(task_id, TaskStatus.FAILED, error=error)

    def retry_task(self, task_id: str):
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        if task.status != TaskStatus.FAILED:
            raise ValueError(f"Task {task_id[:8]} is not in FAILED status")
        task.retry_count = 0
        task.status = TaskStatus.PENDING
        task.updated_at = datetime.now()
        self._log_history(task_id, "retried", {})
        self._save()
        logger.info("Reset retry count for task %s", task_id[:8])

    def get_executable_tasks(self) -> List[Task]:
        pending = self.get_pending_tasks()
        ready = []
        for task in pending:
            deps_met = all(
                dep in self.tasks and self.tasks[dep].status == TaskStatus.COMPLETED
                for dep in task.dependencies
            )
            if deps_met:
                ready.append(task)
        ready.sort(key=lambda t: (-t.priority.value, t.created_at))
        return ready

    # ------------------------------------------------------------------
    # Statistics & Reporting
    # ------------------------------------------------------------------

    def get_task_stats(self) -> Dict:
        total = len(self.tasks)
        by_status = {}
        for status in TaskStatus:
            by_status[status.value] = len([t for t in self.tasks.values() if t.status == status])

        completed = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        failed = [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]

        completion_times = []
        for t in completed:
            delta = (t.updated_at - t.created_at).total_seconds()
            completion_times.append(delta)

        avg_time = sum(completion_times) / len(completion_times) if completion_times else 0
        completion_rate = (len(completed) / total * 100) if total else 0

        by_priority = {}
        for p in TaskPriority:
            by_priority[p.name] = len([t for t in self.tasks.values() if t.priority == p])

        return {
            "total_tasks": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "completion_rate_pct": round(completion_rate, 2),
            "avg_completion_seconds": round(avg_time, 2),
            "total_completed": len(completed),
            "total_failed": len(failed),
            "total_retries": sum(t.retry_count for t in self.tasks.values()),
        }

    def generate_report(self) -> str:
        stats = self.get_task_stats()
        lines = [
            "=== Task Manager Report ===",
            f"Total tasks: {stats['total_tasks']}",
            f"Completion rate: {stats['completion_rate_pct']}%",
            f"Avg completion time: {stats['avg_completion_seconds']}s",
            "",
            "By status:",
        ]
        for status, count in stats["by_status"].items():
            lines.append(f"  {status}: {count}")
        lines.append("")
        lines.append("By priority:")
        for pri, count in stats["by_priority"].items():
            lines.append(f"  {pri}: {count}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_tasks(self, filepath: str):
        data = {
            "exported_at": datetime.now().isoformat(),
            "tasks": [t.to_dict() for t in self.tasks.values()],
            "stats": self.get_task_stats(),
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        logger.info("Exported %d tasks to %s", len(self.tasks), filepath)

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def _log_history(self, task_id: str, action: str, details: Dict):
        self.task_history.append({
            "task_id": task_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "details": details,
        })

    def get_task_history(self, task_id: Optional[str] = None) -> List[Dict]:
        if task_id:
            return [h for h in self.task_history if h["task_id"] == task_id]
        return list(self.task_history)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def delete_task(self, task_id: str):
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        del self.tasks[task_id]
        self._log_history(task_id, "deleted", {})
        self._save()
        logger.info("Deleted task %s", task_id[:8])

    def purge_completed(self) -> int:
        completed_ids = [tid for tid, t in self.tasks.items() if t.status == TaskStatus.COMPLETED]
        for tid in completed_ids:
            del self.tasks[tid]
        self._save()
        logger.info("Purged %d completed tasks", len(completed_ids))
        return len(completed_ids)


# ======================================================================
# CLI
# ======================================================================

def _cli():
    parser = argparse.ArgumentParser(description="AI OS Task Manager")
    parser.add_argument("--project-root", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        help="Project root directory")
    sub = parser.add_subparsers(dest="command")

    p_create = sub.add_parser("create", help="Create a new task")
    p_create.add_argument("description", help="Task description")
    p_create.add_argument("--priority", choices=["low", "medium", "high", "critical"], default="medium")
    p_create.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")
    p_create.add_argument("--deps", nargs="*", default=[], help="Dependency task IDs")

    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument("--status", choices=[s.value for s in TaskStatus], default=None)
    p_list.add_argument("--pending", action="store_true", help="Show only pending tasks")

    sub.add_parser("stats", help="Show task statistics")
    sub.add_parser("report", help="Generate full report")

    p_get = sub.add_parser("get", help="Get task by ID (prefix)")
    p_get.add_argument("task_id")

    p_assign = sub.add_parser("assign", help="Assign task to agent")
    p_assign.add_argument("task_id")
    p_assign.add_argument("agent")

    p_complete = sub.add_parser("complete", help="Mark task as completed")
    p_complete.add_argument("task_id")

    p_fail = sub.add_parser("fail", help="Mark task as failed")
    p_fail.add_argument("task_id")
    p_fail.add_argument("--error", default="manual fail")

    p_cancel = sub.add_parser("cancel", help="Cancel a task")
    p_cancel.add_argument("task_id")

    p_export = sub.add_parser("export", help="Export tasks to JSON")
    p_export.add_argument("filepath")

    p_retry = sub.add_parser("retry", help="Retry a failed task")
    p_retry.add_argument("task_id")

    p_history = sub.add_parser("history", help="Show task history")
    p_history.add_argument("--task-id", default=None)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    tm = TaskManager(args.project_root)

    if args.command == "create":
        pri = TaskPriority[args.priority.upper()]
        task = tm.create_task(args.description, priority=pri, timeout_seconds=args.timeout, dependencies=args.deps)
        print(json.dumps(task.to_dict(), indent=2))

    elif args.command == "list":
        if args.pending:
            tasks = tm.get_pending_tasks()
        elif args.status:
            tasks = tm.get_tasks_by_status(TaskStatus(args.status))
        else:
            tasks = tm.list_all_tasks()
        if not tasks:
            print("No tasks found.")
        for t in tasks:
            agent = t.assigned_agent or "-"
            print(f"  {t.id[:8]}  {t.status.value:10s}  P{t.priority.value}  {agent:12s}  {t.description[:60]}")

    elif args.command == "stats":
        print(json.dumps(tm.get_task_stats(), indent=2))

    elif args.command == "report":
        print(tm.generate_report())

    elif args.command == "get":
        task = tm.find_task_by_prefix(args.task_id)
        if task is None:
            print(f"No task found matching '{args.task_id}'")
            sys.exit(1)
        print(json.dumps(task.to_dict(), indent=2))

    elif args.command == "assign":
        tm.assign_task(args.task_id, args.agent)
        print(f"Assigned {args.task_id[:8]} to {args.agent}")

    elif args.command == "complete":
        tm.complete_task(args.task_id, result={"completed_via": "cli"})
        print(f"Task {args.task_id[:8]} marked completed")

    elif args.command == "fail":
        tm.fail_task(args.task_id, error=args.error)
        print(f"Task {args.task_id[:8]} marked failed")

    elif args.command == "cancel":
        tm.cancel_task(args.task_id)
        print(f"Task {args.task_id[:8]} cancelled")

    elif args.command == "export":
        tm.export_tasks(args.filepath)
        print(f"Exported to {args.filepath}")

    elif args.command == "retry":
        tm.retry_task(args.task_id)
        print(f"Task {args.task_id[:8]} reset for retry")

    elif args.command == "history":
        entries = tm.get_task_history(task_id=args.task_id)
        for h in entries:
            print(f"  {h['timestamp']}  {h['task_id'][:8]}  {h['action']:15s}  {h['details']}")


if __name__ == "__main__":
    _cli()
