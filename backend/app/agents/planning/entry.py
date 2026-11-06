"""EntryAgent — wraps trader-entry/entry.py."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.agents.base import BaseAgent


class EntryAgent(BaseAgent):
    name = "entry"
    tier = "planning"

    def skill_path(self) -> Path:
        return settings.entry_skill

    async def run(self, symbol: str = "TSLA", setup: str = "orb", level: float | None = None, **kwargs) -> dict:
        return await self.check(symbol=symbol, setup=setup, level=level)

    async def check(
        self,
        symbol: str,
        setup: str = "orb",
        level: float | None = None,
        write: bool = True,
    ) -> dict:
        """Check if entry condition has triggered on the latest closed bar."""
        args = ["check", symbol, "--setup", setup]
        if level:
            args.extend(["--level", str(level)])
        if write:
            args.append("--write")
        args.append("--json")

        result = await self._run_skill_wrapped(args)

        entry_file = self.cwd / "entry.json"
        if entry_file.exists():
            try:
                return json.loads(entry_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        try:
            return json.loads(result.stdout)
        except Exception:
            return {"triggered": False, "raw": result.stdout}
