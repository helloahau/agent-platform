from __future__ import annotations

import logging
from dataclasses import dataclass, field

from core.agent.base import Agent

logger = logging.getLogger(__name__)


@dataclass
class PipelineStep:
    agent: Agent
    transform_input: bool = True
    prefix: str = ""


class Pipeline:
    """Sequential multi-agent pipeline.

    Each agent receives the previous agent's output as its input.
    Optionally, a prefix can be prepended to contextualise the handoff.
    """

    def __init__(self, steps: list[PipelineStep] | None = None):
        self._steps: list[PipelineStep] = steps or []

    def add_step(self, agent: Agent, *, prefix: str = "") -> "Pipeline":
        self._steps.append(PipelineStep(agent=agent, prefix=prefix))
        return self

    async def run(self, initial_input: str) -> str:
        current = initial_input
        for i, step in enumerate(self._steps):
            agent_input = f"{step.prefix}\n\n{current}" if step.prefix else current
            logger.info(
                "Pipeline step %d/%d: agent '%s'",
                i + 1,
                len(self._steps),
                step.agent.config.name,
            )
            current = await step.agent.run(agent_input)
        return current


@dataclass
class PipelineResult:
    final_output: str
    intermediate_outputs: list[str] = field(default_factory=list)


class TracedPipeline(Pipeline):
    """Pipeline variant that records every intermediate output."""

    async def run(self, initial_input: str) -> str:
        current = initial_input
        self.trace: list[str] = []
        for i, step in enumerate(self._steps):
            agent_input = f"{step.prefix}\n\n{current}" if step.prefix else current
            logger.info(
                "TracedPipeline step %d/%d: agent '%s'",
                i + 1,
                len(self._steps),
                step.agent.config.name,
            )
            current = await step.agent.run(agent_input)
            self.trace.append(current)
        return current

    def get_result(self, initial_input: str = "") -> PipelineResult:
        return PipelineResult(
            final_output=self.trace[-1] if self.trace else "",
            intermediate_outputs=self.trace,
        )
