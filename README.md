# AI Operating System

A multi-agent AI operating system that orchestrates specialized AI agents to handle complex software engineering tasks through collaborative intelligence.

## Overview

The AI Operating System (AIOS) is a modular, agent-based architecture where 8 specialized agents work together through a central message bus and orchestrator to decompose, plan, and execute complex tasks autonomously.

## Architecture

```
                    ┌─────────────────┐
                    │   Orchestrator  │
                    │  (Router/Core)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼──┐  ┌───────▼──────┐  ┌───▼──────────┐
    │ Researcher  │  │  Architect   │  │   Engineer   │
    │ (Knowledge) │  │  (Design)    │  │  (Code Gen)  │
    └────────────┘  └──────────────┘  └──────────────┘
              │              │              │
    ┌─────────▼──┐  ┌───────▼──────┐  ┌───▼──────────┐
    │   AI Spec.  │  │  DB Spec.    │  │  Security    │
    │ (ML/Models) │  │ (Data/SQL)   │  │ (Auditing)   │
    └────────────┘  └──────────────┘  └──────────────┘
              │              │              │
              └──────────────┼──────────────┘
                    ┌────────▼────────┐
                    │  Automation     │
                    │  (Workflows)    │
                    └─────────────────┘
```

### The 8 Agents

| Agent | Role | Responsibilities |
|-------|------|------------------|
| **Orchestrator** | Central router | Task decomposition, routing, lifecycle management |
| **Researcher** | Knowledge gatherer | Information retrieval, knowledge base management |
| **Architect** | System designer | Architecture decisions, design patterns, system design |
| **Engineer** | Code builder | Code generation, implementation, refactoring |
| **AI Specialist** | ML expert | Model management, AI/ML tasks, model selection |
| **Database Specialist** | Data handler | Query optimization, schema design, data pipelines |
| **Security Specialist** | Security auditor | Vulnerability scanning, security review, compliance |
| **Automation Specialist** | Workflow engine | Task automation, CI/CD, deployment workflows |

### Core Components

- **Message Bus** — Async inter-agent communication with pub/sub and request/reply patterns
- **Agent Registry** — Tracks agent capabilities, health, and availability
- **System Core** — Lifecycle management, health monitoring, graceful shutdown

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optional, for containerized deployment)

### Local Setup

```bash
# Clone the repository
git clone https://github.com/your-org/ai-operating-system.git
cd ai-operating-system

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for tooling)
npm install

# Copy environment template
cp .env.example .env

# Edit .env with your API keys and configuration
```

### Docker Setup

```bash
docker-compose up -d
```

## Configuration

Configuration is managed through:

- `config/default.json` — Default system settings
- `config/agents.yaml` — Agent-specific configuration
- `.env` — Environment-specific secrets and overrides

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AIOS_LOG_LEVEL` | Logging verbosity | `INFO` |
| `AIOS_HOST` | Server bind address | `0.0.0.0` |
| `AIOS_PORT` | Server port | `8080` |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `AIOS_DB_URL` | Database connection URL | `sqlite:///aios.db` |
| `AIOS_REDIS_URL` | Redis URL for message bus | `redis://localhost:6379` |

## Usage

### Starting the System

```bash
# Local
python -m src.core.system

# Or using the start script
./scripts/start.sh
```

### Programmatic Usage

```python
from src.core.system import AIOS

aios = AIOS()
aios.start()

# Submit a task
result = await aios.submit_task(
    task="Build a REST API for user management",
    priority="high",
    agents=["architect", "engineer"]
)

print(result)
```

### CLI Interface

```bash
# Interactive mode
python -m src.core.system --interactive

# Single task mode
python -m src.core.system --task "Analyze the codebase and suggest improvements"
```

## Project Structure

```
ai-operating-system/
├── config/
│   ├── agents.yaml          # Agent configuration
│   ├── default.json         # Default settings
│   └── settings.py          # Python config loader
├── docs/
│   ├── ARCHITECTURE.md      # Architecture deep-dive
│   └── README.md            # Additional docs
├── scripts/
│   ├── setup.sh             # Environment setup
│   └── start.sh             # System startup
├── src/
│   ├── agents/
│   │   ├── ai_specialist/   # ML/AI agent
│   │   ├── architect/       # System design agent
│   │   ├── automation_specialist/ # Workflow agent
│   │   ├── database_specialist/   # Data agent
│   │   ├── engineer/        # Code generation agent
│   │   ├── orchestrator/    # Central routing agent
│   │   ├── researcher/      # Knowledge agent
│   │   └── security_specialist/  # Security agent
│   ├── core/
│   │   ├── system.py        # System core
│   │   ├── agent_registry.py # Agent tracking
│   │   └── message_bus.py   # Communication layer
│   ├── integrations/
│   │   └── api_gateway.py   # External API gateway
│   └── utils/
│       ├── config_manager.py # Config loading
│       └── logger.py        # Logging utilities
├── tests/
│   └── test_orchestrator.py # Core tests
├── .env.example             # Environment template
├── docker-compose.yml       # Container orchestration
├── package.json             # Node.js tooling config
├── requirements.txt         # Python dependencies
└── LICENSE                  # MIT License
```

## API

The system exposes a REST API through the API gateway:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/tasks` | POST | Submit a new task |
| `/api/v1/tasks/:id` | GET | Get task status |
| `/api/v1/tasks/:id` | DELETE | Cancel a task |
| `/api/v1/agents` | GET | List registered agents |
| `/api/v1/agents/:name/health` | GET | Agent health check |
| `/api/v1/system/health` | GET | System health status |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test module
pytest tests/test_orchestrator.py -v
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Code style and conventions
- Pull request process
- Testing requirements
- Agent development guidelines

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
