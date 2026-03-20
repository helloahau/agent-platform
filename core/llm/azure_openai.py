from __future__ import annotations

import json
from typing import Any, AsyncIterator

from openai import AsyncAzureOpenAI

from config.settings import get_settings
from core.llm.base import BaseLLMProvider, LLMResponse


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI chat-completion provider."""

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        api_version: str | None = None,
        default_model: str | None = None,
    ):
        settings = get_settings()
        self._default_model = default_model or settings.default_model
        self._client = AsyncAzureOpenAI(
            api_key=api_key or settings.azure_open_ai_key,
            azure_endpoint=endpoint or settings.azure_open_ai_endpoint,
            api_version=api_version or settings.azure_open_ai_api_version,
        )

    @property
    def provider_name(self) -> str:
        return "azure_openai"

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        model: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        params: dict[str, Any] = {
            "model": model or self._default_model,
            "messages": messages,
            "temperature": temperature,
            **kwargs,
        }
        if tools:
            params["tools"] = tools
            params["tool_choice"] = kwargs.pop("tool_choice", "auto")

        response = await self._client.chat.completions.create(**params)
        choice = response.choices[0]
        message = choice.message

        tool_calls_out: list[dict[str, Any]] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls_out.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                })

        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls_out,
            raw=response,
            usage=usage,
        )

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        model: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        params: dict[str, Any] = {
            "model": model or self._default_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            **kwargs,
        }
        if tools:
            params["tools"] = tools
            params["tool_choice"] = kwargs.pop("tool_choice", "auto")

        stream = await self._client.chat.completions.create(**params)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
