# AI Operating System — Agent Guide

## Quick start
```bash
python -m src.core.orchestrator [--status] [--route "desc"] [--execute "desc"]
python -m src.core.system [--interactive] [--task "..."]
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
- **Agent factory** in `src/agents/__init__.py` — `create_agent(type, root)` and `create_all_agents(root)` with `AGENT_REGISTRY` dict. Agent names: orchestrator, architect, engineer, researcher, ai_specialist, automation, database, security, browser.
- **Two routing layers**: The `Orchestrator` class in `src/core/orchestrator.py` routes via keyword matching against agent capabilities (`DEFAULT_AGENTS`). The `AIOSKernel` in `src/core/kernel.py` has its own `AgentConfig`/`AgentMode` system stored in `.aios/agents/`. They are separate — kernel integrates with orchestrator via `set_orchestrator()`.
- **Core modules** (all stubs or full implementations in `src/core/`): `system.py`, `kernel.py`, `orchestrator.py`, `events.py` (EventBus), `task_manager.py`, `memory.py`, `monitoring.py`, `suggestions.py`, `agent_registry.py` (stub), `message_bus.py` (stub).
- **API** has two servers: `src/api/server.py` (FastAPI, port 8080) and `src/api/kernel_api.py` (JSON API for Mission Control, port 8000). Client library at `src/api/client.py`.

## Key config files
- `config/default.json` — System settings (LLM providers, Redis, agents_config, etc.)
- `config/agents.yaml` — Agent definitions (stub)
- `.env.example` — Environment template
- Configs for agent modes stored per-agent in `.aios/agents/{name}.json`

## Testing quirks
- Pytest markers defined in `pytest.ini` and `conftest.py`: `integration` (real websites), `slow` (network-dependent)
- Skip slow/integration: `pytest -m "not integration and not slow"`
- Browser agent tests require Playwright: `pip install playwright && playwright install chromium`
- `task_manager` persists state to `.task_manager/` directory — clean this between test runs

## Caveats & gotchas
- Several modules are **stubs** with only docstrings (system.py, message_bus.py, agent_registry.py, scripts/*.sh, config/settings.py). If they look empty, that's expected — they're placeholders.
- The `config/agents.yaml` is mostly a stub; real agent config lives in `config/default.json` under `agents_config.*` and in `.aios/agents/*.json`.
- Two separate `Task`/`TaskStatus` dataclasses exist: one in `core/orchestrator.py` (simpler) and one in `core/task_manager.py` (richer, with persistence). They are unrelated.
- Two separate `AgentStatus` enums: `core/orchestrator.py` (IDLE/BUSY/FAILED) and `agents/base_agent.py` (+OFFLINE). Be careful which one you import.
- Backup daemon (`scripts/auto_backup.sh`) auto-pushes commits on a poll interval — be aware when testing.
- `memory/` directory at project root for agent memory persistence.
- `metrics/` and `logs/` dirs at project root — written by the Monitor.
