# AI Operating System — Agent Guide

## Quick start
```bash
scripts/aios start          # Start API server (port 8080)
scripts/aios restart        # Restart API server
scripts/aios dashboard      # Start + open dashboard in browser
scripts/aios serve          # Start server + Cloudflare tunnel (full stack)
scripts/aios serve --deploy # Serve + tunnel + update Vercel env + deploy
scripts/aios status         # Show system status
scripts/aios stop           # Stop server (also stops tunnel)
scripts/aios build          # Build dashboard (Vite)
scripts/aios tunnel         # Start Cloudflare tunnel (exposes local API publicly)
scripts/aios tunnel stop    # Stop tunnel
scripts/aios tunnel logs    # Tail tunnel logs
scripts/aios deploy         # Deploy dashboard to Vercel (preview)
scripts/aios deploy --prod  # Deploy to Vercel (production)
scripts/aios logs           # Tail server logs
```
Python deps: `pip install -r requirements.txt`. Node deps only needed for dashboard (`cd dashboard && npm install`).

## Web Deployment Architecture
- **Vercel** (https://ai-operating-system-sable.vercel.app): Serves the React dashboard (static files)
- **Cloudflare Tunnel**: Exposes local API server (port 8080) publicly via `https://*.trycloudflare.com`
- **Connection**: Dashboard (Vercel) → API (tunnel URL) via `VITE_API_URL` env var embedded at build time
- **Note**: trycloudflare.com URLs change on each tunnel restart. Use `aios tunnel start` to get a new URL, then `aios deploy --prod` to update Vercel.

## Dashboard (React + Vite + Tailwind)
```bash
cd dashboard && npm install && npm run dev   # Dev server (Vite, port 5173)
cd dashboard && npm run build                # Build to dashboard/dist/
```
- 14 pages: Home, Mission Control, Capability Map, AI Chat, Agents, Tasks, Memory, Scheduler, Plugins, Integrations, DeFi Intelligence, Logs, Settings, System Status
- WebSocket: `ws://localhost:8080/ws` — subscribe via `{"type":"subscribe","events":["*"]}`
- API proxy: Vite dev server proxies `/api` and `/ws` to localhost:8080
- For Vercel: `npm run build` outputs to `dashboard/dist/`, configured via `vercel.json`
- For local use: FastAPI serves `dashboard/dist/` at `/dashboard/` (auto-detected)

## API endpoints (port 8080)
All under `/api/`: `status`, `metrics`, `health`, `system`, `agents`, `tasks`, `memory/:agent`, `logs`, `plugins`, `capabilities`, `settings`, `skills`, `suggestions`, `workspaces`, `missions`, `tools`, `marketplace`, `finances`, `analytics`, `taskcenter`
WebSocket at `/ws`

## Python commands
```bash
pytest tests/ -v                                    # all tests (default: -v --tb=short via pytest.ini)
pytest tests/test_orchestrator.py::test_route_task  # single test
pytest -m "not integration and not slow"            # skip slow/integration
ruff check src/ tests/                              # lint
```
No typecheck configured (mypy in requirements.txt but no mypy.ini or pyproject.toml config).

## Architecture
- **Event-driven multi-agent system**: EventBus (pub/sub) + Orchestrator (keyword routing) + AIOSKernel (AgentManager, HeartbeatMonitor, Scheduler)
- **Entrypoint**: `AIOS` class in `src/core/system.py` — `python -m src.core.system`
- **API server**: `src/api/server.py` — `python -m src.api.server --port 8080` (FastAPI, serves dashboard)
- **Agent factory**: `src/agents/__init__.py` — `AGENT_REGISTRY` dict. Agents: orchestrator, architect, engineer, researcher, ai_specialist, automation, database, security, browser.
- **Two routing layers**: `Orchestrator` (src/core/orchestrator.py) routes via keyword matching. `AIOSKernel` (src/core/kernel.py) has its own AgentConfig/AgentMode in `.aios/agents/`. Connected via `set_orchestrator()`.
- **Two API servers**: `src/api/server.py` (FastAPI, port 8080, serves dashboard) and `src/api/kernel_api.py` (JSON, port 8000)
- **WebSocket**: `src/api/websocket_server.py` — EventBus-to-WebSocket bridge, clients subscribe to events

## Key config files
- `config/default.json` — System settings (LLM providers, Redis, agents_config)
- `.env.example` — Environment template (copy to `.env`, gitignored)
- Agent modes stored in `.aios/agents/{name}.json`
- `vercel.json` — Vercel deployment config (builds dashboard, serves from dashboard/dist)
- `.vercel/project.json` — Vercel project linking (org: redeintegrativa-1029)
- `.aios/tunnel.pid` — Cloudflare tunnel process tracking
- `logs/tunnel.log` — Cloudflare tunnel logs

## Persistence directories
| Directory | Contents | Auto-pruned |
|-----------|----------|-------------|
| `memory/agents/*.json` | Agent memories | >90d stale |
| `.aios/agents/*.json` | Kernel AgentConfig | No |
| `.task_manager/tasks.json` | TaskManager state | Tasks >7d completed |
| `context/generated/` | Project snapshot | Regenerated on startup |
| `logs/` | Rotating logs | No |

## Testing quirks
- Pytest markers: `integration` (real websites), `slow` (network-dependent)
- Browser agent tests require Playwright: `pip install playwright && playwright install chromium`
- `task_manager` persists state to `.task_manager/` — clean between test runs

## Caveats & gotchas
- Stubs: `message_bus.py`, `agent_registry.py`, `scripts/setup.sh`, `scripts/start.sh`, `config/settings.py`, `config/agents.yaml` — all contain only comments, no implementation
- `src/providers/` has DeFi data providers (coingecko, defillama, dexscreener, etc.) — not wired into agents yet
- Two separate `Task`/`TaskStatus` dataclasses: `core/orchestrator.py` vs `core/task_manager.py` — different fields, not interchangeable
- Two separate `AgentStatus` enums: `core/orchestrator.py` (IDLE, BUSY) vs `agents/base_agent.py` (IDLE, BUSY, FAILED, OFFLINE)
- Backup daemon (`scripts/auto_backup.sh`) auto-pushes commits — aware when testing
- Dashboard: `frontend/` is legacy HTML/CSS/JS; `dashboard/` is the React app (use this)
- `.gitignore` ignores `.env*` — `.env.example` is tracked, `.env` is not
- Sibling project `../maia-content-engine/` is a separate Next.js app (not part of this system)
