# Contributing to AI Operating System

Thank you for considering contributing to AIOS. This guide covers the conventions, workflows, and standards for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/ai-operating-system.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Set up the development environment (see README.md)
5. Make your changes
6. Run tests and linting
7. Submit a pull request

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available
npm install

# Run pre-commit hooks
pre-commit install

# Verify everything works
pytest
npm run lint
```

## Code Style

### Python

- Follow PEP 8 (enforced by `ruff`)
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use `snake_case` for functions and variables
- Use `PascalCase` for classes
- Use `UPPER_SNAKE_CASE` for constants
- Docstrings for all public functions (Google style)

```python
async def route_task(self, task: Task) -> RoutingDecision:
    """Route a task to the most suitable agent.

    Args:
        task: The task to route.

    Returns:
        The routing decision with assigned agent.

    Raises:
        NoAgentAvailable: If no agent can handle the task.
    """
```

### TypeScript/JavaScript

- Use ESLint and Prettier (configs provided)
- Prefer `const` over `let`
- Use async/await over raw promises
- Type all function parameters and return values

### YAML/JSON

- Use 2-space indentation for YAML
- Use 2-space indentation for JSON
- Order keys alphabetically in JSON config files

## Commit Messages

Follow Conventional Commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style change (no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build, CI, or tooling changes

Examples:
```
feat(orchestrator): add parallel task execution
fix(researcher): handle empty search results
docs(architecture): add scaling section
test(engineer): add code generation tests
```

## Pull Request Process

1. **Keep PRs focused** — One feature or fix per PR
2. **Write a clear description** — What changed, why, and how to test it
3. **Link related issues** — Reference GitHub issues with `Fixes #123`
4. **Ensure CI passes** — All tests, linting, and type checks must pass
5. **Request review** — At least one maintainer review required
6. **Address feedback** — Make requested changes in new commits (don't force-push during review)

### PR Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactoring
- [ ] Documentation
- [ ] Other (describe)

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist

- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated (if needed)
- [ ] No new warnings or errors
```

## Adding a New Agent

Agents are the core extension points. To add a new agent:

### 1. Create the Agent Directory

```
src/agents/your_agent/
├── __init__.py
├── your_agent.py       # Main agent implementation
└── helper_module.py    # Agent-specific utilities
```

### 2. Implement the Base Interface

```python
from src.agents.base import BaseAgent

class YourAgent(BaseAgent):
    name = "your_agent"
    capabilities = ["capability_a", "capability_b"]

    async def initialize(self) -> None:
        """Set up agent resources."""
        pass

    async def execute(self, task: Task) -> TaskResult:
        """Process an assigned task."""
        pass

    async def health_check(self) -> HealthStatus:
        """Report agent health."""
        pass

    async def shutdown(self) -> None:
        """Clean up resources."""
        pass
```

### 3. Register the Agent

Add to `config/agents.yaml`:

```yaml
your_agent:
  enabled: true
  priority: 3
  capabilities:
    - capability_a
    - capability_b
  settings:
    # Agent-specific configuration
```

### 4. Write Tests

```python
import pytest
from src.agents.your_agent import YourAgent

@pytest.mark.asyncio
async def test_your_agent_execute():
    agent = YourAgent()
    await agent.initialize()
    result = await agent.execute(mock_task)
    assert result.success is True
```

### 5. Update Documentation

Add your agent to the README.md agent table and docs/ARCHITECTURE.md.

## Testing Guidelines

### Unit Tests

- Test each agent independently
- Mock external dependencies (LLM APIs, databases)
- Test both success and failure paths
- Aim for >80% code coverage on new code

```bash
pytest tests/unit/ -v --cov=src --cov-report=term-missing
```

### Integration Tests

- Test agent communication through the message bus
- Test orchestrator routing with multiple agents
- Test system startup and shutdown

```bash
pytest tests/integration/ -v
```

### Running Specific Tests

```bash
# Single test file
pytest tests/test_orchestrator.py -v

# Single test function
pytest tests/test_orchestrator.py::test_route_task -v

# With coverage
pytest --cov=src.agents.orchestrator tests/test_orchestrator.py
```

## Reporting Issues

When filing an issue, include:

- **Environment**: OS, Python version, Node version
- **Steps to reproduce**: Minimal steps to trigger the bug
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Logs**: Relevant log output (sanitize secrets)

## Code of Conduct

- Be respectful and constructive
- Focus on technical merit
- Welcome newcomers and help them get started
- Disagreements are fine; personal attacks are not

## Questions?

Open a GitHub Discussion for general questions or ideas.
