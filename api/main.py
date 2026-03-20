from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.agent.runner import AgentRunner
from core.llm.registry import setup_default_providers
from core.logging_config import setup_logging
from core.tools.registry import setup_builtin_tools

logger = logging.getLogger(__name__)

agent_runner = AgentRunner()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting Agent Platform...")
    setup_default_providers()
    setup_builtin_tools()
    agent_runner.load_from_directory()
    logger.info(
        "Loaded %d agent(s): %s",
        len(agent_runner.list_agents()),
        [a.name for a in agent_runner.list_agents()],
    )
    yield
    logger.info("Shutting down Agent Platform.")


app = FastAPI(
    title="Agent Platform",
    description="Create, configure, and run AI agents through a simple API.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check logs for details."},
    )


from api.routes import agents, chat, tools  # noqa: E402

app.include_router(agents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(tools.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
