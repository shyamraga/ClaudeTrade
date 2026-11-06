"""
Base class for all Claude Trade agents.

Every agent:
1. Wraps one underlying trading skill CLI tool
2. Publishes lifecycle events (START, UPDATE, DONE, ERROR, BLOCKED) to the EventBus
3. Reads/writes state files in trader/
4. Exposes a typed async run() method that returns structured data
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.events import AgentStatus, PipelineEvent, bus
from app.core.skill_runner import SkillResult, run_skill

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all trading agents."""

    name: str = "base"
    tier: str = "intelligence"  # "intelligence" | "planning" | "execution"

    def __init__(self, cwd: Path | None = None) -> None:
        self.cwd = cwd or settings.trader_dir

    @abstractmethod
    def skill_path(self) -> Path:
        """Return the path to the underlying skill .py file."""
        ...

    async def emit(self, status: AgentStatus, message: str = "", payload: dict | None = None) -> None:
        """Publish an agent update event to the bus."""
        event = PipelineEvent(
            tier=self.tier,
            agent=self.name,
            status=status,
            message=message,
            payload=payload or {},
        )
        await bus.publish(event)
        logger.debug(f"[{self.name}] {status}: {message}")

    async def _run_skill_wrapped(
        self,
        args: list[str],
        env_extra: dict[str, str] | None = None,
        timeout: float = 300.0,
    ) -> SkillResult:
        """Run the skill, streaming stdout lines as agent updates."""
        await self.emit(AgentStatus.RUNNING, f"Starting with args: {' '.join(args)}")

        async def on_line(line: str) -> None:
            await self.emit(AgentStatus.RUNNING, line)

        result = await run_skill(
            skill_path=self.skill_path(),
            args=args,
            cwd=self.cwd,
            env_extra=env_extra,
            timeout=timeout,
            line_callback=on_line,
        )

        if result.returncode == 0:
            await self.emit(AgentStatus.DONE, "Completed successfully")
        else:
            await self.emit(AgentStatus.ERROR, f"Exited with code {result.returncode}")

        return result

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Main agent logic — subclasses define typed arguments and return type."""
        ...
