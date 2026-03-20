from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import AgentCreateRequest, AgentResponse
from core.agent.config import AgentConfig

router = APIRouter(prefix="/agents", tags=["agents"])


def _get_runner():
    from api.main import agent_runner
    return agent_runner


@router.get("/", response_model=list[AgentResponse])
async def list_agents():
    configs = _get_runner().list_agents()
    return [
        AgentResponse(
            name=c.name,
            description=c.description,
            system_prompt=c.system_prompt,
            model=c.model,
            provider=c.provider,
            temperature=c.temperature,
            tools=c.tools,
            max_iterations=c.max_iterations,
            memory_type=c.memory_type,
        )
        for c in configs
    ]


@router.get("/{name}", response_model=AgentResponse)
async def get_agent(name: str):
    configs = {c.name: c for c in _get_runner().list_agents()}
    if name not in configs:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")
    c = configs[name]
    return AgentResponse(
        name=c.name,
        description=c.description,
        system_prompt=c.system_prompt,
        model=c.model,
        provider=c.provider,
        temperature=c.temperature,
        tools=c.tools,
        max_iterations=c.max_iterations,
        memory_type=c.memory_type,
    )


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(req: AgentCreateRequest):
    config = AgentConfig(**req.model_dump())
    _get_runner().register_config(config)

    config.to_yaml(f"agents/{config.name}.yaml")

    return AgentResponse(
        name=config.name,
        description=config.description,
        system_prompt=config.system_prompt,
        model=config.model,
        provider=config.provider,
        temperature=config.temperature,
        tools=config.tools,
        max_iterations=config.max_iterations,
        memory_type=config.memory_type,
    )


@router.delete("/{name}", status_code=204)
async def delete_agent(name: str):
    runner = _get_runner()
    configs = {c.name: c for c in runner.list_agents()}
    if name not in configs:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")

    runner._configs.pop(name, None)
    keys_to_remove = [k for k in runner._agents if k.startswith(f"{name}:") or k == name]
    for k in keys_to_remove:
        del runner._agents[k]

    from pathlib import Path
    yaml_path = Path("agents") / f"{name}.yaml"
    if yaml_path.exists():
        yaml_path.unlink()
