from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://wc:wc@localhost:5432/worldcup"
    API_FOOTBALL_KEY: Optional[str] = None
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"
    # FIFA World Cup = league 1. Season 2026 is the target; the API-Football free
    # plan only covers 2021–2023, so set API_FOOTBALL_SEASON=2022 for real demo data.
    API_FOOTBALL_LEAGUE: int = 1
    API_FOOTBALL_SEASON: int = 2026
    DEEPSEEK_API_KEY: Optional[str] = None
    BRIEF_TIMEZONE: str = "Australia/Melbourne"


settings = Settings()
