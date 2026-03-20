from __future__ import annotations

from pathlib import Path
from typing import Any

from core.tools.base import BaseTool


class FileReaderTool(BaseTool):
    @property
    def name(self) -> str:
        return "file_reader"

    @property
    def description(self) -> str:
        return "Read the contents of a local file. Returns the text content."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file to read.",
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to return (default: 200).",
                },
            },
            "required": ["path"],
        }

    async def run(self, **kwargs: Any) -> str:
        file_path = kwargs.get("path", "")
        max_lines = kwargs.get("max_lines", 200)

        if not file_path:
            return "Error: no file path provided."

        p = Path(file_path)
        if not p.exists():
            return f"Error: file '{file_path}' not found."
        if not p.is_file():
            return f"Error: '{file_path}' is not a file."

        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                lines.append(f"\n... truncated at {max_lines} lines ...")
            return "\n".join(lines)
        except Exception as exc:
            return f"Error reading file: {exc}"
