from __future__ import annotations

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    azure_open_ai_key: str = ""
    azure_open_ai_endpoint: str = ""
    azure_open_ai_api_version: str = "2024-02-01"
    default_model: str = "gpt-5.1-codex-mini-2025-11-13"

    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "agent-platform"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    github_token: str = ""

    db_path: str = str(PROJECT_ROOT / "data" / "agent_platform.db")
    agents_dir: str = str(PROJECT_ROOT / "agents")

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    max_agent_iterations: int = 10
    default_temperature: float = 0.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
