"""BudgetAgent — wraps trader-budget/size.py."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.agents.base import BaseAgent


class BudgetAgent(BaseAgent):
    name = "budget"
    tier = "planning"

    def skill_path(self) -> Path:
        return settings.budget_skill

    async def run(self, plan: dict | None = None, **kwargs) -> dict | None:
        return await self.size(plan=plan or {})

    async def size(self, plan: dict) -> dict | None:
        """Turn plan into an exact whole-share bracket order inside budget limits."""
        args = ["--write", "--json"]
        result = await self._run_skill_wrapped(args)

        orders_file = self.cwd / "orders.json"
        if orders_file.exists():
            try:
                return json.loads(orders_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        try:
            return json.loads(result.stdout)
        except Exception:
            return None
