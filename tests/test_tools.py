import asyncio
import pytest

from core.tools.builtin.calculator import CalculatorTool
from core.tools.builtin.file_reader import FileReaderTool
from core.tools.registry import ToolRegistry, setup_builtin_tools


@pytest.fixture(autouse=True)
def clean_registry():
    ToolRegistry.clear()
    yield
    ToolRegistry.clear()


def test_calculator_basic():
    calc = CalculatorTool()
    assert asyncio.get_event_loop().run_until_complete(calc.run(expression="2 + 3")) == "5.0"


def test_calculator_complex():
    calc = CalculatorTool()
    result = asyncio.get_event_loop().run_until_complete(calc.run(expression="2 ** 10"))
    assert result == "1024.0"


def test_calculator_error():
    calc = CalculatorTool()
    result = asyncio.get_event_loop().run_until_complete(calc.run(expression="import os"))
    assert "Error" in result


def test_file_reader_missing():
    reader = FileReaderTool()
    result = asyncio.get_event_loop().run_until_complete(
        reader.run(path="/nonexistent/file.txt")
    )
    assert "not found" in result


def test_file_reader_reads_self():
    reader = FileReaderTool()
    result = asyncio.get_event_loop().run_until_complete(
        reader.run(path=__file__)
    )
    assert "test_file_reader_reads_self" in result


def test_tool_openai_format():
    calc = CalculatorTool()
    schema = calc.to_openai_tool()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "calculator"
    assert "parameters" in schema["function"]


def test_registry_setup():
    setup_builtin_tools()
    tools = ToolRegistry.list_tools()
    names = {t.name for t in tools}
    assert "calculator" in names
    assert "web_search" in names
    assert "file_reader" in names


def test_registry_get():
    setup_builtin_tools()
    calc = ToolRegistry.get("calculator")
    assert calc.name == "calculator"


def test_registry_get_missing():
    with pytest.raises(KeyError):
        ToolRegistry.get("nonexistent_tool")
