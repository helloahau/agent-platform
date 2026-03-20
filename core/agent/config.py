from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Declarative agent configuration — loadable from YAML or API."""

    name: str
    description: str = ""
    system_prompt: str = "You are a helpful AI assistant."
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: float = 0.0
    tools: list[str] = Field(default_factory=list)
    max_iterations: int = 10
    memory_type: str = "conversation"
    memory_max_messages: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AgentConfig":
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str | Path) -> None:
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)


def load_agents_from_dir(directory: str | Path) -> dict[str, AgentConfig]:
    """Load all .yaml agent configs from a directory."""
    agents: dict[str, AgentConfig] = {}
    d = Path(directory)
    if not d.is_dir():
        return agents
    for fp in sorted(d.glob("*.yaml")):
        cfg = AgentConfig.from_yaml(fp)
        agents[cfg.name] = cfg
    return agents
