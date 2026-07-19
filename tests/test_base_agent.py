"""Tests for the BaseAgent class."""

import os
import pytest
from datetime import datetime

from src.agents.base_agent import BaseAgent, AgentResult, AgentStatus


class MockAgent(BaseAgent):
    """Minimal concrete agent for testing."""

    def execute(self, task):
        return AgentResult(
            success=True,
            output=f"executed: {task.get('description', 'unknown')}",
            execution_time=0.1,
        )

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
        project_root=str(tmp_path),
    )


@pytest.fixture
def failing_agent(tmp_path):
    return FailingAgent(
        name="failing-agent",
        project_root=str(tmp_path),
    )


class TestAgentCreation:
    def test_agent_attributes(self, agent):
        assert agent.name == "test-agent"
        assert agent.status == AgentStatus.IDLE

    def test_agent_capabilities(self, agent):
        caps = agent.get_capabilities()
        assert "testing" in caps
        assert "mocking" in caps

    def test_agent_get_status(self, agent):
        status = agent.get_status()
        assert status["name"] == "test-agent"
        assert status["status"] == "idle"
        assert "testing" in status["capabilities"]


class TestAgentExecution:
    def test_execute_task(self, agent):
        result = agent.execute({"description": "do something"})
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert "executed: do something" in result.output

    def test_execute_with_retry_success(self, agent):
        result = agent._execute_with_retry({"description": "retry task"})
        assert result.success is True
        assert len(agent.execution_history) == 1

    def test_execute_failure_exhausts_retries(self, failing_agent):
        result = failing_agent._execute_with_retry({"description": "fail task"})
        assert result.success is False
        assert len(result.errors) > 0
        assert failing_agent.status == AgentStatus.FAILED


class TestAgentLifecycle:
    def test_start_stop(self, agent):
        agent.start()
        assert agent.status == AgentStatus.IDLE
        agent.stop()
        assert agent.status == AgentStatus.OFFLINE

    def test_reset(self, agent):
        agent._execute_with_retry({"description": "task 1"})
        agent._execute_with_retry({"description": "task 2"})
        assert len(agent.execution_history) == 2
        agent.reset()
        assert len(agent.execution_history) == 0
        assert agent.status == AgentStatus.IDLE
        assert agent._context == {}


class TestAgentContext:
    def test_load_context(self, agent):
        agent.load_context({"architecture": "microservices", "lang": "python"})
        ctx = agent.get_context()
        assert ctx["architecture"] == "microservices"
        assert ctx["lang"] == "python"

    def test_context_is_copy(self, agent):
        agent.load_context({"x": 1})
        ctx = agent.get_context()
        ctx["y"] = 2
        assert "y" not in agent.get_context()

    def test_context_loaded_flag(self, agent):
        assert agent.get_status()["context_loaded"] is False
        agent.load_context({"x": 1})
        assert agent.get_status()["context_loaded"] is True


class TestAgentCanHandle:
    def test_can_handle_matching(self, agent):
        assert agent.can_handle({"keywords": ["testing"]}) is True

    def test_can_handle_no_match(self, agent):
        assert agent.can_handle({"keywords": ["blockchain"]}) is False

    def test_can_handle_empty_keywords(self, agent):
        assert agent.can_handle({}) is False

    def test_can_handle_case_insensitive(self, agent):
        assert agent.can_handle({"keywords": ["TESTING"]}) is True


class TestAgentHistory:
    def test_execution_history(self, agent):
        agent._execute_with_retry({"description": "task 1"})
        agent._execute_with_retry({"description": "task 2"})
        history = agent.get_execution_history()
        assert len(history) == 2
        assert history[0]["success"] is True

    def test_history_is_copy(self, agent):
        agent._execute_with_retry({"description": "task"})
        history = agent.get_execution_history()
        history.clear()
        assert len(agent.get_execution_history()) == 1
