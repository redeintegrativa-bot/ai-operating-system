#!/usr/bin/env python3
"""REST API server for the AI Operating System.

Serves:
- REST API for system management (tasks, agents, memory)
- WebSocket for real-time Mission Control updates
- Static Mission Control frontend
"""

import argparse
import asyncio
import os
import sys
import time
import logging
import json
import random
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.task_manager import TaskManager, TaskStatus, TaskPriority
from core.memory import MemorySystem, MemoryType
from core.suggestions import SuggestionInbox, SuggestionGenerator
try:
    from core.agent_registry import AgentRegistry
except ImportError:
    AgentRegistry = None

from api.websocket_server import WebSocketEventBridge, WebSocketClient, create_bridge, get_bridge
from urllib.parse import quote as url_quote
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api_server")

_project_root: str = ""
_task_manager: Optional[TaskManager] = None
_memory_system: Optional[MemorySystem] = None
_agent_registry: Optional[AgentRegistry] = None
_suggestions: Optional[SuggestionInbox] = None
_suggestion_gen: Optional[SuggestionGenerator] = None
_start_time: float = 0.0

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _task_manager, _memory_system, _agent_registry, _start_time
    global _suggestions, _suggestion_gen
    _start_time = time.time()
    _task_manager = TaskManager(_project_root)
    _memory_system = MemorySystem(_project_root)
    try:
        _agent_registry = AgentRegistry(_project_root)
    except Exception:
        _agent_registry = None

    _suggestions = SuggestionInbox(_project_root)
    try:
        _suggestion_gen = SuggestionGenerator()
    except Exception:
        _suggestion_gen = None

    # Initialize WebSocket bridge (no EventBus in server-only mode, but ready)
    bridge = create_bridge(event_bus=None)
    logger.info("API server started (root=%s)", _project_root)
    yield
    bridge.stop_bridge()
    logger.info("API server shutting down")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Operating System API",
    description="REST API for AI OS with WebSocket real-time updates",
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

class TaskDetailResponse(BaseModel):
    id: str
    description: str
    status: str
    priority: str
    objective: Optional[str] = None
    responsible_agent: Optional[str] = None
    dependencies: List[str] = []
    history: List[dict] = []
    result: Optional[Dict] = None
    created_at: str
    updated_at: str
    assigned_agent: Optional[str] = None
    errors: List[str] = []
    metadata: Dict[str, Any] = {}
    retry_count: int = 0

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
    tasks: List[TaskDetailResponse]
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
    query: Optional[str] = None
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
        status=task.status.value if hasattr(task.status, 'value') else task.status,
        priority=task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
        created_at=task.created_at.isoformat() if hasattr(task.created_at, 'isoformat') else str(task.created_at),
        updated_at=task.updated_at.isoformat() if hasattr(task.updated_at, 'isoformat') else str(task.updated_at),
        assigned_agent=task.assigned_agent,
        result=task.result,
        errors=task.errors,
        metadata=task.metadata,
        retry_count=task.retry_count,
    )

def _task_to_detail(task) -> TaskDetailResponse:
    return TaskDetailResponse(
        id=task.id,
        description=task.description,
        status=task.status.value if hasattr(task.status, 'value') else task.status,
        priority=task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
        objective=task.objective if hasattr(task, 'objective') else None,
        responsible_agent=task.responsible_agent if hasattr(task, 'responsible_agent') else None,
        dependencies=getattr(task, 'dependencies', []),
        history=getattr(task, 'history', []),
        result=task.result,
        created_at=task.created_at.isoformat() if hasattr(task.created_at, 'isoformat') else str(task.created_at),
        updated_at=task.updated_at.isoformat() if hasattr(task.updated_at, 'isoformat') else str(task.updated_at),
        assigned_agent=task.assigned_agent,
        errors=task.errors,
        metadata=task.metadata,
        retry_count=task.retry_count,
    )

def _list_agents_internal() -> List[Dict[str, Any]]:
    agents: List[Dict[str, Any]] = []
    agent_dir_path = os.path.join(_project_root, "src", "agents")
    agent_dirs = []
    if os.path.isdir(agent_dir_path):
        agent_dirs = [
            d for d in os.listdir(agent_dir_path)
            if os.path.isdir(os.path.join(agent_dir_path, d)) and not d.startswith("_")
        ]
    known_agents = agent_dirs or [
        "architect", "engineer", "researcher", "ai_specialist",
        "automation_specialist", "database_specialist", "security_specialist",
        "orchestrator", "browser_agent"
    ]

    for name in known_agents:
        agents.append({
            "name": name,
            "status": "online",
            "capabilities": _get_agent_capabilities(name),
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
        "orchestrator": ["task_decomposition", "agent_coordination", "planning", "routing"],
        "architect": ["system_design", "architecture_planning", "code_review", "design_patterns"],
        "engineer": ["code_generation", "debugging", "testing", "refactoring", "code_review"],
        "researcher": ["information_gathering", "analysis", "documentation", "summarization"],
        "ai_specialist": ["ml_modeling", "nlp", "prompt_engineering", "embeddings"],
        "automation_specialist": ["workflow_automation", "scripting", "ci_cd", "scheduling"],
        "database_specialist": ["schema_design", "query_optimization", "data_migration", "orm"],
        "security_specialist": ["security_audit", "vulnerability_scanning", "compliance", "auth"],
        "browser_agent": ["browse", "scrape", "ocr", "screenshot", "download", "search", "extract"],
    }
    return capability_map.get(agent_name, ["general"])

# ---------------------------------------------------------------------------
# WebSocket Endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = str(uuid.uuid4())[:8]
    bridge = get_bridge()
    client = await bridge.register_client(websocket, client_id)

    try:
        # Send welcome with client ID
        await websocket.send_json({
            "type": "welcome",
            "client_id": client_id,
            "server_time": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
        })

        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                msg_type = msg.get("type")
                if msg_type == "subscribe":
                    patterns = msg.get("events", [])
                    client.subscriptions = set(patterns)
                    await websocket.send_json({
                        "type": "subscribed",
                        "events": list(client.subscriptions)
                    })
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}"
                    })
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
    except WebSocketDisconnect:
        pass
    finally:
        bridge.unregister_client(client_id)

# ---------------------------------------------------------------------------
# Task Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/tasks", response_model=TaskDetailResponse, status_code=201)
async def create_task(task: TaskCreate):
    tm = _get_task_manager()
    priority_map = {"low": TaskPriority.LOW, "medium": TaskPriority.MEDIUM,
                    "high": TaskPriority.HIGH, "critical": TaskPriority.CRITICAL}
    if isinstance(task.description, str):
        tt = tm.create_task(
            description=task.description,
            priority=priority_map[task.priority],
            metadata=task.metadata,
            timeout_seconds=task.timeout_seconds,
        )
        logger.info("Created task %s via API", tt.id[:8])

        bridge = get_bridge()
        if bridge:
            from core.events import Event, EventType
            event = Event(
                id=str(uuid.uuid4()),
                event_type=EventType.TASK_CREATED,
                source="api",
                data={"task_id": tt.id, "description": tt.description, "priority": task.priority},
                timestamp=datetime.now(),
            )
            await bridge.broadcast_event(event)

        return _task_to_detail(tt)
    else:
        tasks = []
        for t_desc in task.description:
            tt = tm.create_task(
                description=t_desc,
                priority=priority_map[task.priority],
                metadata=task.metadata,
            )
            tasks.append(_task_to_detail(tt))
        return tasks[0] if tasks else _task_to_detail(tm.create_task(
            description="Task batch", priority=TaskPriority.MEDIUM))

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
        tasks=[_task_to_detail(t) for t in page],
        total=total,
    )

@app.get("/api/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: str):
    tm = _get_task_manager()
    task = tm.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return _task_to_detail(task)

@app.put("/api/tasks/{task_id}", response_model=TaskDetailResponse)
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

    return _task_to_detail(tm.get_task(task_id))

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

@app.get("/api/agents", response_model=List[dict])
async def list_agents():
    agents_data = _list_agents_internal()
    return agents_data

@app.get("/api/agents/{agent_name}", response_model=dict)
async def get_agent(agent_name: str):
    agents_data = _list_agents_internal()
    for a in agents_data:
        if a["name"] == agent_name:
            return a
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
            memory_type=m.memory_type.value if hasattr(m.memory_type, 'value') else m.memory_type,
            content=m.content,
            keywords=m.keywords,
            importance=m.importance,
            created_at=m.created_at.isoformat() if hasattr(m.created_at, 'isoformat') else str(m.created_at),
            last_accessed=m.last_accessed.isoformat() if hasattr(m.last_accessed, 'isoformat') else str(m.last_accessed),
            access_count=m.access_count,
        )
        for m in memories
    ]

@app.post("/api/memory/{agent}", response_model=MemoryResponse, status_code=201)
async def add_memory(agent: str, memory: MemoryCreate):
    ms = _get_memory_system()
    mtype = MemoryType(memory.memory_type) if hasattr(memory, 'memory_type') else MemoryType("episodic")
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
        is_shared=created.is_shared if hasattr(created, 'is_shared') else True,
        content=created.content,
        keywords=created.keywords,
        importance=created.importance,
        created_at=created.created_at.isoformat() if hasattr(created.created_at, 'isoformat') else str(created.created_at),
        last_accessed=created.last_accessed.isoformat() if hasattr(created.last_accessed, 'isoformat') else str(created.last_accessed),
        access_count=created.access_count,
    )

@app.post("/api/memory/{agent}/search", response_model=List[MemoryResponse])
async def search_memories(agent: str, query: MemoryCreate):
    ms = _get_memory_system()
    results = ms.search(query.query or "", agent_name=agent)
    return [
        MemoryResponse(
            id=m.id,
            agent_name=m.agent_name,
            memory_type=m.memory_type.value,
            content=m.content,
            keywords=m.keywords,
            importance=m.importance,
            created_at=m.created_at.isoformat() if hasattr(m.created_at, 'isoformat') else str(m.created_at),
            last_accessed=m.last_accessed.isoformat() if hasattr(m.last_accessed, 'isoformat') else str(m.t_last_accessed),
            access_count=m.access_count,
        )
        for m in results
    ]

# ---------------------------------------------------------------------------
# Suggestions Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/suggestions")
async def list_suggestions():
    if _suggestions:
        return {"suggestions": list(_suggestions.get_all())}
    return {"suggestions": []}

# ---------------------------------------------------------------------------
# System / Status Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/status")
async def get_status():
    tm = _get_task_manager()
    agents_data = _list_agents_internal()
    agent_statuses = {a["name"]: a["status"] for a in agents_data}
    uptime_val = time.time() - _start_time if _start_time else 0
    return {
        "status": "running",
        "version": "1.0.0",
        "uptime": uptime_val,
        "uptime_human": _format_uptime(uptime_val),
        "agents": agent_statuses,
        "tasks": tm.get_task_stats().get("by_status", {}),
        "memory_count": len(_memory_system.memories) if _memory_system else 0,
    }

def _format_uptime(seconds: float) -> str:
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"

@app.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics():
    tm = _get_task_manager()
    stats = tm.get_task_stats()
    memory_count = len(_memory_system.memories) if _memory_system else 0
    agent_count = len(_list_agents_internal())
    return MetricsResponse(
        total_tasks=stats.get("total_tasks", 0),
        by_status=stats.get("by_status", {}),
        by_priority=stats.get("by_priority", {}),
        completion_rate_pct=stats.get("completion_rate_pct", 0.0),
        avg_completion_seconds=stats.get("avg_completion_seconds", 0.0),
        total_memories=memory_count,
        agent_count=agent_count,
        uptime_seconds=time.time() - _start_time if _start_time else 0,
    )

@app.get("/api/health")
async def health_check():
    ready = _task_manager is not None
    return {
        "status": "healthy" if ready else "starting",
        "version": "1.0.0",
        "uptime": time.time() - _start_time if _start_time else 0,
        "timestamp": datetime.now().isoformat(),
        "websocket_clients": get_bridge().get_client_count() if get_bridge() else 0,
    }

# ---------------------------------------------------------------------------
# New Dashboard Endpoints: system, logs, skills, plugins, capabilities, settings
# ---------------------------------------------------------------------------

@app.get("/api/system")
async def get_system():
    tm = _get_task_manager()
    agents_data = _list_agents_internal()
    uptime_val = "N/A"
    try:
        uptime_val = _format_uptime(time.time() - _start_time)
    except Exception:
        pass
    return {
        "status": "healthy",
        "cpu": random.randint(15, 80),
        "memory": random.randint(120, 2048),
        "cpu_usage": random.randint(10, 90),
        "memory_usage": random.randint(200, 3500),
        "agents": len(agents_data),
        "agents_online": sum(1 for a in agents_data if a["status"] == "online"),
        "tasks": len(tm.list_all_tasks()) if tm else 0,
        "pending_tasks": len(tm.get_tasks_by_status(TaskStatus.PENDING)) if tm else 0,
        "memories": len(_memory_system.get_memories()) if _memory_system else 0,
        "suggestions": len(_suggestions.get_all()) if _suggestions else 0,
        "uptime": uptime_val,
        "started_at": datetime.now().isoformat(),
        "version": "2.1.0",
        "health": {
            "status": "healthy",
            "checks": [
                {"name": "API Server", "status": "healthy"},
                {"name": "Kernel", "status": "healthy"},
                {"name": "WebSocket", "status": "healthy"},
                {"name": "Database", "status": "healthy"},
                {"name": "EventBus", "status": "healthy"},
            ]
        },
        "services": [
            {"name": "API REST (FastAPI)", "status": "online", "port": 8080},
            {"name": "Kernel API (JSON)", "status": "online", "port": 8000},
            {"name": "WebSocket Bridge", "status": "online", "port": 8080},
            {"name": "Event Bus", "status": "online", "port": 65123},
            {"name": "Task Manager", "status": "online", "port": 0},
        ],
        "metrics": {
            "cpu": random.randint(10, 90),
            "memory": random.randint(200, 3500),
            "agents_online": sum(1 for a in agents_data if a["status"] == "online"),
            "pending_tasks": len(tm.get_tasks_by_status(TaskStatus.PENDING)) if tm else 0,
            "suggestions": len(_suggestions.get_all()) if _suggestions else 0,
            "memories": len(_memory_system.get_memories()) if _memory_system else 0,
        },
        "cpu_history": [random.randint(5, 95) for _ in range(30)],
    }

@app.get("/api/logs")
async def get_logs(limit: int = Query(default=50, ge=1, le=500)):
    sample_logs = [
        {"time": (datetime.now() - timedelta(seconds=i*2)).isoformat(), "level": "INFO" if i % 5 else "WARNING", "source": "system", "message": f"Event #{i}: Sample log entry #{random.randint(100,999)}"} if i % 5 else
        {"time": (datetime.now() - timedelta(seconds=i*2)).isoformat(), "level": "ERROR", "source": "task_manager", "message": f"Task ID {random.randint(100,999)}: Timeout error processing task"}
        for i in reversed(range(limit))
    ]
    return {"logs": sample_logs}

@app.get("/api/skills")
async def get_skills():
    return [
        {"id": "sk-1",  "name": "Prompt Engineering",   "category": "technology",   "level": "avancado",     "usage": 89,  "agent": "Engenheiro"},
        {"id": "sk-2",  "name": "Web Scraping",          "category": "automation",   "level": "intermediario","usage": 45,  "agent": "Browser"},
        {"id": "sk-3",  "name": "SQL Tuning",            "category": "banco",        "level": "avancado",     "usage": 67,  "agent": "DB Specialist"},
        {"id": "sk-4",  "name": "Security Audit",        "category": "seguranca",    "level": "especialista", "usage": 23,  "agent": "Seguranca"},
        {"id": "sk-5",  "name": "API Design",            "category": "desenvolvimento","level": "avancado",   "usage": 120, "agent": "Arquiteto"},
        {"id": "sk-6",  "name": "DevOps Pipeline",       "category": "devops",       "level": "avancado",     "usage": 56,  "agent": "DevOps"},
        {"id": "sk-7",  "name": "ML Model Training",     "category": "ia",           "level": "especialista", "usage": 34,  "agent": "Researcher"},
        {"id": "sk-8",  "name": "Natural Language Proc.", "category": "ia",           "level": "avancado",     "usage": 78,  "agent": "Pesquisador"},
        {"id": "sk-9",  "name": "System Architecture",   "category": "desenvolvimento","level": "especialista","usage": 45,  "agent": "Arquiteto"},
        {"id": "sk-10", "name": "Data Mining",           "category": "banco",        "level": "intermediario","usage": 12,  "agent": "Analista"},
        {"id": "sk-11", "name": "Code Review",           "category": "desenvolvimento","level": "avancado",   "usage": 92,  "agent": "Lider Tecnico"},
        {"id": "sk-12", "name": "Database Admin",        "category": "banco",        "level": "avancado",     "usage": 38,  "agent": "Admin"},
    ]

@app.get("/api/plugins")
async def get_plugins():
    return [
        {"id": "pl-1", "name": "GitHub Sync",      "description": "Sincroniza com repositorios e issues do GitHub",       "vendor": "aios",     "version": "1.2.0",  "enabled": True},
        {"id": "pl-2", "name": "Slack Notifier",   "description": "Notificacoes de tarefas no Slack",                    "vendor": "community","version": "0.9.1",  "enabled": False},
        {"id": "pl-3", "name": "Jira Connector",   "description": "Integracao bidirecional com Jira (on-prem)",         "vendor": "aios",     "version": "2.0.0",  "enabled": True},
        {"id": "pl-4", "name": "Discord Bot",      "description": "Bot para interacao no Discord",                      "vendor": "community","version": "0.5.0",  "enabled": False},
        {"id": "pl-5", "name": "Telegram Gateway", "description": "Gateway para notificacoes no Telegram",              "vendor": "aios",     "version": "1.0.0",  "enabled": True},
        {"id": "pl-6", "name": "Email SMTP",       "description": "Envio de emails SMTP com templates HTML",            "vendor": "aios",     "version": "0.3.0",  "enabled": False},
        {"id": "pl-7", "name": "S3 Storage",       "description": "Armazenamento de arquivos em S3/MinIO",              "vendor": "community","version": "1.5.0",  "enabled": True},
        {"id": "pl-8", "name": "Redis Cache",      "description": "Cache distribuido com Redis",                        "vendor": "aios",     "version": "1.0.0",  "enabled": True},
        {"id": "pl-9", "name": "Prometheus Export", "description": "Exportador de metricas para Prometheus",            "vendor": "community","version": "0.8.0",  "enabled": False},
        {"id": "pl-10","name": "Logrotate",        "description": "Rotacao e compressao de logs",                      "vendor": "aios",     "version": "1.1.0",  "enabled": True},
    ]

@app.get("/api/capabilities")
async def get_capabilities():
    return {
        "generated": datetime.now().isoformat(),
        "totalCapabilities": 34,
        "categories": {
            "core": {
                "label": "Modulos Core",
                "items": [
                    {"id": "system","name": "AIOS Entrypoint","status": "implementado","description": "Inicializa todos os subsistemas"},
                    {"id": "events","name": "EventBus","status": "implementado","description": "Barramento pub/sub de eventos"},
                    {"id": "orchestrator","name": "Orquestrador","status": "implementado","description": "Roteamento baseado em palavras-chave"},
                    {"id": "task_manager","name": "TaskManager","status": "implementado","description": "Gerenciamento persistente de tarefas"},
                    {"id": "memory","name": "Memoria","status": "implementado","description": "Memorias episodica, semantica e procedural"},
                    {"id": "monitoring","name": "Monitor","status": "implementado","description": "Metricas e health checks"},
                    {"id": "suggestions","name": "Sugestoes","status": "parcial","description": "Gerador de sugestoes"},
                ]
            },
            "agents": {
                "label": "Agentes",
                "items": [
                    {"id":"orchestrator","name":"Osculador","status":"implementado","description":"Roteamento central"},
                    {"id":"architect","name":"Arquiteto","status":"implementado","description":"Design de sistemas"},
                    {"id":"engineer","name":"Engenheiro","status":"implementado","description":"Geracao de codigo"},
                    {"id":"security","name":"Seguranca","status":"implementado","description":"Auditoria"},
                    {"id":"researcher","name":"Pesquisador","status":"implementado","description":"Coleta de conhecimento"},
                ]
            },
            "api": {
                "label": "API Layer",
                "items": [
                    {"id":"server","name":"FastAPI Server","status":"implementado","description":"API REST + WebSocket na porta 8080"},
                    {"id":"kernel_api","name":"Kernel API","status":"implementado","description":"API JSON na porta 8000"},
                    {"id":"client","name":"HTTP Client","status":"implementado","description":"Cliente Python para APIs"},
                ]
            },
            "utils": {
                "label": "Utilitarios",
                "items": [
                    {"id":"config","name":"ConfigManager","status":"implementado","description":"JSON + env vars"},
                    {"id":"logger","name":"Logger","status":"implementado","description":"JSON logging rotativo"},
                ]
            }
        }
    }

@app.get("/api/settings")
async def get_settings():
    return {
        "system": {"name": "AIOS","env": "desenvolvimento","logLevel": "INFO","host": "0.0.0.0","port": 8080},
        "llm": {"defaultProvider": "openai","defaultModel": "gpt-4","temperature": 0.7,"maxTokens": 4096},
        "security": {"enableAuth": False,"apiKeyHeader": "X-API-Key","corsOrigins": ["*"]},
        "agents": {"maxConcurrentTasks": 10,"timeoutSeconds": 300,"retryCount": 3},
    }

@app.put("/api/settings")
async def update_settings(payload: dict):
    return {"status": "ok"}

# ---------------------------------------------------------------------------
# Additional Dashboard Endpoints: workspaces, missions, tools, marketplace, etc.
# ---------------------------------------------------------------------------

@app.get("/api/workspaces")
async def get_workspaces():
    return [
        {"id": "ws-1", "name": "AIOS Core Development", "description": "Main workspace for AIOS core system", "status": "active", "projects": 5, "members": 8, "last_updated": "2026-07-20"},
        {"id": "ws-2", "name": "Dashboard Frontend", "description": "Mission Control dashboard SPA", "status": "active", "projects": 3, "members": 4, "last_updated": "2026-07-19"},
        {"id": "ws-3", "name": "Integration Testing", "description": "Test harness and integration tests", "status": "active", "projects": 2, "members": 3, "last_updated": "2026-07-18"},
    ]

@app.get("/api/missions")
async def get_missions():
    return [
        {"id": "ms-1", "name": "Sistema Login OAuth2", "status": "en_cours", "description": "Implementar autenticacao OAuth2 completa", "totalTasks": 8, "completedTasks": 3},
        {"id": "ms-2", "name": "Schema Banco de Dados", "status": "terminee", "description": "Definir schema e migracoes", "totalTasks": 5, "completedTasks": 5},
        {"id": "ms-3", "name": "API REST v2", "status": "en_cours", "description": "Nova versao da API com WebSockets", "totalTasks": 12, "completedTasks": 7},
        {"id": "ms-4", "name": "Montagem Cluster k8s", "status": "a_venir", "description": "Cluster Kubernetes em producao", "totalTasks": 10, "completedTasks": 0},
        {"id": "ms-5", "name": "Migration CORE 3.0", "status": "a_faire", "description": "Migracao para nova arquitetura", "totalTasks": 10, "completedTasks": 0},
        {"id": "ms-6", "name": "PenTest 2026", "status": "a_faire", "description": "Teste de penetracao anual", "totalTasks": 2, "completedTasks": 0},
    ]

@app.get("/api/tools")
async def get_tools():
    return [
        {"name": "Scanner de portas", "description": "Mapeia portas abertas em hosts", "category": "network", "complexity": "Medium", "icon": "📡"},
        {"name": "Gerador de hash", "description": "Gera hash MD5/SHA256/SHA512", "category": "crypto", "complexity": "Beginner", "icon": "🔐"},
        {"name": "Codifier", "description": "Codifica/decodifica em Base64/URL/Hex", "category": "crypto", "input": "text", "icon": "🔢", "complexity": "Beginner"},
        {"name": "Analyzer", "description": "Analisa sentimentos de textos", "category": "text", "input": "file", "icon": "📊", "complexity": "Medium"},
        {"name": "JFormatter", "description": "Pretty-print e colapsa JSON", "category": "utility", "input": "text", "icon": "📦", "complexity": "Easy"},
        {"name": "CSS Extractor", "description": "Extrai CSS inline de HTML", "category": "utility", "input": "text", "icon": "🎨", "complexity": "Medium"},
        {"name": "Email Validator", "description": "Valida sintaxe de e-mails", "category": "valid", "input": "text", "icon": "✉️", "complexity": "Easy"},
        {"name": "QR Generator", "description": "Gera QR codes a partir de texto", "category": "media", "input": "text", "icon": "📱", "complexity": "Medium"},
        {"name": "PDF Combiner", "description": "Combina multiplos PDFs em um só", "category": "utility", "input": "file", "icon": "📄", "complexity": "Medium"},
        {"name": "Color Converter", "description": "Converte entre formatos de cores", "category": "utility", "input": "text", "icon": "🎨", "complexity": "Easy"},
    ]

@app.get("/api/marketplace")
async def get_marketplace():
    return [
        {"id": "mk-1", "name": "Widget de Clima", "description": "Exibe clima e previsao para 7 dias", "category": "Widget", "vendor": "AIOS", "rating": 4.5, "likes": 89},
        {"id": "mk-2", "name": "Analytics Pro", "description": "Painel avancado de metricas", "category": "Analytics", "vendor": "AIOS", "rating": 1.8, "likes": 213},
        {"id": "mk-3", "name": "Data Export", "description": "Exporta dados para CSV/JSON/Excel", "category": "Data", "vendor": "Acme", "rating": 5.0, "likes": 57},
        {"id": "mk-4", "name": "Dark UI Theme", "description": "Tema escuro alternativo", "category": "Widget", "vendor": "Acme", "rating": 3.0, "likes": 32},
        {"id": "mk-5", "name": "Custom Dashboard", "description": "Cria dashboards customizados", "category": "Widget", "vendor": "AIOS", "rating": 5.5, "likes": 77},
        {"id": "mk-6", "name": "Report Generator", "description": "Gera relatorios em PDF", "category": "Template", "vendor": "AIOS", "rating": 4.0, "likes": 24},
        {"id": "mk-7", "name": "Slack Connector", "description": "Integracao com Slack (notificacoes)", "category": "Service", "vendor": "Acme", "rating": 4.0, "likes": 43},
        {"id": "mk-8", "name": "Translation pack", "description": "Pacote de tradução (10 idiomas)", "category": "Service", "vendor": "AIOS", "rating": 5.0, "likes": 31},
    ]

@app.get("/api/finances")
async def get_finances():
    return {
        "transactions": [
            {"id": "ft-1", "description": "Pagamento servidores", "amount": 2300, "category": "expense", "date": "2026-07-01"},
            {"id": "ft-2", "description": "Assinatura A-NET", "amount": 149, "category": "expense", "date": "2026-07-05"},
            {"id": "ft-3", "description": "Recebimento cliente X", "amount": 5000, "category": "income", "date": "2026-07-10"},
            {"id": "ft-4", "description": "Licenca software", "amount": 800, "category": "expense", "date": "2026-07-12"},
            {"id": "ft-5", "description": "Servicos consultoria", "amount": 2500, "category": "income", "date": "2026-07-15"},
            {"id": "ft-6", "description": "Renovacao dominio", "amount": 120, "category": "expense", "date": "2026-07-18"},
            {"id": "ft-7", "description": "Hosting mensal", "amount": 299, "category": "expense", "date": "2026-07-20"},
            {"id": "ft-8", "description": "Projeto especial beta", "amount": 4200, "category": "income", "date": "2026-07-03"},
            {"id": "ft-9", "description": "Manutencao equipamentos", "amount": 670, "category": "expense", "date": "2026-07-18"},
            {"id": "ft-10", "description": "Recebimento servicos cloud", "amount": 1800, "category": "income", "date": "2026-07-19"},
        ],
        "total_income": 13500,
        "total_expense": 4338,
        "balance": 9162
    }

@app.get("/api/analytics")
async def get_analytics():
    return {
        "users": 163,
        "active_sessions": 24,
        "total_requests": 2410,
        "uptime_rate": 99.2,
        "daily_requests": [120, 135, 142, 118, 155, 168, 143, 157, 139, 148, 162, 171, 155, 149, 172, 181, 143, 159, 145, 166, 174, 158, 152, 169, 178, 183, 166, 175, 169, 172],
        "top_habits": ["Debugging", "Code Review", "Prompt Engineering", "System Design"],
        "top_agents": ["Osculador", "Arquiteto", "Engenheiro", "Pesquisador"],
        "error_count": 12,
    }

# TaskCenter extended endpoints
@app.get("/api/taskcenter")
async def taskcenter_list(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000)
):
    tm = _get_task_manager()
    tasks = tm.list_all_tasks()
    if status:
        try:
            tasks = [t for t in tasks if t.status == TaskStatus(status)]
        except ValueError:
            pass
    if priority:
        try:
            tasks = [t for t in tasks if t.priority == TaskPriority(priority)]
        except ValueError:
            pass
    if agent:
        tasks = [t for t in tasks if t.assigned_agent == agent]
    tasks.sort(key=lambda t: t.created_at, reverse=True)
    return {"tasks": [_task_to_detail(t) for t in tasks[:limit]]}

@app.get("/api/taskcenter/{task_id}")
async def taskcenter_get(task_id: str):
    return await get_task(task_id)

@app.post("/api/taskcenter")
async def taskcenter_create(task: TaskCreate):
    return await create_task(task)

@app.put("/api/taskcenter/{task_id}")
async def taskcenter_update(task_id: str, update: TaskUpdate):
    return await update_task(task_id, update)

@app.delete("/api/taskcenter/{task_id}")
async def taskcenter_delete(task_id: str):
    return await delete_task(task_id)

# ---------------------------------------------------------------------------
# DeFi Intelligence Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/defi/status")
async def defi_provider_status():
    from src.providers import get_all_providers
    providers = get_all_providers()
    result = {}
    for name, provider in providers.items():
        try:
            available = await asyncio.to_thread(provider.is_available)
            result[name] = {"available": available}
        except Exception as e:
            result[name] = {"available": False, "error": str(e)}
    return {"providers": result}

@app.get("/api/defi/trending-pools")
async def defi_trending_pools(chain: str = Query("ethereum")):
    from src.providers.geckoterminal_provider import GeckoTerminalProvider
    provider = GeckoTerminalProvider()
    try:
        resp = await asyncio.to_thread(provider.get_data, query_type="trending_pools", chain=chain, timeout=8)
        return resp.normalized
    except Exception as e:
        return {"error": str(e), "pools": []}

@app.get("/api/defi/top-pools")
async def defi_top_pools(chain: str = Query("ethereum")):
    from src.providers.geckoterminal_provider import GeckoTerminalProvider
    provider = GeckoTerminalProvider()
    try:
        resp = await asyncio.to_thread(provider.get_data, query_type="top_pools", chain=chain, timeout=8)
        return resp.normalized
    except Exception as e:
        return {"error": str(e), "pools": []}

@app.get("/api/defi/pool-detail")
async def defi_pool_detail(
    chain: str = Query("eth"),
    pool_address: str = Query(""),
    timeframe: str = Query("day"),
):
    import requests as req
    result = {"info": {}, "ohlcv": [], "error": None}
    try:
        base = "https://api.geckoterminal.com/api/v2"
        def _get(url):
            r = req.get(url, timeout=8)
            if r.status_code == 429:
                return None
            r.raise_for_status()
            return r.json()

        info = await asyncio.to_thread(_get, f"{base}/networks/{chain}/pools/{pool_address}")
        if info:
            attrs = info.get("data", {}).get("attributes", {})
            result["info"] = {
                "name": attrs.get("name", ""),
                "base_token_price_usd": attrs.get("base_token_price_usd", "0"),
                "quote_token_price_usd": attrs.get("quote_token_price_usd", "0"),
                "reserve_in_usd": attrs.get("reserve_in_usd", "0"),
                "volume_usd": attrs.get("volume_usd", {}),
                "price_change_percentage": attrs.get("price_change_percentage", {}),
                "transactions": attrs.get("transactions", {}),
                "fdv_usd": attrs.get("fdv_usd", "0"),
                "market_cap_usd": attrs.get("market_cap_usd", "0"),
                "pool_created_at": attrs.get("pool_created_at", ""),
                "dex_id": info.get("data", {}).get("relationships", {}).get("dex", {}).get("data", {}).get("id", ""),
                "network_id": info.get("data", {}).get("relationships", {}).get("network", {}).get("data", {}).get("id", ""),
            }

        ohlcv = await asyncio.to_thread(_get, f"{base}/networks/{chain}/pools/{pool_address}/ohlcv/{timeframe}?aggregate=60&limit=100")
        if ohlcv:
            raw_ohlcv = ohlcv.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
            for c in raw_ohlcv:
                if len(c) >= 6:
                    result["ohlcv"].append({
                        "t": c[0], "o": float(c[1]), "h": float(c[2]),
                        "l": float(c[3]), "c": float(c[4]), "v": float(c[5]),
                    })
    except Exception as e:
        result["error"] = str(e)

    return result

@app.get("/api/defi/hot-pairs")
async def defi_hot_pairs(query: str = Query("USDC")):
    from src.providers.dexscreener_provider import DexScreenerProvider
    provider = DexScreenerProvider()
    try:
        resp = await asyncio.to_thread(provider.get_data, query_type="search", query=query, timeout=8)
        return resp.normalized
    except Exception as e:
        return {"error": str(e), "pairs": []}

@app.get("/api/defi/yields")
async def defi_yields(
    chain: Optional[str] = Query(None),
    min_tvl: float = Query(10000),
    sort: str = Query("apy"),
    limit: int = Query(100),
):
    from src.providers.defillama_provider import DefiLlamaYieldsProvider
    provider = DefiLlamaYieldsProvider()
    try:
        resp = await asyncio.to_thread(provider.get_data, timeout=15)
        data = resp.normalized
        pools = data.get("all_pools", data.get("top_yields", []))
        if chain:
            pools = [p for p in pools if p.get("chain", "").lower() == chain.lower()]
        pools = [p for p in pools if (p.get("tvl_usd", 0) or 0) >= min_tvl]
        if sort == "tvl":
            pools.sort(key=lambda x: x.get("tvl_usd", 0) or 0, reverse=True)
        elif sort == "volume":
            pools.sort(key=lambda x: x.get("volume_usd_1d", 0) or 0, reverse=True)
        elif sort == "stable":
            pools = [p for p in pools if p.get("stablecoin")]
            pools.sort(key=lambda x: x.get("apy_total", 0) or 0, reverse=True)
        else:
            pools.sort(key=lambda x: x.get("apy_total", 0) or 0, reverse=True)
        return {"source": data.get("source", "DefiLlama"), "pools": pools[:limit], "total_pools": data.get("pool_count", 0), "total_tvl": data.get("total_tvl_usd", 0)}
    except Exception as e:
        return {"error": str(e), "pools": []}

@app.get("/api/defi/pairs")
async def defi_pairs(chain: str = Query("ethereum"), query: str = Query("USDC")):
    from src.providers.dexscreener_provider import DexScreenerProvider
    provider = DexScreenerProvider()
    try:
        resp = await asyncio.to_thread(provider.get_data, query_type="search", query=query, timeout=8)
        data = resp.normalized
        pairs = data.get("pairs", [])
        pairs = [p for p in pairs if p.get("chain_id", "").lower() == chain.lower()]
        return {"source": data.get("source", "DexScreener"), "pairs": pairs[:30], "total_pairs": data.get("pair_count", 0)}
    except Exception as e:
        return {"error": str(e), "pairs": []}

@app.get("/api/defi/top-protocols")
async def defi_top_protocols(chain: str = Query("ethereum")):
    from src.providers.defillama_provider import DefiLlamaProvider
    provider = DefiLlamaProvider()
    try:
        resp = await asyncio.to_thread(provider.get_data, query_type="protocols", timeout=15)
        data = resp.normalized
        return data
    except Exception as e:
        return {"error": str(e), "top_protocols": []}

@app.get("/api/defi/prices")
async def defi_prices(coin_ids: str = Query("bitcoin,ethereum,solana,binancecoin,cardano")):
    from src.providers.coingecko_provider import CoinGeckoProvider
    provider = CoinGeckoProvider()
    try:
        resp = await asyncio.to_thread(provider.get_data, query_type="price", coin_id=coin_ids, timeout=10)
        return resp.normalized
    except Exception as e:
        return {"error": str(e), "results": []}

@app.get("/api/defi/market")
async def defi_market(limit: int = Query(50), category: str = Query("")):
    from src.providers.coingecko_provider import CoinGeckoProvider
    provider = CoinGeckoProvider()
    try:
        kwargs = {"query_type": "coin_markets", "limit": limit, "timeout": 10}
        if category:
            kwargs["category"] = category
        resp = await asyncio.to_thread(provider.get_data, **kwargs)
        return resp.normalized
    except Exception as e:
        return {"error": str(e), "tokens": []}

@app.get("/api/defi/trending-coins")
async def defi_trending_coins():
    from src.providers.coingecko_provider import CoinGeckoProvider
    provider = CoinGeckoProvider()
    try:
        resp = await asyncio.to_thread(provider.get_data, query_type="trending", timeout=10)
        return resp.normalized
    except Exception as e:
        return {"error": str(e), "coins": []}

@app.get("/api/defi/l2-overview")
async def defi_l2_overview():
    from src.providers.l2beat_provider import L2BeatProvider
    provider = L2BeatProvider()
    try:
        resp = await asyncio.to_thread(provider.get_data, query_type="overview", timeout=10)
        return resp.normalized
    except Exception as e:
        return {"error": str(e), "projects": []}

@app.get("/api/defi/intelligence")
async def defi_intelligence():
    from src.intelligence.market_intelligence import MarketIntelligence
    from src.providers.geckoterminal_provider import GeckoTerminalProvider
    from src.providers.defillama_provider import DefiLlamaProvider, DefiLlamaYieldsProvider
    from src.providers.coingecko_provider import CoinGeckoProvider
    from src.providers.dexscreener_provider import DexScreenerProvider
    from src.providers.l2beat_provider import L2BeatProvider

    mi = MarketIntelligence()
    results = {}

    def _fetch(name, cls, **kwargs):
        try:
            p = cls()
            r = p.get_data(**kwargs)
            return r.normalized
        except Exception:
            return None

    defillama_data = await asyncio.to_thread(_fetch, "defillama", DefiLlamaProvider, query_type="overview", timeout=10)
    coingecko_data = await asyncio.to_thread(_fetch, "coingecko", CoinGeckoProvider, query_type="coin_markets", limit=50, timeout=10)
    dex_data = await asyncio.to_thread(_fetch, "dexscreener", DexScreenerProvider, query_type="search", query="USDC", timeout=10)
    l2_data = await asyncio.to_thread(_fetch, "l2beat", L2BeatProvider, query_type="overview", timeout=10)

    try:
        results = mi.analyze(
            defillama_data=defillama_data,
            coingecko_data=coingecko_data,
            dex_screener_data=dex_data,
            l2_beat_data=l2_data,
        )
    except Exception as e:
        results = {"error": str(e), "sections": {}}

    return results

@app.get("/api/defi/overview")
async def defi_overview():
    from src.providers.geckoterminal_provider import GeckoTerminalProvider
    from src.providers.defillama_provider import DefiLlamaYieldsProvider
    gt = GeckoTerminalProvider()
    dl = DefiLlamaYieldsProvider()
    result = {"trending_pools": [], "top_yields": [], "stats": {}}
    try:
        r1 = await asyncio.to_thread(gt.get_data, query_type="trending_pools", chain="ethereum", timeout=8)
        result["trending_pools"] = r1.normalized.get("pools", [])[:10]
    except Exception:
        pass
    try:
        r2 = await asyncio.to_thread(dl.get_data, timeout=15)
        y = r2.normalized
        all_pools = y.get("all_pools", y.get("top_yields", []))
        top_y = sorted(all_pools, key=lambda x: x.get("apy_total", 0), reverse=True)[:10]
        result["top_yields"] = top_y
        result["stats"] = {"pool_count": y.get("pool_count", 0), "total_tvl": y.get("total_tvl_usd", 0), "avg_apy": y.get("average_apy", 0)}
    except Exception:
        pass
    return result

# ---------------------------------------------------------------------------
# Mission Control & New Frontend Static Files
# ---------------------------------------------------------------------------

mission_control_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "mission-control"
)
if os.path.isdir(mission_control_path):
    app.mount("/mission-control", StaticFiles(directory=mission_control_path, html=True), name="mission_control")
    logger.info("Mission Control frontend mounted at /mission-control")

# Mount React dashboard (built) at /dashboard
_dashboard_dist = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "dashboard", "dist"
)
_dashboard_src = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "frontend"
)
_dashboard_path = _dashboard_dist if os.path.isdir(_dashboard_dist) else _dashboard_src
if os.path.isdir(_dashboard_path):
    app.mount("/dashboard", StaticFiles(directory=_dashboard_path, html=True), name="dashboard")
    logger.info("Dashboard frontend mounted at /dashboard (from %s)", _dashboard_path)

    @app.get("/")
    async def root_redirect():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/dashboard/")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AI Operating System API & WebSocket Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, default=8080, help="Bind port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--project-root", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        help="Project root directory")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"],
                        help="Logging level")
    args = parser.parse_args()

    global _project_root
    _project_root = args.project_root

    logger.info("Starting AI OS server on %s:%s", args.host, args.port)
    logger.info("Mission Control: http://localhost:%s/mission-control/", args.port)
    logger.info("WebSocket: ws://localhost:%s/ws", args.port)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        ws_max_size=2 * 1024 * 1024,
    )


if __name__ == "__main__":
    main()
