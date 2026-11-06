"""App configuration loaded from environment / .env file."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # SEC
    sec_user_agent: str = ""

    # Alpaca
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_paper_trade: bool = True

    # Paths
    trader_dir: Path = Path("./trader")
    skills_dir: Path = Path("C:/Users/shyam/.claude/skills")

    # App
    log_level: str = "INFO"

    @property
    def trader_state_dir(self) -> Path:
        return self.trader_dir / "state"

    @property
    def scanner_skill(self) -> Path:
        return self.skills_dir / "trader-scanner" / "scan.py"

    @property
    def news_skill(self) -> Path:
        return self.skills_dir / "trader-news" / "news.py"

    @property
    def analyst_skill(self) -> Path:
        return self.skills_dir / "trader-analyst" / "facts.py"

    @property
    def pelosi_skill(self) -> Path:
        return self.skills_dir / "trader-pelosi" / "ptr.py"

    @property
    def entry_skill(self) -> Path:
        return self.skills_dir / "trader-entry" / "entry.py"

    @property
    def exit_skill(self) -> Path:
        return self.skills_dir / "trader-exit" / "exit.py"

    @property
    def timemachine_skill(self) -> Path:
        return self.skills_dir / "trader-timemachine" / "timemachine.py"

    @property
    def budget_skill(self) -> Path:
        return self.skills_dir / "trader-budget" / "size.py"

    @property
    def risk_skill(self) -> Path:
        return self.skills_dir / "trader-risk" / "check.py"

    @property
    def alerts_skill(self) -> Path:
        return self.skills_dir / "trader-alerts" / "alerts.py"

    @property
    def broker_skill(self) -> Path:
        return self.skills_dir / "trader-broker" / "ticket.py"


settings = Settings()
