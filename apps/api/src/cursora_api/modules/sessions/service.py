"""Service layer of the sessions module: use cases and business logic."""

import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from cursora_api.modules.sessions.models import SessionState, WidgetSession
from cursora_api.modules.sessions.repository import SessionRepository

# 32 random bytes = 256 bits of entropy, 43 URL-safe characters.
SESSION_ID_BYTES = 32


def new_session_id() -> str:
    """A cryptographically secure, URL- and cookie-safe session id."""
    return secrets.token_urlsafe(SESSION_ID_BYTES)


def utc_now() -> datetime:
    return datetime.now(UTC)


class SessionService:
    def __init__(
        self,
        repository: SessionRepository,
        *,
        ttl: timedelta,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._repository = repository
        self._ttl = ttl
        self._clock = clock

    async def get_or_create(self, session_id: str | None) -> tuple[WidgetSession, bool]:
        """Return ``(session, created)`` for the id from the visitor's cookie.

        A live session is returned unchanged, state included. A missing, unknown or expired id
        is ignored and a new session in state ``new`` is created with a fresh id.

        TODO(team): absolute lifetime for now; decide whether reuse should extend ``expires_at``.
        """
        now = self._clock()
        if session_id:
            session = await self._repository.get(session_id)
            if session is not None and session.expires_at > now:
                return session, False

        session = WidgetSession(
            id=new_session_id(),
            state=SessionState.NEW,
            created_at=now,
            expires_at=now + self._ttl,
        )
        await self._repository.add(session)
        return session, True
