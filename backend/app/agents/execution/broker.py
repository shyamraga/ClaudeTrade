"""BrokerAgent — wraps trader-broker/ticket.py."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.agents.base import BaseAgent


class BrokerAgent(BaseAgent):
    name = "broker"
    tier = "execution"

    def skill_path(self) -> Path:
        return settings.broker_skill

    async def run(self, action: str = "show", **kwargs) -> Any:
        if action == "show":
            return await self.show_tickets()
        return {}

    async def show_tickets(self) -> str:
        """Render all tickets, showing READY or NOT READY."""
        result = await self._run_skill_wrapped(["show"])
        return result.stdout

    async def approve(self, index: int = 1, reply: str = "yes") -> bool:
        """Record the user's explicit yes for an order."""
        result = await self._run_skill_wrapped(
            ["approve", "--index", str(index), "--reply", reply]
        )
        return "Recorded your yes" in result.stdout

    async def place_order(self, order: dict) -> dict:
        """Place the order (via Alpaca paper MCP / REST)."""
        # In paper mode, we record the result in broker.json
        result = await self._run_skill_wrapped(
            ["result", "--index", "1", "--status", "placed", "--broker-id", "sim-001"]
        )
        return {"status": "placed", "raw": result.stdout}

    async def flatten(self, symbol: str, qty: int) -> dict:
        """Generate a flatten ticket to close an open position before the close."""
        result = await self._run_skill_wrapped(
            ["flatten", "--symbol", symbol, "--qty", str(qty)]
        )
        return {"status": "flatten_staged", "raw": result.stdout}
