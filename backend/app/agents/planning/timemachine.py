"""TimeMachineAgent — wraps trader-timemachine/timemachine.py."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.agents.base import BaseAgent


class TimeMachineAgent(BaseAgent):
    name = "timemachine"
    tier = "planning"

    def skill_path(self) -> Path:
        return settings.timemachine_skill

    async def run(
        self,
        symbol: str,
        plan: dict,
        replays: int = 10000,
        seed: int = 19,
    ) -> dict | None:
        """Run 10,000 Monte Carlo replays against the last 60 days of 5m bars."""
        args = [
            "run",
            "--symbol", symbol,
            "--replays", str(replays),
            "--seed", str(seed),
            "--write",
            "--json",
        ]
        result = await self._run_skill_wrapped(args)

        tm_file = self.cwd / "timemachine.json"
        if tm_file.exists():
            try:
                return json.loads(tm_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        try:
            return json.loads(result.stdout)
        except Exception:
            return None
