"""Kernel API - JSON API for Mission Control frontend.

Provides endpoints for agents, suggestions, scheduler, and kernel status.
Designed to be consumed by the Mission Control dashboard.

Usage:
    python src/api/kernel_api.py --port 8000
    
    Or import and use generate_* functions directly.
"""

import json
import os
import sys
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, project_root)

from src.core.kernel import (
    AIOSKernel, AgentConfig, AgentMode, AgentHealth,
    HeartbeatMonitor, Scheduler, ScheduledMission,
    create_default_kernel,
)
from src.core.suggestions import SuggestionInbox, SuggestionGenerator
from src.core.orchestrator import Orchestrator
from src.agents import create_agent


logger = logging.getLogger("kernel_api")


class KernelAPI:
    """JSON API layer for the AIOS Kernel."""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        
        # Initialize kernel
        self.kernel = create_default_kernel(project_root)
        
        # Initialize suggestions
        self.inbox = SuggestionInbox(project_root)
        
        # Initialize orchestrator and integrate
        self.orchestrator = Orchestrator(project_root)
        self.kernel.set_orchestrator(self.orchestrator)
        
        logger.info("KernelAPI initialized for %s", project_root)
    
    # ---- Agent Endpoints ----
    
    def list_agents(self) -> Dict[str, Any]:
        agents = self.kernel.agent_manager.get_all()
        result = []
        for agent in agents:
            hb = self.kernel.heartbeat.get(agent.name)
            orch_agent = self.orchestrator.agents.get(agent.name)
            result.append({
                **agent.to_dict(),
                "heartbeat": {
                    "status": hb.status if hb else "unknown",
                    "timestamp": hb.timestamp if hb else None,
                    "active_tasks": hb.active_tasks if hb else 0,
                },
                "tasks_completed": orch_agent.tasks_completed if orch_agent else 0,
                "tasks_failed": orch_agent.tasks_failed if orch_agent else 0,
            })
        return {"agents": result, "total": len(result)}
    
    def get_agent(self, name: str) -> Optional[Dict[str, Any]]:
        config = self.kernel.agent_manager.get(name)
        if not config:
            return None
        hb = self.kernel.heartbeat.get(name)
        orch_agent = self.orchestrator.agents.get(name)
        return {
            **config.to_dict(),
            "heartbeat": {
                "status": hb.status if hb else "unknown",
                "timestamp": hb.timestamp if hb else None,
            },
            "tasks_completed": orch_agent.tasks_completed if orch_agent else 0,
            "tasks_failed": orch_agent.tasks_failed if orch_agent else 0,
        }
    
    def set_agent_mode(self, name: str, mode: str) -> Dict[str, Any]:
        try:
            agent_mode = AgentMode(mode)
            success = self.kernel.agent_manager.set_mode(name, agent_mode)
            return {"success": success, "agent": name, "mode": mode}
        except ValueError:
            return {"success": False, "error": f"Invalid mode: {mode}"}
    
    # ---- Suggestion Endpoints ----
    
    def list_suggestions(self, status: Optional[str] = None) -> Dict[str, Any]:
        if status:
            suggestions = self.inbox.get_by_status(status)
        else:
            suggestions = self.inbox.get_all()
        return {
            "suggestions": [s.__dict__ for s in suggestions],
            "total": len(suggestions),
            "stats": self.inbox.get_stats(),
        }
    
    def approve_suggestion(self, suggestion_id: str) -> Dict[str, Any]:
        success = self.inbox.approve(suggestion_id)
        return {"success": success, "id": suggestion_id}
    
    def reject_suggestion(self, suggestion_id: str, reason: str = "") -> Dict[str, Any]:
        success = self.inbox.reject(suggestion_id, reason)
        return {"success": success, "id": suggestion_id}
    
    def add_suggestion(self, agent_name: str, title: str, description: str,
                      suggestion_type: str = "improvement", domain: str = "",
                      priority: str = "medium") -> Dict[str, Any]:
        from src.core.kernel import Suggestion
        s = Suggestion(
            agent_name=agent_name,
            title=title,
            description=description,
            suggestion_type=suggestion_type,
            domain=domain,
            priority=priority,
        )
        self.inbox.add(s)
        return {"success": True, "id": s.id}
    
    # ---- Scheduler Endpoints ----
    
    def list_scheduled_missions(self) -> Dict[str, Any]:
        missions = self.kernel.scheduler.get_all_missions()
        return {
            "missions": [m.to_dict() for m in missions],
            "total": len(missions),
        }
    
    def add_scheduled_mission(self, name: str, agent_name: str,
                             description: str = "", interval_seconds: float = 3600,
                             enabled: bool = True) -> Dict[str, Any]:
        mission = ScheduledMission(
            name=name,
            agent_name=agent_name,
            description=description,
            interval_seconds=interval_seconds,
            enabled=enabled,
        )
        self.kernel.scheduler.add_mission(mission)
        return {"success": True, "id": mission.id}
    
    def get_due_missions(self) -> Dict[str, Any]:
        due = self.kernel.scheduler.get_due_missions()
        return {
            "due": [m.to_dict() for m in due],
            "total": len(due),
        }
    
    # ---- Kernel Status ----
    
    def get_kernel_status(self) -> Dict[str, Any]:
        status = self.kernel.get_status()
        status["suggestion_stats"] = self.inbox.get_stats()
        status["orchestrator"] = self.orchestrator.get_status()
        return status
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Aggregated data for the Mission Control dashboard."""
        orch_status = self.orchestrator.get_status()
        suggestion_stats = self.inbox.get_stats()
        kernel_status = self.kernel.get_status()
        
        return {
            "agents": {
                "total": len(self.kernel.agent_manager.get_all()),
                "online": len([c for c in self.kernel.agent_manager.get_all() 
                             if c.mode != AgentMode.MANUAL]),
                "busy": sum(1 for a in self.orchestrator.agents.values() 
                          if a.status.value == "busy"),
            },
            "tasks": {
                "pending": orch_status.get("pending", 0),
                "completed": orch_status.get("completed", 0),
                "total": orch_status.get("total_submitted", 0),
            },
            "suggestions": suggestion_stats,
            "scheduler": {
                "total_missions": len(self.kernel.scheduler.get_all_missions()),
                "due_now": len(self.kernel.scheduler.get_due_missions()),
            },
            "stale_agents": kernel_status.get("stale_agents", []),
        }

    # ---- Browser Agent Endpoints ----

    def get_browser_agent(self) -> Dict[str, Any]:
        """Get browser agent status and configuration."""
        config = self.kernel.agent_manager.get("browser")
        if not config:
            return {"error": "Browser agent not registered"}
        hb = self.kernel.heartbeat.get("browser")
        orch_agent = self.orchestrator.agents.get("browser")
        return {
            **config.to_dict(),
            "heartbeat": {
                "status": hb.status if hb else "unknown",
                "timestamp": hb.timestamp if hb else None,
                "active_tasks": hb.active_tasks if hb else 0,
            },
            "tasks_completed": orch_agent.tasks_completed if orch_agent else 0,
            "tasks_failed": orch_agent.tasks_failed if orch_agent else 0,
        }

    def execute_browser_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a browser agent task (browse, scrape, ocr, screenshot, download, search, extract_json)."""
        valid_types = {"browse", "scrape", "ocr", "screenshot", "download", "search", "extract_json"}
        if task_type not in valid_types:
            return {"success": False, "error": f"Invalid task type: {task_type}. Valid: {sorted(valid_types)}"}
        try:
            agent = create_agent("browser", self.project_root)
            task = {"type": task_type, **params}
            result = agent.execute(task)
            return {
                "success": result.success,
                "output": result.output,
                "errors": result.errors,
                "execution_time": result.execution_time,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def schedule_browser_task(self, name: str, task_type: str, params: Dict[str, Any],
                              interval_seconds: float = 3600, enabled: bool = True) -> Dict[str, Any]:
        """Schedule a recurring browser task."""
        mission = ScheduledMission(
            name=name,
            agent_name="browser",
            description=f"Browser task: {task_type}",
            interval_seconds=interval_seconds,
            enabled=enabled,
            task_template={"type": task_type, **params},
        )
        mission_id = self.kernel.scheduler.add_mission(mission)
        return {"success": True, "id": mission_id, "name": name, "task_type": task_type}

    def get_browser_memories(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Get browser agent memories (scrape results, OCR results, etc.)."""
        try:
            from src.core.memory import MemorySystem
            memory = MemorySystem(self.project_root)
            if query:
                results = memory.search_memories(query, agent_name="browser_agent")
            else:
                results = memory.get_memories("browser_agent")
            return {
                "memories": [m.to_dict() for m in results],
                "total": len(results),
            }
        except Exception as e:
            return {"memories": [], "total": 0, "error": str(e)}


def generate_api_json(api: KernelAPI, endpoint: str, **kwargs) -> str:
    """Generate JSON response for an API endpoint."""
    methods = {
        "agents": lambda: api.list_agents(),
        "agent": lambda: api.get_agent(kwargs.get("name", "")),
        "suggestions": lambda: api.list_suggestions(kwargs.get("status")),
        "kernel_status": lambda: api.get_kernel_status(),
        "dashboard": lambda: api.get_dashboard_data(),
        "scheduled_missions": lambda: api.list_scheduled_missions(),
        "due_missions": lambda: api.get_due_missions(),
        "browser": lambda: api.get_browser_agent(),
        "browser_memories": lambda: api.get_browser_memories(kwargs.get("query")),
    }
    
    handler = methods.get(endpoint)
    if handler:
        return json.dumps(handler(), indent=2, default=str)
    return json.dumps({"error": f"Unknown endpoint: {endpoint}"})


# ---------------------------------------------------------------------------
# CLI & HTTP Server
# ---------------------------------------------------------------------------

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AIOS Kernel API")
    parser.add_argument("--project-root", default=project_root)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--endpoint", default="dashboard",
                       choices=["agents", "suggestions", "kernel_status", 
                               "dashboard", "scheduled_missions", "due_missions",
                               "browser", "browser_memories"])
    args = parser.parse_args()
    
    api = KernelAPI(args.project_root)
    
    # Print JSON for requested endpoint
    result = generate_api_json(api, args.endpoint)
    print(result)


if __name__ == "__main__":
    main()
