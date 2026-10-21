"""Application settings, loaded from environment variables (see .env.example)."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CURSORA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"
    # 127.0.0.1, not localhost: on Windows/Docker Desktop "localhost" may resolve to ::1 and hang.
    database_url: str = "postgresql+asyncpg://cursora:cursora@127.0.0.1:5432/cursora"
    db_echo: bool = False
    db_connect_timeout_s: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
