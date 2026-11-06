"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.pipeline import router as pipeline_router
from app.api.ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure trader state dirs exist
    from app.core.config import settings
    settings.trader_state_dir.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown logic if needed


app = FastAPI(
    title="Claude Trade API",
    description="Backend for Claude Trade hybrid simulator and algorithmic trading bot",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline_router)
app.include_router(ws_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "claude-trade-backend"}
