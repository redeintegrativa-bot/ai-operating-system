from .base_agent import BaseAgent, AgentResult, AgentStatus
from .orchestrator.orchestrator import OrchestratorAgent
from .architect.architect import ArchitectAgent
from .engineer.engineer import EngineerAgent
from .researcher.researcher import ResearcherAgent
from .ai_specialist.ai_specialist import AISpecialistAgent
from .automation_specialist.automation_specialist import AutomationAgent
from .database_specialist.database_specialist import DatabaseAgent
from .security_specialist.security_specialist import SecurityAgent

__all__ = [
    "BaseAgent",
    "AgentResult",
    "AgentStatus",
    "OrchestratorAgent",
    "ArchitectAgent",
    "EngineerAgent",
    "ResearcherAgent",
    "AISpecialistAgent",
    "AutomationAgent",
    "DatabaseAgent",
    "SecurityAgent",
]

AGENT_REGISTRY = {
    "orchestrator": OrchestratorAgent,
    "architect": ArchitectAgent,
    "engineer": EngineerAgent,
    "researcher": ResearcherAgent,
    "ai_specialist": AISpecialistAgent,
    "automation": AutomationAgent,
    "database": DatabaseAgent,
    "security": SecurityAgent,
}


def create_agent(agent_type: str, project_root: str) -> BaseAgent:
    """Factory function to create agents by type."""
    agent_class = AGENT_REGISTRY.get(agent_type)
    if agent_class is None:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(AGENT_REGISTRY.keys())}")
    return agent_class(project_root)


def create_all_agents(project_root: str) -> dict:
    """Create all agents and return them as a dict."""
    return {
        name: cls(project_root)
        for name, cls in AGENT_REGISTRY.items()
    }
