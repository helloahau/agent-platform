from __future__ import annotations

import json
import logging
from typing import Any

from core.agent.base import Agent
from core.agent.config import AgentConfig
from core.llm.registry import LLMRegistry

logger = logging.getLogger(__name__)


class RouterAgent:
    """Routes incoming messages to the most appropriate specialist agent.

    Uses an LLM call to decide which agent should handle the request,
    then delegates execution to that agent.
    """

    def __init__(
        self,
        agents: dict[str, Agent],
        router_model: str | None = None,
        provider: str | None = None,
    ):
        self._agents = agents
        self._provider = LLMRegistry.get(provider)
        self._router_model = router_model

    def _build_routing_prompt(self, user_message: str) -> list[dict[str, Any]]:
        agent_descriptions = "\n".join(
            f"- **{name}**: {a.config.description}"
            for name, a in self._agents.items()
        )
        return [
            {
                "role": "system",
                "content": (
                    "You are a routing agent. Given the user's message and the list of "
                    "available specialist agents below, decide which agent is best suited "
                    "to handle the request.\n\n"
                    f"Available agents:\n{agent_descriptions}\n\n"
                    'Respond with ONLY a JSON object: {"agent": "<agent_name>", "reason": "<brief reason>"}'
                ),
            },
            {"role": "user", "content": user_message},
        ]

    async def route(self, user_message: str) -> str:
        messages = self._build_routing_prompt(user_message)
        response = await self._provider.chat(
            messages=messages,
            model=self._router_model,
            temperature=0.0,
        )

        try:
            decision = json.loads(response.content)
            agent_name = decision["agent"]
        except (json.JSONDecodeError, KeyError):
            agent_name = list(self._agents.keys())[0]
            logger.warning(
                "Router could not parse decision '%s', falling back to '%s'.",
                response.content,
                agent_name,
            )

        if agent_name not in self._agents:
            agent_name = list(self._agents.keys())[0]
            logger.warning("Routed agent '%s' not found, falling back.", agent_name)

        logger.info("Router selected agent '%s' for message.", agent_name)
        return await self._agents[agent_name].run(user_message)


def build_router_from_configs(
    configs: dict[str, AgentConfig],
    router_model: str | None = None,
) -> RouterAgent:
    """Convenience builder: creates Agent instances from configs and wraps them in a RouterAgent."""
    agents = {name: Agent(cfg) for name, cfg in configs.items()}
    return RouterAgent(agents, router_model=router_model)
