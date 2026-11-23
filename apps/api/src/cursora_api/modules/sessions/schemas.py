"""Pydantic request/response schemas of the sessions module."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from cursora_api.modules.sessions.models import SessionState
from cursora_api.modules.tenant.service import SITE_KEY_MAX_LENGTH


class SessionRequest(BaseModel):
    """What the widget sends when a page with it loads."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(min_length=1, max_length=SITE_KEY_MAX_LENGTH)


class SessionResponse(BaseModel):
    """The visitor's current session. The id itself is only in the HttpOnly cookie."""

    state: SessionState
    expires_at: datetime
