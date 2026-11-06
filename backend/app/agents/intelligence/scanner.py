"""ScannerAgent — wraps trader-scanner/scan.py."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.agents.base import BaseAgent


class ScannerAgent(BaseAgent):
    name = "scanner"
    tier = "intelligence"

    def skill_path(self) -> Path:
        return settings.scanner_skill

    async def run(
        self,
        mode: str = "daily",
        symbols: list[str] | None = None,
        min_price: float = 5.0,
        limit: int | None = None,
    ) -> list[dict]:
        """Run daily or ORB scan and return parsed hits."""
        args = [mode]
        if symbols:
            args.extend(["--symbols", ",".join(symbols)])
        if min_price:
            args.extend(["--min-price", str(min_price)])
        if limit:
            args.extend(["--limit", str(limit)])
        args.append("--json")

        result = await self._run_skill_wrapped(args)

        # Parse hits from watchlist.json or stdout
        watchlist_file = self.cwd / "watchlist.json"
        if watchlist_file.exists():
            try:
                data = json.loads(watchlist_file.read_text(encoding="utf-8"))
                return data.get("hits", [])
            except Exception:
                pass

        try:
            data = json.loads(result.stdout)
            return data.get("hits", [])
        except Exception:
            return []
