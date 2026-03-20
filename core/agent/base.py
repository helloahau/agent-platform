from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator
from uuid import uuid4

from core.agent.config import AgentConfig
from core.llm.base import BaseLLMProvider, LLMResponse
from core.llm.registry import LLMRegistry
from core.memory.base import BaseMemory
from core.memory.conversation import ConversationMemory
from core.memory.persistent import PersistentMemory
from core.tools.base import BaseTool
from core.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class Agent:
    """Core agent implementing a ReAct (Reasoning + Acting) loop."""

    def __init__(
        self,
        config: AgentConfig,
        provider: BaseLLMProvider | None = None,
        memory: BaseMemory | None = None,
        session_id: str | None = None,
    ):
        self.config = config
        self.session_id = session_id or uuid4().hex
        self._provider = provider or LLMRegistry.get(config.provider)
        self._memory = memory or self._build_memory()
        self._tools = self._resolve_tools()

    def _build_memory(self) -> BaseMemory:
        if self.config.memory_type == "persistent":
            return PersistentMemory(session_id=self.session_id)
        return ConversationMemory(max_messages=self.config.memory_max_messages)

    def _resolve_tools(self) -> dict[str, BaseTool]:
        tools: dict[str, BaseTool] = {}
        for name in self.config.tools:
            try:
                tools[name] = ToolRegistry.get(name)
            except KeyError:
                logger.warning("Tool '%s' not found in registry, skipping.", name)
        return tools

    def _openai_tools(self) -> list[dict[str, Any]] | None:
        if not self._tools:
            return None
        return [t.to_openai_tool() for t in self._tools.values()]

    async def run(self, user_message: str) -> str:
        """Execute the full ReAct loop and return the final assistant response."""
        await self._memory.add_message("user", user_message)

        messages = [{"role": "system", "content": self.config.system_prompt}]
        messages.extend(await self._memory.get_messages())

        for iteration in range(self.config.max_iterations):
            logger.debug("Agent '%s' iteration %d", self.config.name, iteration + 1)

            response: LLMResponse = await self._provider.chat(
                messages=messages,
                tools=self._openai_tools(),
                temperature=self.config.temperature,
                model=self.config.model,
            )

            if not response.tool_calls:
                await self._memory.add_message("assistant", response.content)
                return response.content

            assistant_msg: dict[str, Any] = {"role": "assistant", "content": response.content or ""}
            if response.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                    for tc in response.tool_calls
                ]
            messages.append(assistant_msg)

            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["arguments"]
                logger.info("Calling tool '%s' with %s", tool_name, tool_args)

                tool = self._tools.get(tool_name)
                if tool is None:
                    result = f"Error: tool '{tool_name}' is not available."
                else:
                    try:
                        result = await tool.run(**tool_args)
                    except Exception as exc:
                        result = f"Error executing tool '{tool_name}': {exc}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

        final = await self._provider.chat(
            messages=messages,
            temperature=self.config.temperature,
            model=self.config.model,
        )
        await self._memory.add_message("assistant", final.content)
        return final.content

    async def run_stream(self, user_message: str) -> AsyncIterator[str]:
        """Streaming variant — yields text chunks. Falls back to non-streaming for tool calls."""
        result = await self.run(user_message)
        yield result
