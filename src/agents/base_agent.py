from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import time
import logging
import traceback


class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"
    OFFLINE = "offline"


@dataclass
class AgentResult:
    success: bool
    output: Any
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    def __init__(self, name: str, project_root: str):
        self.name = name
        self.project_root = project_root
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(name)
        self.execution_history: List[Dict] = []
        self._context: Dict[str, Any] = {}
        self._max_retries = 3

    @abstractmethod
    def execute(self, task: Dict) -> AgentResult:
        """Execute a task. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities. Must be implemented by subclasses."""
        pass

    def can_handle(self, task: Dict) -> bool:
        """Check if this agent can handle the given task."""
        task_keywords = task.get("keywords", [])
        capabilities = self.get_capabilities()
        return any(kw.lower() in [c.lower() for c in capabilities] for kw in task_keywords)

    def get_status(self) -> Dict:
        """Get agent status."""
        return {
            "name": self.name,
            "status": self.status.value,
            "capabilities": self.get_capabilities(),
            "tasks_completed": len(self.execution_history),
            "context_loaded": bool(self._context),
        }

    def start(self):
        """Start the agent."""
        self.status = AgentStatus.IDLE
        self.logger.info(f"Agent {self.name} started")

    def stop(self):
        """Stop the agent."""
        self.status = AgentStatus.OFFLINE
        self.logger.info(f"Agent {self.name} stopped")

    def load_context(self, context: Dict[str, Any]):
        """Load project context before execution."""
        self._context.update(context)
        self.logger.debug(f"Context loaded for {self.name}: {list(context.keys())}")

    def get_context(self) -> Dict[str, Any]:
        """Return loaded context."""
        return self._context.copy()

    def _execute_with_retry(self, task: Dict) -> AgentResult:
        """Execute a task with retry logic."""
        last_error = None
        for attempt in range(1, self._max_retries + 1):
            try:
                self.status = AgentStatus.BUSY
                start_time = time.time()
                result = self.execute(task)
                result.execution_time = time.time() - start_time
                self._record_execution(task, result)
                self.status = AgentStatus.IDLE
                return result
            except Exception as e:
                last_error = str(e)
                self.logger.error(
                    f"Attempt {attempt}/{self._max_retries} failed for {self.name}: {last_error}"
                )
                if attempt == self._max_retries:
                    self.status = AgentStatus.FAILED
                    return AgentResult(
                        success=False,
                        output=None,
                        errors=[last_error, traceback.format_exc()],
                        execution_time=0.0,
                    )
        return AgentResult(
            success=False,
            output=None,
            errors=[last_error or "Unknown error"],
            execution_time=0.0,
        )

    def _record_execution(self, task: Dict, result: AgentResult):
        """Store execution history."""
        record = {
            "task": task.get("description", str(task)[:100]),
            "success": result.success,
            "execution_time": result.execution_time,
            "errors": result.errors,
        }
        self.execution_history.append(record)
        self.logger.info(
            f"{self.name} completed task: success={result.success}, "
            f"time={result.execution_time:.3f}s"
        )

    def get_execution_history(self) -> List[Dict]:
        """Return execution history."""
        return self.execution_history.copy()

    def reset(self):
        """Reset agent state."""
        self.status = AgentStatus.IDLE
        self.execution_history.clear()
        self._context.clear()
        self.logger.info(f"Agent {self.name} reset")
