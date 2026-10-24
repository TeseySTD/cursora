"""HTTP layer of the sessions module: request/response mapping only, no business logic."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status

from cursora_api.core.config import SettingsDep
from cursora_api.core.db import SessionDep
from cursora_api.modules.sessions.repository import SessionRepository
from cursora_api.modules.sessions.schemas import SessionResponse
from cursora_api.modules.sessions.service import SessionService

# Holds the session id. Never log or return its value.
SESSION_COOKIE = "cursora_session"

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_session_service(db: SessionDep, settings: SettingsDep) -> SessionService:
    return SessionService(SessionRepository(db), ttl=timedelta(seconds=settings.session_ttl_s))


SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]


@router.post(
    "",
    response_model=SessionResponse,
    responses={
        status.HTTP_200_OK: {"description": "The live session from the cookie was reused."},
        status.HTTP_201_CREATED: {
            "model": SessionResponse,
            "description": "A new session was created and set in the cookie.",
        },
    },
)
async def ensure_session(
    response: Response,
    service: SessionServiceDep,
    settings: SettingsDep,
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> SessionResponse:
    """Restore the visitor's session from the cookie, or create a new one.

    Called by the widget when a page with it loads.

    - 200: the cookie holds a live session. It is reused as is, state included.
    - 201: no cookie, or its session is unknown or expired. A new session in state ``new``
      is created and its id is set in an HttpOnly cookie that expires with the session.
    """
    session, created = await service.get_or_create(session_id)
    if created:
        response.status_code = status.HTTP_201_CREATED
        response.set_cookie(
            SESSION_COOKIE,
            session.id,
            expires=session.expires_at,
            path="/",
            secure=settings.session_cookie_secure,
            httponly=True,
            samesite=settings.session_cookie_samesite,
        )
    return SessionResponse(state=session.state, expires_at=session.expires_at)
