import pytest

from core.llm.registry import LLMRegistry
from core.llm.base import BaseLLMProvider, LLMResponse


class MockProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "mock"

    async def chat(self, messages, tools=None, temperature=0.0, model=None, **kwargs):
        return LLMResponse(content="mock response", tool_calls=[], raw=None, usage={})

    async def chat_stream(self, messages, tools=None, temperature=0.0, model=None, **kwargs):
        yield "mock "
        yield "stream"


@pytest.fixture(autouse=True)
def clean_registry():
    LLMRegistry.clear()
    yield
    LLMRegistry.clear()


def test_register_and_get():
    provider = MockProvider()
    LLMRegistry.register(provider, default=True)
    assert LLMRegistry.get("mock") is provider
    assert LLMRegistry.get() is provider


def test_list_providers():
    LLMRegistry.register(MockProvider())
    assert "mock" in LLMRegistry.list_providers()


def test_get_missing():
    with pytest.raises(KeyError):
        LLMRegistry.get("nonexistent")


@pytest.mark.asyncio
async def test_mock_chat():
    provider = MockProvider()
    resp = await provider.chat(messages=[{"role": "user", "content": "hi"}])
    assert resp.content == "mock response"
    assert resp.tool_calls == []


@pytest.mark.asyncio
async def test_mock_stream():
    provider = MockProvider()
    chunks = []
    async for chunk in provider.chat_stream(messages=[{"role": "user", "content": "hi"}]):
        chunks.append(chunk)
    assert chunks == ["mock ", "stream"]
