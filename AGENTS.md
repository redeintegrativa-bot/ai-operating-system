# AI Operating System — Agent Guide

## Quick start
```bash
python -m src.core.system [--status] [--task "..."] [--interactive]
python -m src.core.orchestrator [--status] [--route "desc"] [--execute "desc"]
python -m src.core.kernel status
python -m src.api.server --port 8080
python -m src.api.kernel_api --port 8000
```

## Python commands (single test, package, verification)
```bash
pytest tests/ -v                                     # all tests
pytest tests/test_orchestrator.py -v                 # single file
pytest tests/test_orchestrator.py::test_route_task   # single test
pytest --cov=src --cov-report=html                   # coverage
pytest -m "not integration"                          # skip slow/integration
ruff check src/ tests/                               # lint (ruff)
```

## Architecture

- **Event-driven multi-agent system**: Agents communicate via `EventBus` (pub/sub), coordinated by `Orchestrator` (keyword-based routing). Also has `AIOSKernel` (AgentManager, HeartbeatMonitor, Scheduler).
- **System entrypoint**: `AIOS` class in `src/core/system.py` — initializes all subsystems, loads persisted state, runs context refresh and memory pruning on startup. Use `python -m src.core.system` to start.
- **Agent factory** in `src/agents/__init__.py` — `create_agent(type, root)` and `create_all_agents(root)` with `AGENT_REGISTRY` dict. Agent names: orchestrator, architect, engineer, researcher, ai_specialist, automation, database, security, browser.
- **Two routing layers**: The `Orchestrator` class in `src/core/orchestrator.py` routes via keyword matching against agent capabilities (`DEFAULT_AGENTS`). The `AIOSKernel` in `src/core/kernel.py` has its own `AgentConfig`/`AgentMode` system stored in `.aios/agents/`. They are separate — kernel integrates with orchestrator via `set_orchestrator()`.
- **Core modules**: `system.py` (entrypoint), `kernel.py`, `orchestrator.py`, `events.py` (EventBus), `task_manager.py`, `memory.py`, `monitoring.py`, `suggestions.py`.
- **API** has two servers: `src/api/server.py` (FastAPI, port 8080) and `src/api/kernel_api.py` (JSON API for Mission Control, port 8000). Client library at `src/api/client.py`.

## Key config files
- `config/default.json` — System settings (LLM providers, Redis, agents_config, etc.)
- `config/agents.yaml` — Agent definitions (stub)
- `.env.example` — Environment template
- Configs for agent modes stored per-agent in `.aios/agents/{name}.json`

## Context system
- `context/scripts/reconstruct_context.py` — Scans project, analyzes git, reads config, generates `context/generated/project_snapshot.json` and `context_summary.md`
- `context/scripts/load_context.py` — Loads context with levels: `full`, `summary`, `minimal`; auto-regenerates if stale (>5 min)
- `context/scripts/context_integration.py` — Hooks for orchestrator: `pre_task_hook()`, `post_task_hook()`, `get_context_for_agent()`
- `context/scripts/generate_context.py` — Generates context from templates with `{{variable}}` placeholders
- On startup, `AIOS.start()` runs `reconstruct_context.py` automatically

## Persistence directories
| Directory | Contents | Auto-pruned on startup |
|-----------|----------|-----------------------|
| `memory/agents/*.json` | Agent memories (Episodic, Semantic, Procedural) | Memories >90d stale |
| `.aios/agents/*.json` | Kernel AgentConfig per agent | No |
| `.aios/suggestions/inbox.json` | Suggestion inbox | No |
| `.task_manager/tasks.json` | TaskManager state | Tasks >7d completed |
| `context/generated/` | Project snapshot, summary | Regenerated on startup |
| `logs/` | Rotating logs | No |
| `metrics/` | Metric exports | No |

## Testing quirks
- Pytest markers: `integration` (real websites), `slow` (network-dependent)
- Skip slow/integration: `pytest -m "not integration and not slow"`
- Browser agent tests require Playwright: `pip install playwright && playwright install chromium`
- `task_manager` persists state to `.task_manager/` — clean between test runs

## Caveats & gotchas
- Several modules were **stubs** and are now implemented: `system.py` (full AIOS entrypoint), `config_manager.py` (JSON+env config), `logger.py` (structured JSON logging with rotation)
- Still stubs: `message_bus.py`, `agent_registry.py`, scripts/*.sh, `config/settings.py`
- Two separate `Task`/`TaskStatus` dataclasses: `core/orchestrator.py` (simpler) and `core/task_manager.py` (richer, persistent)
- Two separate `AgentStatus` enums: `core/orchestrator.py` (IDLE/BUSY/FAILED) and `agents/base_agent.py` (+OFFLINE)
- Backup daemon (`scripts/auto_backup.sh`) auto-pushes commits — be aware when testing
