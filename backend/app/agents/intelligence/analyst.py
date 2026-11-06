"""AnalystAgent — wraps trader-analyst/facts.py."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.agents.base import BaseAgent


class AnalystAgent(BaseAgent):
    name = "analyst"
    tier = "intelligence"

    def skill_path(self) -> Path:
        return settings.analyst_skill

    async def run(
        self,
        tickers: list[str],
        quarters: int = 4,
    ) -> dict[str, Any]:
        """Fetch SEC XBRL financial facts and earnings Q/Q metrics."""
        if not settings.sec_user_agent:
            return {"error": "SEC_USER_AGENT is not configured"}

        args = [*tickers, "--quarters", str(quarters), "--json"]
        env_extra = {"SEC_USER_AGENT": settings.sec_user_agent}

        result = await self._run_skill_wrapped(args, env_extra=env_extra)

        try:
            return json.loads(result.stdout)
        except Exception:
            return {"raw": result.stdout}
