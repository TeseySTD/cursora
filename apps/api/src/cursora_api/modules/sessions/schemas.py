"""Pydantic request/response schemas of the sessions module."""

from datetime import datetime

from pydantic import BaseModel

from cursora_api.modules.sessions.models import SessionState


class SessionResponse(BaseModel):
    """The visitor's current session. The id itself is only in the HttpOnly cookie."""

    state: SessionState
    expires_at: datetime
