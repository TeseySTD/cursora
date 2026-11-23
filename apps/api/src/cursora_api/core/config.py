"""Application settings, loaded from environment variables (see .env.example)."""

from functools import lru_cache
from typing import Annotated, Literal, Self

from fastapi import Depends, Request
from pydantic import PositiveInt, model_validator
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

    # Widget sessions (sessions module). The cookie is always HttpOnly: the widget never reads it.
    # TODO(team): default session lifetime (open question in CAPTHCA-16).
    session_ttl_s: PositiveInt = 1800
    # TODO(team): cookie flags for embedding on customer domains (open question in CAPTHCA-16).
    # Browsers accept Secure cookies from http://localhost, so the default also works in dev.
    session_cookie_secure: bool = True
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # Signal ingestion (sessions module). The widget sends a batch every 2 s or at 100 signals,
    # so about one a second at most.
    # TODO(team): maximum batch size and rate are placeholders (open questions in CAPTHCA-17).
    signal_batch_max_bytes: PositiveInt = 32768
    signal_batch_max_signals: PositiveInt = 200
    signal_rate_max_batches: PositiveInt = 10
    signal_rate_window_s: PositiveInt = 10

    @model_validator(mode="after")
    def _samesite_none_requires_secure(self) -> Self:
        # Browsers drop SameSite=None cookies without Secure: every load would be a new session.
        if self.session_cookie_samesite == "none" and not self.session_cookie_secure:
            raise ValueError("session_cookie_samesite='none' requires session_cookie_secure=true")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_app_settings(request: Request) -> Settings:
    """FastAPI dependency: the settings the app was created with (see ``create_app``)."""
    settings: Settings = request.app.state.settings
    return settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
