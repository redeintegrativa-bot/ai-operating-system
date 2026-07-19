# Project State (Auto-Generated)

## Metadata

- **Generated**: 2026-07-19T06:23:49.304680+00:00
- **Commit**: 13fcc56
- **Branch**: master
- **Dirty**: True
- **Project Type**: Node.js

## File Structure

```
|-- config/
|   |-- agents.yaml
|   |-- backup_cron.example
|   |-- default.json
|   |-- logrotate.conf
|   ---settings.py
|-- context/
|   |-- generated/
|   |-- scripts/
|   |   ---generate_context.py
|   |-- templates/
|   |   |-- agents.md
|   |   |-- architecture.md
|   |   |-- project_state.md
|   |   |-- session_history.md
|   |   ---workflow.md
|   ---README.md
|-- docs/
|   |-- ARCHITECTURE.md
|   ---README.md
|-- logs/
|   |-- auto_backup.pid
|   |-- backup.log
|   ---backup_startup.log
|-- scripts/
|   |-- auto_backup.sh
|   |-- cleanup_logs.sh
|   |-- setup.sh
|   |-- start.sh
|   |-- start_backup_service.sh
|   ---view_logs.sh
|-- src/
|   |-- agents/
|   |   |-- ai_specialist/
|   |   |   |-- __init__.py
|   |   |   |-- ai_specialist.py
|   |   |   ---model_manager.py
|   |   |-- architect/
|   |   |   |-- __init__.py
|   |   |   |-- architect.py
|   |   |   ---design_patterns.py
|   |   |-- automation_specialist/
|   |   |   |-- __init__.py
|   |   |   |-- automation_specialist.py
|   |   |   ---workflow_engine.py
|   |   |-- database_specialist/
|   |   |   |-- __init__.py
|   |   |   |-- database_specialist.py
|   |   |   ---query_optimizer.py
|   |   |-- engineer/
|   |   |   |-- __init__.py
|   |   |   |-- code_generator.py
|   |   |   ---engineer.py
|   |   |-- orchestrator/
|   |   |   |-- __init__.py
|   |   |   |-- orchestrator.py
|   |   |   ---task_router.py
|   |   |-- researcher/
|   |   |   |-- __init__.py
|   |   |   |-- knowledge_base.py
|   |   |   ---researcher.py
|   |   ---security_specialist/
|   |       |-- __init__.py
|   |       |-- security_scanner.py
|   |       ---security_specialist.py
|   |-- core/
|   |   |-- __init__.py
|   |   |-- agent_registry.py
|   |   |-- message_bus.py
|   |   ---system.py
|   |-- integrations/
|   |   |-- __init__.py
|   |   ---api_gateway.py
|   ---utils/
|       |-- __init__.py
|       |-- config_manager.py
|       ---logger.py
|-- tests/
|   |-- __init__.py
|   ---test_orchestrator.py
|-- CONTRIBUTING.md
|-- LICENSE
|-- README.md
|-- docker-compose.yml
|-- package.json
---requirements.txt
```

## File Statistics

- **Total files**: 66

### By Extension

| Extension | Count |
|-----------|-------|
| `.py` | 37 |
| `.md` | 10 |
| `.sh` | 6 |
| `.json` | 3 |
| `(no ext)` | 2 |
| `.log` | 2 |
| `.txt` | 1 |
| `.yml` | 1 |
| `.yaml` | 1 |
| `.example` | 1 |
| `.conf` | 1 |
| `.pid` | 1 |

## Dependencies

### Runtime

| Package | Version/Info |
|---------|-------------|
| `express` | `^4.18.2` |
| `ioredis` | `^5.3.2` |
| `winston` | `^3.11.0` |
| `zod` | `^3.22.4` |
| `uuid` | `^9.0.0` |
| `dotenv` | `^16.3.1` |
| `cors` | `^2.8.5` |
| `helmet` | `^7.1.0` |
| `compression` | `^1.7.4` |
| `rate-limiter-flexible` | `^4.0.1` |

### Dev

| Package | Version/Info |
|---------|-------------|
| `@types/express` | `^4.17.21` |
| `@types/node` | `^20.10.0` |
| `@types/cors` | `^2.8.17` |
| `@types/uuid` | `^9.0.7` |
| `typescript` | `^5.3.2` |
| `eslint` | `^8.55.0` |
| `@typescript-eslint/eslint-plugin` | `^6.13.1` |
| `@typescript-eslint/parser` | `^6.13.1` |
| `prettier` | `^3.1.0` |
| `jest` | `^29.7.0` |
| `@types/jest` | `^29.5.11` |
| `ts-jest` | `^29.1.1` |
| `nodemon` | `^3.0.2` |
| `docsify-cli` | `^4.4.4` |

## Key Directories

| Directory | Exists |
|-----------|--------|
| `src/` | Yes |
| `lib/` | No |
| `tests/` | Yes |
| `docs/` | Yes |
| `scripts/` | Yes |
| `config/` | Yes |
| `.github/` | No |
| `context/` | Yes |