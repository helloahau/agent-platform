import asyncio
import pytest

from core.agent.config import AgentConfig
from core.agent.base import Agent
from core.llm.base import BaseLLMProvider, LLMResponse
from core.llm.registry import LLMRegistry
from core.tools.registry import ToolRegistry, setup_builtin_tools
from core.memory.conversation import ConversationMemory


class FakeLLM(BaseLLMProvider):
    """Returns a canned response, no tool calls."""

    def __init__(self, response: str = "Hello from fake LLM!"):
        self._response = response

    @property
    def provider_name(self) -> str:
        return "fake"

    async def chat(self, messages, tools=None, temperature=0.0, model=None, **kwargs):
        return LLMResponse(content=self._response, tool_calls=[], raw=None, usage={})

    async def chat_stream(self, messages, tools=None, temperature=0.0, model=None, **kwargs):
        yield self._response


@pytest.fixture(autouse=True)
def clean_registries():
    LLMRegistry.clear()
    ToolRegistry.clear()
    setup_builtin_tools()
    LLMRegistry.register(FakeLLM(), default=True)
    yield
    LLMRegistry.clear()
    ToolRegistry.clear()


def test_agent_config_from_dict():
    cfg = AgentConfig(name="test", description="A test agent")
    assert cfg.name == "test"
    assert cfg.temperature == 0.0
    assert cfg.tools == []


def test_agent_config_yaml_roundtrip(tmp_path):
    cfg = AgentConfig(
        name="roundtrip",
        description="test roundtrip",
        tools=["calculator"],
    )
    path = tmp_path / "agent.yaml"
    cfg.to_yaml(path)
    loaded = AgentConfig.from_yaml(path)
    assert loaded.name == "roundtrip"
    assert loaded.tools == ["calculator"]


@pytest.mark.asyncio
async def test_agent_run_no_tools():
    cfg = AgentConfig(name="simple", description="no tools")
    agent = Agent(cfg)
    result = await agent.run("Hello")
    assert result == "Hello from fake LLM!"


@pytest.mark.asyncio
async def test_agent_memory():
    cfg = AgentConfig(name="mem_test", description="memory test")
    memory = ConversationMemory()
    agent = Agent(cfg, memory=memory)
    await agent.run("First message")
    msgs = await memory.get_messages()
    roles = [m["role"] for m in msgs]
    assert "user" in roles
    assert "assistant" in roles


@pytest.mark.asyncio
async def test_agent_stream():
    cfg = AgentConfig(name="stream_test", description="stream test")
    agent = Agent(cfg)
    chunks = []
    async for chunk in agent.run_stream("Hello"):
        chunks.append(chunk)
    assert len(chunks) >= 1
