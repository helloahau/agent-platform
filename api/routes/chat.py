from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


def _get_runner():
    from api.main import agent_runner
    return agent_runner


@router.post("/{agent_name}", response_model=ChatResponse)
async def chat(agent_name: str, req: ChatRequest):
    runner = _get_runner()
    session_id = req.session_id or uuid4().hex

    try:
        response = await runner.run(agent_name, req.message, session_id=session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}")

    return ChatResponse(agent=agent_name, session_id=session_id, response=response)


@router.post("/{agent_name}/stream")
async def chat_stream(agent_name: str, req: ChatRequest):
    """SSE streaming endpoint — yields chunks as server-sent events."""
    runner = _get_runner()
    session_id = req.session_id or uuid4().hex

    try:
        agent = runner.get_or_create_agent(agent_name, session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    async def event_generator():
        try:
            async for chunk in agent.run_stream(req.message):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
