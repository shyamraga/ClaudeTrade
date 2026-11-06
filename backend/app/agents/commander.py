"""
Commander — the top-level orchestrator agent.

Sits above all three tiers and drives the full end-to-end flow:

    1. Trigger Tier ① (Intelligence) — runs scanner, news, analyst, pelosi in parallel
    2. Once a setup is picked → Trigger Tier ② (Execution Planning) in sequence
       entry → exit → timemachine → budget
    3. Hand off to Tier ③ (Execution) — risk check (gate) → broker (requires 2 confirms)
    4. Start Tier ③ monitoring — alerts watch stop/target/flat-by

Can run in:
- "auto" mode (paper only, runs full pipeline without stopping)
- "semi-auto" mode (stops at broker for user yes)
- "signal" mode (stops after planning, emits signal to UI)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.events import AgentStatus, PipelineEvent, bus
from app.agents.intelligence.scanner import ScannerAgent
from app.agents.intelligence.news import NewsAgent
from app.agents.intelligence.analyst import AnalystAgent
from app.agents.intelligence.pelosi import PelosiAgent
from app.agents.planning.entry import EntryAgent
from app.agents.planning.exit import ExitAgent
from app.agents.planning.timemachine import TimeMachineAgent
from app.agents.planning.budget import BudgetAgent
from app.agents.execution.risk import RiskAgent
from app.agents.execution.broker import BrokerAgent
from app.agents.execution.alerts import AlertsAgent

logger = logging.getLogger(__name__)


class RunMode(str, Enum):
    SIGNAL_ONLY = "signal"       # scan → plan, emit signal to UI
    SEMI_AUTO = "semi-auto"      # scan → plan → risk, wait for user yes before broker
    AUTO = "auto"                # paper only: full pipeline automated


@dataclass
class PipelineResult:
    watchlist: list[dict] = field(default_factory=list)
    enriched_context: dict[str, Any] = field(default_factory=dict)
    entry_signal: dict | None = None
    plan: dict | None = None
    simulation: dict | None = None
    order: dict | None = None
    risk_passed: bool = False
    broker_result: dict | None = None


class CommanderAgent:
    """The central orchestrator that coordinates all 11 trading agents."""

    name = "commander"

    def __init__(self, cwd: Path | None = None) -> None:
        self.cwd = cwd or settings.trader_dir
        # Intelligence tier
        self.scanner = ScannerAgent(self.cwd)
        self.news = NewsAgent(self.cwd)
        self.analyst = AnalystAgent(self.cwd)
        self.pelosi = PelosiAgent(self.cwd)
        # Planning tier
        self.entry = EntryAgent(self.cwd)
        self.exit = ExitAgent(self.cwd)
        self.timemachine = TimeMachineAgent(self.cwd)
        self.budget = BudgetAgent(self.cwd)
        # Execution tier
        self.risk = RiskAgent(self.cwd)
        self.broker = BrokerAgent(self.cwd)
        self.alerts = AlertsAgent(self.cwd)

    async def emit(self, status: AgentStatus, message: str = "", payload: dict | None = None) -> None:
        await bus.publish(
            PipelineEvent(
                tier="orchestration",
                agent=self.name,
                status=status,
                message=message,
                payload=payload or {},
            )
        )

    # ── Tier ① : Intelligence (Parallel Fan-Out) ─────────────────────────────

    async def run_intelligence(
        self,
        mode: str = "daily",
        symbols: list[str] | None = None,
    ) -> tuple[list[dict], dict[str, Any]]:
        """Fan out intelligence agents: scanner first, then enrich hits in parallel."""
        await self.emit(AgentStatus.RUNNING, "Starting Intelligence Tier...")

        # 1. Run scanner to get watchlist hits
        scan_hits = await self.scanner.run(mode=mode, symbols=symbols)
        if not scan_hits:
            await self.emit(AgentStatus.DONE, "Scanner found no hits today")
            return [], {}

        tickers = [h["symbol"] for h in scan_hits[:10]]  # enrich top 10
        await self.emit(AgentStatus.RUNNING, f"Enriching top {len(tickers)} tickers in parallel: {', '.join(tickers)}")

        # 2. Fan out news, analyst, pelosi concurrently
        news_task = self.news.run(tickers=tickers)
        analyst_task = self.analyst.run(tickers=tickers[:5])  # top 5 for SEC XBRL
        pelosi_task = self.pelosi.run()

        news_res, analyst_res, pelosi_res = await asyncio.gather(
            news_task, analyst_task, pelosi_task, return_exceptions=True
        )

        enriched = {
            "news": news_res if not isinstance(news_res, Exception) else {},
            "analyst": analyst_res if not isinstance(analyst_res, Exception) else {},
            "pelosi": pelosi_res if not isinstance(pelosi_res, Exception) else {},
        }

        await self.emit(AgentStatus.DONE, f"Intelligence Tier complete: {len(scan_hits)} candidates ready")
        return scan_hits, enriched

    # ── Tier ② : Execution Planning (Sequential Pipeline) ────────────────────

    async def run_planning(
        self,
        symbol: str,
        setup: str = "orb",
        level: float | None = None,
    ) -> tuple[dict | None, dict | None, dict | None, dict | None]:
        """Run the planning sequence: entry → exit → timemachine → budget."""
        await self.emit(AgentStatus.RUNNING, f"Starting Planning Tier for {symbol}...")

        # 1. Entry check
        entry_result = await self.entry.check(symbol=symbol, setup=setup, level=level)
        if not entry_result.get("triggered"):
            await self.emit(AgentStatus.DONE, f"{symbol}: Entry not triggered (waiting or expired)")
            return entry_result, None, None, None

        # 2. Exit plan (stop + target before entry)
        exit_plan = await self.exit.plan_from_entry(symbol=symbol)
        if not exit_plan:
            await self.emit(AgentStatus.ERROR, f"{symbol}: Exit planner failed to create valid plan")
            return entry_result, None, None, None

        # 3. TimeMachine simulation (10,000 replays)
        sim_result = await self.timemachine.run(symbol=symbol, plan=exit_plan)

        # 4. Budget sizing (plan → exact share qty)
        order = await self.budget.size(plan=exit_plan)

        await self.emit(AgentStatus.DONE, f"Planning Tier complete for {symbol}")
        return entry_result, exit_plan, sim_result, order

    # ── Tier ③ : Execution (Risk Gate + Broker) ──────────────────────────────

    async def run_execution(
        self,
        order: dict,
        user_confirmed: bool = False,
    ) -> tuple[bool, dict | None]:
        """Run the execution tier: risk gate first, broker requires user confirm."""
        await self.emit(AgentStatus.RUNNING, "Starting Execution Tier: running risk checks...")

        # 1. Risk check (hard gate — BLOCK is final)
        risk_verdict = await self.risk.check()
        if not risk_verdict.get("passed"):
            await self.emit(AgentStatus.BLOCKED, f"Risk check failed: {risk_verdict.get('reason')}")
            return False, None

        await self.emit(AgentStatus.DONE, "Risk check PASSED — order is READY")

        # 2. Broker requires explicit user confirmation
        if not user_confirmed:
            await self.emit(AgentStatus.RUNNING, "Waiting for user confirmation to place order...")
            return True, None  # Ready, but paused waiting for confirmation

        broker_res = await self.broker.place_order(order)
        # 3. Arm post-entry alerts
        await self.alerts.add_from_plan()

        return True, broker_res

    # ── Full End-to-End Run ──────────────────────────────────────────────────

    async def run_pipeline(
        self,
        mode: RunMode = RunMode.SEMI_AUTO,
        symbol_override: str | None = None,
    ) -> PipelineResult:
        """Run the complete pipeline from intelligence through execution."""
        result = PipelineResult()

        # Step 1: Intelligence
        scan_hits, enriched = await self.run_intelligence()
        result.watchlist = scan_hits
        result.enriched_context = enriched

        if not scan_hits and not symbol_override:
            return result

        target_symbol = symbol_override or scan_hits[0]["symbol"]

        # Step 2: Planning
        entry_sig, plan, sim, order = await self.run_planning(symbol=target_symbol)
        result.entry_signal = entry_sig
        result.plan = plan
        result.simulation = sim
        result.order = order

        if mode == RunMode.SIGNAL_ONLY or not order:
            return result

        # Step 3: Execution
        auto_confirm = (mode == RunMode.AUTO)
        passed, broker_res = await self.run_execution(order, user_confirmed=auto_confirm)
        result.risk_passed = passed
        result.broker_result = broker_res

        return result
