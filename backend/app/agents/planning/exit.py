"""ExitAgent — wraps trader-exit/exit.py."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.agents.base import BaseAgent


class ExitAgent(BaseAgent):
    name = "exit"
    tier = "planning"

    def skill_path(self) -> Path:
        return settings.exit_skill

    async def run(self, symbol: str = "TSLA", stop_rule: str = "or-mid", target_r: str = "2R", **kwargs) -> dict | None:
        return await self.plan_from_entry(symbol=symbol, stop_rule=stop_rule, target_r=target_r)

    async def plan_from_entry(
        self,
        symbol: str,
        stop_rule: str = "or-mid",
        target_r: str = "2R",
    ) -> dict | None:
        """Create exit plan (stop + target before entry) from entry.json."""
        args = ["plan", "--stop", stop_rule, "--target", target_r, "--write", "--json"]
        result = await self._run_skill_wrapped(args)

        plan_file = self.cwd / "plan.json"
        if plan_file.exists():
            try:
                return json.loads(plan_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        try:
            return json.loads(result.stdout)
        except Exception:
            return None
