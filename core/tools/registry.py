from __future__ import annotations

from core.tools.base import BaseTool


class ToolRegistry:
    """Global registry of available tools."""

    _tools: dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool: BaseTool) -> None:
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> BaseTool:
        if name not in cls._tools:
            raise KeyError(
                f"Tool '{name}' not found. Available: {list(cls._tools.keys())}"
            )
        return cls._tools[name]

    @classmethod
    def list_tools(cls) -> list[BaseTool]:
        return list(cls._tools.values())

    @classmethod
    def get_openai_tools(cls, names: list[str] | None = None) -> list[dict]:
        """Return OpenAI-format tool definitions, optionally filtered by name."""
        tools = cls._tools.values() if names is None else [cls._tools[n] for n in names if n in cls._tools]
        return [t.to_openai_tool() for t in tools]

    @classmethod
    def clear(cls) -> None:
        cls._tools.clear()


def setup_builtin_tools() -> None:
    from core.tools.builtin.calculator import CalculatorTool
    from core.tools.builtin.web_search import WebSearchTool
    from core.tools.builtin.file_reader import FileReaderTool
    from core.tools.builtin.github import GitHubTool

    for tool_cls in (CalculatorTool, WebSearchTool, FileReaderTool, GitHubTool):
        ToolRegistry.register(tool_cls())
