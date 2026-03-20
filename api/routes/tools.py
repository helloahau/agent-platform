from __future__ import annotations

from fastapi import APIRouter

from api.schemas import ToolInfo
from core.tools.registry import ToolRegistry

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("/", response_model=list[ToolInfo])
async def list_tools():
    return [
        ToolInfo(
            name=t.name,
            description=t.description,
            parameters=t.parameters_schema,
        )
        for t in ToolRegistry.list_tools()
    ]
