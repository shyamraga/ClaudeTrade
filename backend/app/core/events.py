"""
Internal event bus for broadcasting pipeline state to WebSocket clients.
Agents publish events here; the WebSocket router subscribes and fans them
out to all connected browser sessions.

Usage:
    # Publisher (in an agent):
    from app.core.events import bus
    await bus.publish(PipelineEvent(tier="intelligence", agent="scanner", ...))

    # Subscriber (in the WS router):
    async for event in bus.subscribe():
        await ws.send_json(event.model_dump())
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import AsyncGenerator

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    BLOCKED = "blocked"   # trader-risk BLOCK


class PipelineEvent(BaseModel):
    event_type: str = "agent_update"
    tier: str                          # "intelligence" | "planning" | "execution"
    agent: str                         # e.g. "scanner", "risk"
    status: AgentStatus
    message: str = ""
    payload: dict = Field(default_factory=dict)
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    """Simple in-process pub/sub — one queue per subscriber."""

    def __init__(self) -> None:
        self._queues: list[asyncio.Queue[PipelineEvent]] = []

    async def publish(self, event: PipelineEvent) -> None:
        for q in self._queues:
            await q.put(event)

    async def subscribe(self) -> AsyncGenerator[PipelineEvent, None]:
        q: asyncio.Queue[PipelineEvent] = asyncio.Queue()
        self._queues.append(q)
        try:
            while True:
                event = await q.get()
                yield event
        finally:
            self._queues.remove(q)


# Module-level singleton
bus = EventBus()
