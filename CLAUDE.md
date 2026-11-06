# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (Python / FastAPI)
```bash
# Install dependencies
cd backend
uv sync

# Run development server with reload
uv run uvicorn app.main:app --reload --port 8000

# Run all tests
uv run pytest

# Run a single test
uv run pytest tests/test_pipeline.py -k test_intelligence_tier

# Lint / format check
uv run ruff check .
uv run ruff format --check .
```

### Trading Skills CLI (run from backend/trader/)
All trading skills are located at `C:/Users/shyam/.claude/skills/` and can be invoked directly:

```bash
# Scanner: daily scan before the open
python -I "C:/Users/shyam/.claude/skills/trader-scanner/scan.py" daily

# Scanner: ORB scan after 9:50 AM ET
python -I "C:/Users/shyam/.claude/skills/trader-scanner/scan.py" orb

# News: headlines + SEC 8-K filings
python -I "C:/Users/shyam/.claude/skills/trader-news/news.py" --tickers TSLA,NVDA

# Analyst: SEC XBRL fundamentals & earnings Q/Q
python -I "C:/Users/shyam/.claude/skills/trader-analyst/facts.py" TSLA

# Pelosi: Congressional trade disclosures
python -I "C:/Users/shyam/.claude/skills/trader-pelosi/ptr.py" new --member pelosi

# Entry: check if bar closed above trigger level
python -I "C:/Users/shyam/.claude/skills/trader-entry/entry.py" check TSLA --write

# Exit: create plan (stop + target) before entry
python -I "C:/Users/shyam/.claude/skills/trader-exit/exit.py" plan --write

# TimeMachine: 10,000 Monte Carlo replays from recent bars
python -I "C:/Users/shyam/.claude/skills/trader-timemachine/timemachine.py" run --write

# Budget: size order to max loss per trade
python -I "C:/Users/shyam/.claude/skills/trader-budget/size.py" --write

# Risk: gate all orders (PASS or BLOCK)
python -I "C:/Users/shyam/.claude/skills/trader-risk/check.py"

# Broker: show tickets / record user yes
python -I "C:/Users/shyam/.claude/skills/trader-broker/ticket.py" show

# Alerts: arm stop / target / flat-by alerts
python -I "C:/Users/shyam/.claude/skills/trader-alerts/alerts.py" add --from-plan
```

### Frontend (React + Vite + TailwindCSS)
```bash
cd frontend
npm install
npm run dev      # runs on http://localhost:5173
npm run build    # production build
```

---

## High-Level Architecture

Claude Trade is a hybrid trading simulator and algorithmic trading bot built around **11 specialized trading agents** structured into a three-tier hierarchy managed by a top-level **Commander**:

```
                       ┌─────────────────────────┐
                       │     COMMANDER AGENT     │
                       │  (orchestrates flow)    │
                       └────────────┬────────────┘
                                    │
    ┌───────────────────────────────┼──────────────────────────────┐
    │                               │                              │
    ▼                               ▼                              ▼
TIER ① INTELLIGENCE            TIER ② PLANNING                TIER ③ EXECUTION
(parallel fan-out)             (sequential pipeline)          (gates & execution)
┌──────────────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
│ trader-scanner       │       │ trader-entry         │       │ trader-risk          │
│ trader-news          │       │ trader-exit          │       │ (hard BLOCK gate)    │
│ trader-analyst       │       │ trader-timemachine   │       └──────────┬───────────┘
│ trader-pelosi        │       │ trader-budget        │                  │ PASS
└──────────────────────┘       └──────────────────────┘                  ▼
                                                              ┌──────────────────────┐
                                                              │ trader-broker        │
                                                              │ (2x user confirmation)│
                                                              └──────────┬───────────┘
                                                                         │
                                                                         ▼
                                                              ┌──────────────────────┐
                                                              │ trader-alerts        │
                                                              │ (monitors live)      │
                                                              └──────────────────────┘
```

### Agent Hierarchy & Flow

1. **Tier ① — Intelligence (Parallel Fan-Out)**:
   - `ScannerAgent` finds liquid charts matching rules (breakout, bull flag, ORB) → writes `watchlist.json`.
   - `NewsAgent`, `AnalystAgent`, and `PelosiAgent` run concurrently via `asyncio.gather` to enrich candidate tickers with headlines, SEC XBRL financials, and congressional disclosures.

2. **Tier ② — Execution Planning (Sequential Pipeline)**:
   - `EntryAgent` confirms a setup only when a bar *closes* above the trigger level → writes `entry.json`.
   - `ExitAgent` sets stop-loss and profit target *before* entry → writes `plan.json`.
   - `TimeMachineAgent` runs 10,000 Monte Carlo replays against the last 60 days of 5m bars → writes `timemachine.json`.
   - `BudgetAgent` sizes the trade to the `$50` max loss limit → writes `orders.json`.

3. **Tier ③ — Execution (Risk Gate & Execution)**:
   - `RiskAgent` checks format, size, cash buffer, daily loss limits, and trading windows. A **BLOCK is final** — never bypassed.
   - `BrokerAgent` requires **two explicit human yeses** (typed in chat + clicked on permission card) before any order is submitted. Trades on a **paper account** by default.
   - `AlertsAgent` monitors stop-loss, take-profit, and the mandatory 15:55 ET flat-by time.

4. **Event Bus & Real-Time Comms**:
   - Every agent inherits from `BaseAgent` and emits structured `PipelineEvent` messages.
   - `EventBus` (`app/core/events.py`) broadcasts updates in real time to connected browser sessions via WebSocket (`/ws`).

### Key Invariants & Safety Rules

- **Paper trading by default**: `"paper": true` in `trader/config.json`. Live trading is strictly opt-in by the user.
- **Never auto-execute real money orders**: The broker gate requires explicit user approval every time.
- **Closed bars only**: Entry triggers never fire on incomplete or live-forming bars.
- **Exit before entry**: Stop and target are always calculated and agreed upon before any order is sized.
- **Flat by close**: Day trades must be closed by 15:55 ET — no unmanaged overnight holds.
