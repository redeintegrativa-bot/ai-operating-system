#!/usr/bin/env python3
"""REST API server for the AI Operating System."""

import argparse
import os
import sys
import time
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.task_manager import TaskManager, TaskStatus, TaskPriority
from core.memory import MemorySystem, MemoryType
try:
    from core.agent_registry import AgentRegistry
except ImportError:
    AgentRegistry = None  # placeholder module

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api_server")

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

_project_root: str = ""
_task_manager: Optional[TaskManager] = None
_memory_system: Optional[MemorySystem] = None
_agent_registry: Optional[AgentRegistry] = None
_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _task_manager, _memory_system, _agent_registry, _start_time
    _start_time = time.time()
    _task_manager = TaskManager(_project_root)
    _memory_system = MemorySystem(_project_root)
    try:
        _agent_registry = AgentRegistry(_project_root)
    except Exception:
        _agent_registry = None
    logger.info("API server started (root=%s)", _project_root)
    yield
    logger.info("API server shutting down")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Operating System API",
    description="REST API for AI OS",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TaskCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=2000)
    priority: str = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: Optional[int] = Field(default=None, ge=1)


class TaskUpdate(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    priority: Optional[str] = Field(default=None, pattern=r"^(low|medium|high|critical)$")
    status: Optional[str] = Field(default=None, pattern=r"^(created|pending|assigned|running|completed|failed|cancelled)$")
    metadata: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    id: str
    description: str
    status: str
    priority: str
    created_at: str
    updated_at: str
    assigned_agent: Optional[str] = None
    result: Optional[Dict] = None
    errors: List[str] = []
    metadata: Dict[str, Any] = {}
    retry_count: int = 0


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int


class AgentResponse(BaseModel):
    name: str
    status: str
    capabilities: List[str]
    tasks_completed: int = 0


class ExecuteRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Task description to execute")


class ExecuteResponse(BaseModel):
    task_id: str
    agent: str
    status: str
    message: str


class MemoryCreate(BaseModel):
    content: Dict[str, Any]
    memory_type: str = Field(default="episodic", pattern=r"^(episodic|semantic|procedural)$")
    keywords: List[str] = Field(default_factory=list)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)


class MemoryResponse(BaseModel):
    id: str
    agent_name: str
    memory_type: str
    content: Dict
    keywords: List[str]
    importance: float
    created_at: str
    last_accessed: str
    access_count: int


class StatusResponse(BaseModel):
    status: str
    version: str
    uptime: float
    agents: Dict[str, str]
    tasks: Dict[str, int]


class MetricsResponse(BaseModel):
    total_tasks: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    completion_rate_pct: float
    avg_completion_seconds: float
    total_memories: int
    agent_count: int
    uptime_seconds: float


class ErrorResponse(BaseModel):
    detail: str
    error_code: str = "UNKNOWN"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_task_manager() -> TaskManager:
    if _task_manager is None:
        raise HTTPException(status_code=503, detail="Task manager not initialized")
    return _task_manager


def _get_memory_system() -> MemorySystem:
    if _memory_system is None:
        raise HTTPException(status_code=503, detail="Memory system not initialized")
    return _memory_system


def _task_to_response(task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        description=task.description,
        status=task.status.value,
        priority=TaskPriority(task.priority).name.lower() if isinstance(task.priority, int) else task.priority.name.lower(),
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
        assigned_agent=task.assigned_agent,
        result=task.result,
        errors=task.errors,
        metadata=task.metadata,
        retry_count=task.retry_count,
    )


def _list_agents_internal() -> List[Dict[str, Any]]:
    agents: List[Dict[str, Any]] = []

    agent_dirs = [
        d for d in os.listdir(os.path.join(_project_root, "src", "agents"))
        if os.path.isdir(os.path.join(_project_root, "src", "agents", d)) and not d.startswith("_")
    ]
    known_agents = agent_dirs or ["architect", "engineer", "researcher",
                                   "ai_specialist", "automation_specialist",
                                   "database_specialist", "security_specialist",
                                   "orchestrator"]

    for name in known_agents:
        agents.append({
            "name": name,
            "status": "online",
            "capabilities": [],
            "tasks_completed": 0,
        })

    if _task_manager:
        for name in known_agents:
            agent_tasks = _task_manager.get_tasks_by_agent(name)
            completed = sum(1 for t in agent_tasks if t.status == TaskStatus.COMPLETED)
            for a in agents:
                if a["name"] == name:
                    a["tasks_completed"] = completed

    return agents


def _get_agent_capabilities(agent_name: str) -> List[str]:
    capability_map = {
        "architect": ["system_design", "architecture_planning", "code_review"],
        "engineer": ["code_generation", "debugging", "testing", "refactoring"],
        "researcher": ["information_gathering", "analysis", "documentation"],
        "ai_specialist": ["ml_modeling", "nlp", "prompt_engineering"],
        "automation_specialist": ["workflow_automation", "scripting", "ci_cd"],
        "database_specialist": ["schema_design", "query_optimization", "data_migration"],
        "security_specialist": ["security_audit", "vulnerability_scanning", "compliance"],
        "orchestrator": ["task_decomposition", "agent_coordination", "planning"],
    }
    return capability_map.get(agent_name, ["general"])

# ---------------------------------------------------------------------------
# Task Endpoints
# ---------------------------------------------------------------------------


@app.post("/api/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    tm = _get_task_manager()
    priority_map = {"low": TaskPriority.LOW, "medium": TaskPriority.MEDIUM,
                    "high": TaskPriority.HIGH, "critical": TaskPriority.CRITICAL}
    created = tm.create_task(
        description=task.description,
        priority=priority_map[task.priority],
        metadata=task.metadata,
        timeout_seconds=task.timeout_seconds,
    )
    logger.info("Created task %s via API", created.id[:8])
    return _task_to_response(created)


@app.get("/api/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(None, pattern=r"^(created|pending|assigned|running|completed|failed|cancelled)$"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    tm = _get_task_manager()
    if status:
        try:
            tasks = tm.get_tasks_by_status(TaskStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    else:
        tasks = tm.list_all_tasks()
    tasks.sort(key=lambda t: t.created_at, reverse=True)
    total = len(tasks)
    page = tasks[offset:offset + limit]
    return TaskListResponse(
        tasks=[_task_to_response(t) for t in page],
        total=total,
    )


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    tm = _get_task_manager()
    task = tm.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return _task_to_response(task)


@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, update: TaskUpdate):
    tm = _get_task_manager()
    task = tm.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if update.description is not None:
        task.description = update.description

    if update.priority is not None:
        priority_map = {"low": TaskPriority.LOW, "medium": TaskPriority.MEDIUM,
                        "high": TaskPriority.HIGH, "critical": TaskPriority.CRITICAL}
        task.priority = priority_map[update.priority]

    if update.status is not None:
        try:
            new_status = TaskStatus(update.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {update.status}")
        if new_status == TaskStatus.CANCELLED:
            tm.cancel_task(task_id)
        elif new_status == TaskStatus.COMPLETED:
            tm.complete_task(task_id, result=task.result)
        elif new_status == TaskStatus.FAILED:
            tm.fail_task(task_id, error="Manually set to failed via API")
        else:
            task.status = new_status
            task.updated_at = datetime.now()

    if update.metadata is not None:
        task.metadata = update.metadata

    return _task_to_response(tm.get_task(task_id))


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    tm = _get_task_manager()
    task = tm.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    tm.delete_task(task_id)
    return {"detail": f"Task {task_id} deleted"}

# ---------------------------------------------------------------------------
# Agent Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/agents", response_model=List[AgentResponse])
async def list_agents():
    agents_data = _list_agents_internal()
    return [
        AgentResponse(
            name=a["name"],
            status=a["status"],
            capabilities=_get_agent_capabilities(a["name"]),
            tasks_completed=a["tasks_completed"],
        )
        for a in agents_data
    ]


@app.get("/api/agents/{agent_name}", response_model=AgentResponse)
async def get_agent(agent_name: str):
    agents_data = _list_agents_internal()
    for a in agents_data:
        if a["name"] == agent_name:
            return AgentResponse(
                name=a["name"],
                status=a["status"],
                capabilities=_get_agent_capabilities(agent_name),
                tasks_completed=a["tasks_completed"],
            )
    raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")


@app.post("/api/agents/{agent_name}/execute", response_model=ExecuteResponse)
async def execute_task(agent_name: str, req: ExecuteRequest):
    tm = _get_task_manager()
    agents_data = _list_agents_internal()
    agent_names = {a["name"] for a in agents_data}
    if agent_name not in agent_names:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    task = tm.create_task(description=req.task, priority=TaskPriority.MEDIUM)
    try:
        tm.assign_task(task.id, agent_name)
        tm.start_task(task.id)
        tm.complete_task(task.id, result={"summary": f"Executed by {agent_name}"})
        status = "completed"
        message = f"Task executed successfully by agent '{agent_name}'"
    except ValueError as e:
        status = "failed"
        message = str(e)

    return ExecuteResponse(
        task_id=task.id,
        agent=agent_name,
        status=status,
        message=message,
    )

# ---------------------------------------------------------------------------
# System Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    tm = _get_task_manager()
    agents_data = _list_agents_internal()
    agent_statuses = {a["name"]: a["status"] for a in agents_data}
    stats = tm.get_task_stats()
    return StatusResponse(
        status="running",
        version="1.0.0",
        uptime=time.time() - _start_time,
        agents=agent_statuses,
        tasks=stats.get("by_status", {}),
    )


@app.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics():
    tm = _get_task_manager()
    stats = tm.get_task_stats()
    memory_count = len(_memory_system.memories) if _memory_system else 0
    agent_count = len(_list_agents_internal())
    return MetricsResponse(
        total_tasks=stats["total_tasks"],
        by_status=stats["by_status"],
        by_priority=stats["by_priority"],
        completion_rate_pct=stats["completion_rate_pct"],
        avg_completion_seconds=stats["avg_completion_seconds"],
        total_memories=memory_count,
        agent_count=agent_count,
        uptime_seconds=time.time() - _start_time,
    )


@app.get("/api/health")
async def health_check():
    ready = _task_manager is not None
    return {
        "status": "healthy" if ready else "starting",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }

# ---------------------------------------------------------------------------
# Memory Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/memory/{agent}", response_model=List[MemoryResponse])
async def get_memories(
    agent: str,
    memory_type: Optional[str] = Query(None, pattern=r"^(episodic|semantic|procedural)$"),
):
    ms = _get_memory_system()
    mtype = MemoryType(memory_type) if memory_type else None
    memories = ms.get_memories(agent, mtype)
    return [
        MemoryResponse(
            id=m.id,
            agent_name=m.agent_name,
            memory_type=m.memory_type.value,
            content=m.content,
            keywords=m.keywords,
            importance=m.importance,
            created_at=m.created_at.isoformat(),
            last_accessed=m.last_accessed.isoformat(),
            access_count=m.access_count,
        )
        for m in memories
    ]


@app.post("/api/memory/{agent}", response_model=MemoryResponse, status_code=201)
async def add_memory(agent: str, memory: MemoryCreate):
    ms = _get_memory_system()
    mtype = MemoryType(memory.memory_type)
    created = ms.add_memory(
        agent_name=agent,
        memory_type=mtype,
        content=memory.content,
        keywords=memory.keywords,
        importance=memory.importance,
    )
    return MemoryResponse(
        id=created.id,
        agent_name=created.agent_name,
        memory_type=created.memory_type.value,
        content=created.content,
        keywords=created.keywords,
        importance=created.importance,
        created_at=created.created_at.isoformat(),
        last_accessed=created.last_accessed.isoformat(),
        access_count=created.access_count,
    )

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="AI Operating System API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--project-root", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        help="Project root directory")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"],
                        help="Logging level")
    args = parser.parse_args()

    global _project_root
    _project_root = args.project_root

    logger.info("Starting AI OS API server on %s:%s", args.host, args.port)
    uvicorn.run(
        "src.api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
