"""PelosiAgent — wraps trader-pelosi/ptr.py."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.agents.base import BaseAgent


class PelosiAgent(BaseAgent):
    name = "pelosi"
    tier = "intelligence"

    def skill_path(self) -> Path:
        return settings.pelosi_skill

    async def run(
        self,
        member: str = "pelosi",
        days: int = 45,
    ) -> list[dict]:
        """Check for new Periodic Transaction Reports (disclosures)."""
        args = ["new", "--member", member, "--json"]
        result = await self._run_skill_wrapped(args)

        try:
            data = json.loads(result.stdout)
            return data if isinstance(data, list) else data.get("reports", [])
        except Exception:
            return []
