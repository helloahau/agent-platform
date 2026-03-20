from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentCreateRequest(BaseModel):
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


class AgentResponse(BaseModel):
    name: str
    description: str
    system_prompt: str
    model: Optional[str]
    provider: Optional[str]
    temperature: float
    tools: list[str]
    max_iterations: int
    memory_type: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    agent: str
    session_id: str
    response: str


class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]
