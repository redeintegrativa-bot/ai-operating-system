"""Tests for the BaseAgent class."""

import os
import pytest
from datetime import datetime

from src.agents.base_agent import BaseAgent


class MockAgent(BaseAgent):
    """Minimal concrete agent for testing."""

    def execute(self, task):
        return {"result": f"executed: {task.get('description', 'unknown')}"}

    def get_capabilities(self):
        return ["testing", "mocking"]


class FailingAgent(BaseAgent):
    """Agent that always fails."""

    def execute(self, task):
        raise RuntimeError("Intentional failure")

    def get_capabilities(self):
        return ["failing"]


@pytest.fixture
def agent(tmp_path):
    return MockAgent(
        name="test-agent",
        description="A test agent",
        project_root=str(tmp_path),
    )


@pytest.fixture
def failing_agent(tmp_path):
    return FailingAgent(
        name="failing-agent",
        description="Always fails",
        project_root=str(tmp_path),
    )


class TestAgentCreation:
    def test_agent_attributes(self, agent):
        assert agent.name == "test-agent"
        assert agent.description == "A test agent"

    def test_agent_capabilities(self, agent):
        caps = agent.get_capabilities()
        assert "testing" in caps
        assert "mocking" in caps


class TestAgentExecution:
    def test_execute_task(self, agent):
        result = agent.execute({"description": "do something"})
        assert result["result"] == "executed: do something"

    def test_execute_failure(self, failing_agent):
        with pytest.raises(RuntimeError, match="Intentional"):
            failing_agent.execute({"description": "fail"})


class TestAgentLifecycle:
    def test_agent_lifecycle(self, agent):
        agent.start()
        assert agent.status == "running"
        agent.stop()
        assert agent.status == "stopped"
