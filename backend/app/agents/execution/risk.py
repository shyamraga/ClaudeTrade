"""RiskAgent — wraps trader-risk/check.py (hard gate)."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.agents.base import BaseAgent
from app.core.events import AgentStatus


class RiskAgent(BaseAgent):
    name = "risk"
    tier = "execution"

    def skill_path(self) -> Path:
        return settings.risk_skill

    async def run(self, **kwargs) -> dict:
        return await self.check()

    async def check(self) -> dict:
        """Run all risk checks against trader/orders.json.

        Returns:
            {"passed": True} if all orders passed,
            {"passed": False, "reason": "..."} if blocked.
        """
        args = ["--json"]
        result = await self._run_skill_wrapped(args)

        passed = (result.returncode == 0)

        # Read verdict from trader/state/risk.json if it exists
        risk_file = self.cwd / "state" / "risk.json"
        details = {}
        if risk_file.exists():
            try:
                details = json.loads(risk_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        if not passed:
            await self.emit(
                AgentStatus.BLOCKED,
                f"Risk check BLOCKED order: {result.stdout.strip()}",
                payload=details,
            )

        return {
            "passed": passed,
            "stdout": result.stdout,
            "details": details,
            "reason": "" if passed else result.stdout.strip(),
        }
