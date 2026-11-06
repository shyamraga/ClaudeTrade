"""AlertsAgent — wraps trader-alerts/alerts.py."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.agents.base import BaseAgent


class AlertsAgent(BaseAgent):
    name = "alerts"
    tier = "execution"

    def skill_path(self) -> Path:
        return settings.alerts_skill

    async def run(self, action: str = "check", **kwargs) -> dict:
        if action == "add":
            return await self.add_from_plan()
        return await self.check()

    async def add_from_plan(self) -> dict:
        """Arm the stop, target, and flat-by alerts from trader/plan.json."""
        result = await self._run_skill_wrapped(["add", "--from-plan"])
        return {"raw": result.stdout}

    async def check(self) -> dict:
        """Check all active alerts against current quotes.

        Returns exit code 0 if an alert rang, 1 otherwise.
        """
        result = await self._run_skill_wrapped(["check"])
        return {
            "rang": result.returncode == 0,
            "stdout": result.stdout,
        }

    async def quote(self, symbol: str) -> dict:
        """Fetch latest quote and update trader/prices.json."""
        result = await self._run_skill_wrapped(["quote", symbol, "--write"])
        return {"raw": result.stdout}
