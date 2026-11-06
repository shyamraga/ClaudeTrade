---
name: project-bootstrap
description: Initial project structure and agent hierarchy for Claude Trade
metadata:
  type: project
---

# Claude Trade — Project Bootstrap (2026-11-06)

## What was built

Full backend scaffold for a hybrid trading simulator + algorithmic trading bot.

**Stack**: Python 3.12 + FastAPI + WebSockets backend. React frontend (not yet scaffolded).

**Project root**: `C:\Users\shyam\.claude\projects\Claude Trade`

## Agent Hierarchy

11 trading skills wrapped as Python agents, organized into 3 tiers under a Commander:

```
Commander
├── Tier ① Intelligence (parallel fan-out)
│   ├── trader-scanner   → ScannerAgent
│   ├── trader-news      → NewsAgent
│   ├── trader-analyst   → AnalystAgent
│   └── trader-pelosi    → PelosiAgent
├── Tier ② Execution Planning (sequential)
│   ├── trader-entry     → EntryAgent
│   ├── trader-exit      → ExitAgent
│   ├── trader-timemachine → TimeMachineAgent
│   └── trader-budget    → BudgetAgent
└── Tier ③ Execution (gates)
    ├── trader-risk      → RiskAgent  (hard BLOCK gate)
    ├── trader-broker    → BrokerAgent (2x user confirm)
    └── trader-alerts    → AlertsAgent (monitors live)
```

## Key Files

- `backend/app/agents/commander.py` — top-level orchestrator
- `backend/app/agents/base.py` — BaseAgent (emit, skill runner)
- `backend/app/core/events.py` — EventBus pub/sub for WebSocket streaming
- `backend/app/core/skill_runner.py` — async subprocess wrapper for skill CLIs
- `backend/app/core/config.py` — Settings (all 11 skill paths, env vars)
- `backend/app/main.py` — FastAPI app
- `backend/app/api/pipeline.py` — REST: /pipeline/run, /plan/{symbol}, /approve
- `backend/app/api/ws.py` — WebSocket /ws (streams PipelineEvents)
- `backend/trader/config.json` — risk limits (paper=true, $50 max loss)
- `backend/.env.example` — SEC_USER_AGENT, Alpaca keys template
- `CLAUDE.md` — guidance for future Claude Code sessions

## Tests

`backend/tests/test_agents.py` — 2/2 passing:
- `test_agent_instantiation` — all 11 agents + Commander instantiate
- `test_skill_paths_exist` — all 11 skill .py files exist on disk

## Run

```bash
cd backend
uv run --all-extras uvicorn app.main:app --reload --port 8000
```

## Next Steps (pending)

1. React frontend (Vite + TailwindCSS, connects to /ws)
2. APScheduler job for pre-market daily scan
3. trader/config.json setup wizard
4. End-to-end paper trade test with Alpaca keys

**Why**: User wants to build a hybrid simulator + algo bot using the 11 installed trader-* skills as agents.

**How to apply**: Always check `backend/trader/config.json` for risk limits before running any execution tier code. Skills are at `C:/Users/shyam/.claude/skills/trader-*/`. All agents inherit from `BaseAgent` — add new agents the same way.
