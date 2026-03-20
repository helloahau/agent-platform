from __future__ import annotations

from core.agent.base import Agent
from core.agent.config import AgentConfig, load_agents_from_dir
from config.settings import get_settings


class AgentRunner:
    """High-level facade for loading and running agents."""

    def __init__(self) -> None:
        self._configs: dict[str, AgentConfig] = {}
        self._agents: dict[str, Agent] = {}

    def load_from_directory(self, directory: str | None = None) -> None:
        settings = get_settings()
        d = directory or settings.agents_dir
        self._configs.update(load_agents_from_dir(d))

    def register_config(self, config: AgentConfig) -> None:
        self._configs[config.name] = config

    def get_or_create_agent(
        self, name: str, session_id: str | None = None
    ) -> Agent:
        key = f"{name}:{session_id}" if session_id else name
        if key not in self._agents:
            if name not in self._configs:
                raise KeyError(
                    f"Agent '{name}' not configured. "
                    f"Available: {list(self._configs.keys())}"
                )
            self._agents[key] = Agent(self._configs[name], session_id=session_id)
        return self._agents[key]

    async def run(self, agent_name: str, message: str, session_id: str | None = None) -> str:
        agent = self.get_or_create_agent(agent_name, session_id)
        return await agent.run(message)

    def list_agents(self) -> list[AgentConfig]:
        return list(self._configs.values())
