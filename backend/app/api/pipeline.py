"""FastAPI router exposing pipeline trigger endpoints and status."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.agents.commander import CommanderAgent, RunMode

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
commander = CommanderAgent()


class TriggerRequest(BaseModel):
    mode: RunMode = RunMode.SEMI_AUTO
    symbol: str | None = None


class ApproveRequest(BaseModel):
    index: int = 1
    reply: str = "yes"


@router.post("/run")
async def trigger_pipeline(req: TriggerRequest, background_tasks: BackgroundTasks) -> dict:
    """Trigger the pipeline in background and return immediately."""
    background_tasks.add_task(commander.run_pipeline, req.mode, req.symbol)
    return {"status": "started", "mode": req.mode, "symbol": req.symbol}


@router.post("/intelligence")
async def run_intelligence(mode: str = "daily", symbols: list[str] | None = None) -> dict:
    """Run only Tier ① Intelligence (scanner + news + analyst + pelosi)."""
    hits, enriched = await commander.run_intelligence(mode=mode, symbols=symbols)
    return {"hits": hits, "enriched": enriched}


@router.post("/plan/{symbol}")
async def run_planning(symbol: str, setup: str = "orb") -> dict:
    """Run only Tier ② Planning for a specific ticker."""
    entry_sig, plan, sim, order = await commander.run_planning(symbol=symbol, setup=setup)
    return {
        "symbol": symbol,
        "entry": entry_sig,
        "plan": plan,
        "simulation": sim,
        "order": order,
    }


@router.post("/approve")
async def approve_order(req: ApproveRequest) -> dict:
    """Record user confirmation for a pending order."""
    approved = await commander.broker.approve(index=req.index, reply=req.reply)
    if not approved:
        raise HTTPException(status_code=400, detail="Approval rejected — reply must be an explicit yes")
    return {"status": "approved", "index": req.index}


@router.get("/tickets")
async def get_tickets() -> dict:
    """Get the current order tickets and their readiness status."""
    tickets_text = await commander.broker.show_tickets()
    return {"tickets": tickets_text}
