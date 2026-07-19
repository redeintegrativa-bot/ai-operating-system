# Architecture

Detailed technical architecture of the AI Operating System.

## System Overview

AIOS is a distributed multi-agent system built on an event-driven architecture. Agents communicate asynchronously through a message bus, coordinated by a central orchestrator that handles task decomposition, routing, and lifecycle management.

## Core Principles

1. **Agent Autonomy** — Each agent operates independently and makes local decisions within its domain
2. **Loose Coupling** — Agents communicate only through the message bus; no direct agent-to-agent calls
3. **Message-Driven** — All interactions are asynchronous messages, enabling non-blocking parallel execution
4. **Fault Isolation** — Agent failures are contained and retried without crashing the system
5. **Observable** — Every message, decision, and state change is logged and traceable

## Component Architecture

### Message Bus

The message bus is the communication backbone. It supports three patterns:

- **Publish/Subscribe** — Broadcast messages to all subscribers (e.g., health broadcasts)
- **Request/Reply** — Synchronous-style calls with correlation IDs (e.g., agent queries)
- **Task Queue** — Durable queues for work distribution (e.g., task assignment)

Implementation uses Redis Streams for durability and at-least-once delivery guarantees.

```
Producer → Stream → Consumer Group → Agent
                ↓
          Dead Letter Queue (failed messages)
```

### Agent Registry

The registry maintains real-time state for all agents:

```yaml
AgentState:
  name: string           # Unique agent identifier
  status: enum           # ready | busy | degraded | offline
  capabilities: list     # What this agent can do
  current_task: uuid     # Active task ID (if busy)
  health:
    last_heartbeat: datetime
    success_rate: float  # 0.0 - 1.0
    avg_response_ms: int
    error_count: int
  metadata: dict         # Agent-specific info
```

### Orchestrator

The orchestrator is the brain of the system. It handles:

1. **Task Analysis** — Parse incoming requests to understand intent and requirements
2. **Decomposition** — Break complex tasks into subtasks with dependencies
3. **Routing** — Match subtasks to agents based on capabilities and availability
4. **Scheduling** — Determine execution order, respecting dependencies
5. **Aggregation** — Collect results from agents and compose final output
6. **Error Handling** — Detect failures, retry, re-route, or escalate

#### Routing Algorithm

```
function route(task):
    candidates = registry.find_by_capability(task.required_capabilities)
    candidates = filter(candidates, status == READY)
    candidates = sort(candidates, by=score(task, agent))

    if candidates is empty:
        queue(task, retry_after=30s)
        return

    best = candidates[0]
    assign(task, best)
```

Scoring factors:
- Capability match score (0-1)
- Agent load (fewer active tasks = higher score)
- Historical success rate on similar tasks
- Response time percentiles

### Agent Base Class

All agents extend a common base:

```python
class BaseAgent:
    name: str
    capabilities: list[str]

    async def initialize(self) -> None
    async def execute(self, task: Task) -> TaskResult
    async def health_check(self) -> HealthStatus
    async def shutdown(self) -> None
```

### Agent Implementations

#### Researcher

- Queries web APIs, documentation, and knowledge bases
- Maintains a vector store of retrieved information
- Returns structured findings with sources and confidence scores

#### Architect

- Analyzes system requirements and proposes designs
- Recommends design patterns based on constraints
- Produces architecture decision records (ADRs)

#### Engineer

- Generates code based on specifications
- Handles multiple languages and frameworks
- Applies tests and validates generated code

#### AI Specialist

- Manages ML model lifecycle (selection, fine-tuning, deployment)
- Handles prompt engineering and chain optimization
- Monitors model performance and drift

#### Database Specialist

- Designs and optimizes database schemas
- Writes and optimizes SQL queries
- Manages data migrations and ETL pipelines

#### Security Specialist

- Scans code for vulnerabilities (OWASP Top 10, SAST/DAST)
- Reviews access controls and authentication
- Checks compliance with security standards

#### Automation Specialist

- Creates and manages CI/CD pipelines
- Automates repetitive workflows
- Handles deployment orchestration

#### Browser Agent

- Web browsing and navigation with Playwright
- Page scraping and content extraction
- OCR (Optical Character Recognition) for image text extraction
- Screenshot capture of web pages
- File download from web sources
- Web search and result extraction
- JSON data extraction from web content

Helper modules:
- `page_scraper.py` — HTML parsing and content extraction
- `ocr_engine.py` — Image-to-text conversion using Tesseract

## Data Flow

```
User Request
    │
    ▼
┌─────────────┐
│  API Gateway │  ── Authentication, rate limiting, validation
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────────────────────────────┐
│ Orchestrator │ ◄── │           AIOS Kernel                │
└──────┬──────┘     │  ┌──────────────┐  ┌──────────────┐ │
       │            │  │ AgentManager │  │  Heartbeat   │ │
       │            │  │  (modes,     │  │   Monitor    │ │
       │            │  │   config)    │  │  (health)    │ │
       │            │  └──────────────┘  └──────────────┘ │
       │            │  ┌──────────────┐                   │
       │            │  │   Scheduler  │                   │
       │            │  │  (missions)  │                   │
       │            │  └──────────────┘                   │
       │            └─────────────────────────────────────┘
       │                        │
       │                        ▼
       │            ┌─────────────────────┐
       │            │  Suggestion Inbox    │
       │            │  (agent suggestions) │
       │            └─────────────────────┘
       │
       ├──────────────────┬──────────────────┬──────────────────┐
       ▼                  ▼                  ▼                  ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Agent A    │   │   Agent B    │   │   Agent C    │   │  Agent D     │
│  (parallel)  │   │  (parallel)  │   │  (parallel)  │   │  (parallel)  │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                  │                  │                  │
       └──────────────────┼──────────────────┼──────────────────┘
                          ▼
                   ┌─────────────┐
                   │  Aggregator  │  ── Merge results, resolve conflicts
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Response   │  ── Formatted output to user
                   └─────────────┘
```

## Task Lifecycle

```
PENDING → ROUTING → ASSIGNED → RUNNING → COMPLETED
                                  │
                                  ├→ FAILED → RETRYING → ASSIGNED
                                  │
                                  └→ TIMEOUT → FAILED
```

## Fault Tolerance

- **Agent crashes**: Detected via missed heartbeats; task re-routed to another agent
- **Message loss**: Redis Streams provide at-least-once delivery; idempotency keys prevent duplication
- **Timeout handling**: Tasks have configurable timeouts; exceeded tasks are cancelled and retried
- **Circuit breaker**: Agents with high failure rates are temporarily taken offline

## Core Engine Modules

### AIOS Kernel (`src/core/kernel.py`)

Central infrastructure for agent intelligence. Provides AgentManager, Heartbeat monitoring, and Scheduler for recurring missions.

```
┌─────────────────────────────────────────────────────────┐
│                      AIOSKernel                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ AgentManager │  │  Heartbeat   │  │   Scheduler  │  │
│  │              │  │   Monitor    │  │              │  │
│  │ • register   │  │ • record     │  │ • add_mission│  │
│  │ • set_mode   │  │ • get_stale  │  │ • get_due    │  │
│  │ • get_all    │  │ • get_all    │  │ • start/stop │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         └─────────────────┼─────────────────┘           │
│                           ▼                             │
│              ┌────────────────────────┐                 │
│              │    Integrations        │                 │
│              │ • Orchestrator         │                 │
│              │ • EventBus             │                 │
│              │ • Monitor              │                 │
│              └────────────────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

**AgentManager:** Dynamic agent registration with modes (Manual/Assisted/Autonomous), persistence in `.aios/agents/`, and auto_suggest control.

**HeartbeatMonitor:** Tracks agent health via periodic heartbeats. Detects stale agents (configurable timeout), tracks latency and active tasks.

**Scheduler:** Recurring mission engine with cron expressions or intervals. Runs as daemon thread with 10s poll. Tracks last_run, next_run, run_count.

**Agent Modes:**
- `manual` — Requires explicit user approval for all actions
- `assisted` — Operates with user supervision; suggests actions
- `autonomous` — Full independence; executes without human intervention

### Suggestion Inbox (`src/core/suggestions.py`)

Agent-generated suggestions for human review. No automatic execution — user must approve/reject each suggestion.

```
┌─────────────────────────────────────────────────────────┐
│                  SuggestionInbox                         │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │                   Workflow                        │  │
│  │                                                  │  │
│  │  Agent ──► add() ──► PENDING ──► APPROVED        │  │
│  │                          │            │          │  │
│  │                          ▼            ▼          │  │
│  │                      REJECTED    EXECUTED        │  │
│  │                          │                      │  │
│  │                          ▼                      │  │
│  │                      DISMISSED                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  SuggestionGenerator:                                   │
│  • create_improvement()  • create_research()            │
│  • create_question()     • create_mission_idea()        │
└─────────────────────────────────────────────────────────┘
```

**Suggestion Types:**
- `improvement` — Code or system improvement suggestions
- `research` — Research topics suggested by agents
- `question` — Strategic questions for the user
- `mission` — Recurring mission ideas

**Features:** Filter by agent/type/status/priority, JSON persistence in `.aios/suggestions/`, statistics, recent suggestions.

### Event System (`src/core/events.py`)

Enables decoupled communication between components via publish/subscribe:

```
┌──────────────┐   publish()   ┌──────────┐   dispatch   ┌──────────────┐
│ Publisher     │ ──────────►  │ EventBus │ ──────────►  │ Handler(s)   │
│ (any module)  │              │          │              │ (subscribers) │
└──────────────┘              └──────────┘              └──────────────┘
                                    │
                              ┌─────▼─────┐
                              │  History   │  (replay, archival)
                              └───────────┘
```

**Event Types:** `TASK_CREATED`, `TASK_ASSIGNED`, `TASK_COMPLETED`, `TASK_FAILED`, `AGENT_STARTED`, `AGENT_STOPPED`, `AGENT_FAILED`, `SYSTEM_STARTUP`, `SYSTEM_SHUTDOWN`, `SYSTEM_ERROR`

**Features:** Thread-safe, wildcard subscriptions, priority ordering, event filtering (by source/type/data), event archival to JSON, event replay, async queue processing.

### Task Manager (`src/core/task_manager.py`)

Manages the full task lifecycle with persistence:

```
CREATED → PENDING → ASSIGNED → RUNNING → COMPLETED
                                    │
                                    ├→ FAILED → (auto-retry) → PENDING
                                    │
                                    └→ CANCELLED
```

**Features:** Priority levels (LOW/MEDIUM/HIGH/CRITICAL), dependency tracking, automatic retry with configurable max, task statistics, history tracking, JSON persistence, export/import.

### Memory System (`src/core/memory.py`)

Provides persistent memory for agents across sessions:

- **Episodic** — Task-specific experiences and outcomes
- **Semantic** — Knowledge, facts, and learned patterns  
- **Procedural** — How-to knowledge and workflows

**Features:** Keyword-based search with relevance scoring (keyword match + importance + recency + frequency), memory sharing between agents, consolidation of similar memories, per-agent persistence, shared memory index.

### Monitoring System (`src/core/monitoring.py`)

Provides observability into system health and performance:

- **Structured Logging** — JSON-formatted logs with rotation (10MB files, 5 backups)
- **Metrics Collection** — CPU, memory, disk usage; task/agent metrics
- **Health Checks** — CPU load, memory usage, log directory accessibility
- **Alerting** — Automatic alerts on ERROR/CRITICAL log entries
- **Report Generation** — Full system report with health status and recent alerts

## API Layer (`src/api/`)

REST API for external system integration (FastAPI):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tasks` | POST/GET | Create/list tasks |
| `/api/tasks/{id}` | GET/PUT/DELETE | Task CRUD |
| `/api/agents` | GET | List all agents |
| `/api/agents/{name}` | GET | Agent details |
| `/api/agents/{name}/execute` | POST | Execute task on agent |
| `/api/status` | GET | System status |
| `/api/metrics` | GET | System metrics |
| `/api/health` | GET | Health check |

**Features:** CORS support, request validation, auto-generated OpenAPI docs, client library (`src/api/client.py`).

## Test Suite (`tests/`)

180+ unit tests covering all core modules:

| Module | Tests | Coverage |
|--------|-------|----------|
| BaseAgent | 17 | Lifecycle, execution, retry, context, capabilities |
| TaskManager | 35 | CRUD, lifecycle, persistence, stats, dependencies |
| Memory | 18 | CRUD, search, sharing, consolidation, persistence |
| EventBus | 24 | Publishing, subscribing, filtering, archiving, replay |
| Monitor | 21 | Logging, metrics, health, alerts, reports |
| AIOS Kernel | 40 | AgentManager, HeartbeatMonitor, Scheduler, CLI, persistence |
| Suggestion Inbox | 25 | CRUD, review workflow, filters, stats, persistence |
| Browser Agent | 20 | Browse, scrape, OCR, screenshot, download, search, extract_json |

Run with: `python -m pytest tests/ -v`

## Scaling

- **Horizontal**: Add more agent instances; the message bus distributes work automatically
- **Vertical**: Increase agent capabilities or add new agent types via the registry
- **Sharding**: Tasks can be sharded by type, priority, or domain

## Security Model

- API gateway handles authentication (API keys, JWT tokens)
- Inter-agent communication is authenticated via service tokens
- All messages are signed and verified
- Agent permissions are scoped to their capabilities
- Sensitive data is encrypted at rest and in transit
