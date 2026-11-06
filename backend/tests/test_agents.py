"""Smoke test to verify that all agents can be instantiated and wired properly."""

import pytest
from app.agents.commander import CommanderAgent
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
from app.core.config import settings


def test_agent_instantiation():
    """Verify all 11 agents and the Commander instantiate cleanly."""
    cmd = CommanderAgent()
    assert cmd.scanner.name == "scanner"
    assert cmd.news.name == "news"
    assert cmd.analyst.name == "analyst"
    assert cmd.pelosi.name == "pelosi"
    assert cmd.entry.name == "entry"
    assert cmd.exit.name == "exit"
    assert cmd.timemachine.name == "timemachine"
    assert cmd.budget.name == "budget"
    assert cmd.risk.name == "risk"
    assert cmd.broker.name == "broker"
    assert cmd.alerts.name == "alerts"


def test_skill_paths_exist():
    """Verify that all 11 underlying skill scripts exist on disk."""
    agents = [
        ScannerAgent(),
        NewsAgent(),
        AnalystAgent(),
        PelosiAgent(),
        EntryAgent(),
        ExitAgent(),
        TimeMachineAgent(),
        BudgetAgent(),
        RiskAgent(),
        BrokerAgent(),
        AlertsAgent(),
    ]
    for agent in agents:
        path = agent.skill_path()
        assert path.exists(), f"Skill file does not exist: {path}"
