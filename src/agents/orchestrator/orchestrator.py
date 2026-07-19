from typing import Any, Dict, List
from ..base_agent import BaseAgent, AgentResult


class OrchestratorAgent(BaseAgent):
    def __init__(self, project_root: str):
        super().__init__("orchestrator", project_root)
        self._registered_agents: List[BaseAgent] = []

    def execute(self, task: Dict) -> AgentResult:
        task_type = task.get("type", "route")
        if task_type == "route":
            return self._route_task(task)
        elif task_type == "coordinate":
            return self._coordinate_task(task)
        elif task_type == "status":
            return self._get_system_status()
        else:
            return AgentResult(
                success=False,
                output=None,
                errors=[f"Unknown task type: {task_type}"],
            )

    def get_capabilities(self) -> List[str]:
        return [
            "route",
            "coordinate",
            "orchestrate",
            "dispatch",
            "manage",
            "status",
            "monitor",
            "aggregate",
        ]

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator."""
        self._registered_agents.append(agent)
        self.logger.info(f"Registered agent: {agent.name}")

    def unregister_agent(self, agent_name: str):
        """Unregister an agent by name."""
        self._registered_agents = [
            a for a in self._registered_agents if a.name != agent_name
        ]

    def find_agent(self, task: Dict) -> BaseAgent:
        """Find the best agent for a task."""
        for agent in self._registered_agents:
            if agent.status.value == "idle" and agent.can_handle(task):
                return agent
        return None

    def _route_task(self, task: Dict) -> AgentResult:
        agent = self.find_agent(task)
        if agent is None:
            return AgentResult(
                success=False,
                output=None,
                errors=["No suitable agent found for task"],
            )
        result = agent._execute_with_retry(task)
        return result

    def _coordinate_task(self, task: Dict) -> AgentResult:
        subtasks = task.get("subtasks", [])
        results = []
        for subtask in subtasks:
            agent = self.find_agent(subtask)
            if agent:
                result = agent._execute_with_retry(subtask)
                results.append({"agent": agent.name, "result": result})
            else:
                results.append({"agent": None, "result": None, "error": "No agent found"})
        all_success = all(r["result"].success for r in results if r.get("result"))
        return AgentResult(
            success=all_success,
            output=results,
            errors=[],
        )

    def _get_system_status(self) -> AgentResult:
        statuses = [a.get_status() for a in self._registered_agents]
        return AgentResult(success=True, output=statuses)

    def get_agents(self) -> List[BaseAgent]:
        """Return list of registered agents."""
        return self._registered_agents.copy()
