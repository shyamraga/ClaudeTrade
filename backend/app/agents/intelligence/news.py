"""NewsAgent — wraps trader-news/news.py."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.agents.base import BaseAgent


class NewsAgent(BaseAgent):
    name = "news"
    tier = "intelligence"

    def skill_path(self) -> Path:
        return settings.news_skill

    async def run(
        self,
        tickers: list[str] | None = None,
        hours: int = 24,
        no_sec: bool = False,
    ) -> dict:
        """Fetch headlines and 8-K filings for given tickers."""
        args: list[str] = []
        if tickers:
            args.extend(["--tickers", *tickers])
        if hours:
            args.extend(["--hours", str(hours)])
        if no_sec or not settings.sec_user_agent:
            args.append("--no-sec")
        args.append("--json")

        env_extra = {}
        if settings.sec_user_agent:
            env_extra["SEC_USER_AGENT"] = settings.sec_user_agent

        result = await self._run_skill_wrapped(args, env_extra=env_extra)

        try:
            return json.loads(result.stdout)
        except Exception:
            return {"raw": result.stdout}
