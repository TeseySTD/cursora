"""Service layer of the sessions module: use cases and business logic."""

import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from cursora_api.modules.sessions.models import SessionState, WidgetSession
from cursora_api.modules.sessions.repository import SessionRepository
from cursora_api.modules.tenant.service import TenantService

# 32 random bytes = 256 bits of entropy, 43 URL-safe characters.
SESSION_ID_BYTES = 32


def new_session_id() -> str:
    """A cryptographically secure, URL- and cookie-safe session id."""
    return secrets.token_urlsafe(SESSION_ID_BYTES)


def utc_now() -> datetime:
    return datetime.now(UTC)


class SiteNotFoundError(Exception):
    """No site has the site key the widget sent."""


class SessionService:
    def __init__(
        self,
        repository: SessionRepository,
        tenant: TenantService,
        *,
        ttl: timedelta,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._repository = repository
        self._tenant = tenant
        self._ttl = ttl
        self._clock = clock

    async def get_or_create(
        self, session_id: str | None, site_key: str
    ) -> tuple[WidgetSession, bool]:
        """Return ``(session, created)`` for the id from the visitor's cookie on the given site.

        A live session of the same site is returned unchanged, state included. A missing,
        unknown or expired id, or a session of another site, is ignored and a new session in
        state ``new`` is created with a fresh id (BR-3, BR-4).

        Raises ``SiteNotFoundError`` if no site has ``site_key``.

        TODO(team): absolute lifetime for now; decide whether reuse should extend ``expires_at``.
        """
        site = await self._tenant.find_by_site_key(site_key)
        if site is None:
            raise SiteNotFoundError

        now = self._clock()
        if session_id:
            session = await self._repository.get(session_id)
            if session is not None and session.site_id == site.id and session.expires_at > now:
                return session, False

        session = WidgetSession(
            id=new_session_id(),
            site_id=site.id,
            state=SessionState.NEW,
            created_at=now,
            expires_at=now + self._ttl,
        )
        await self._repository.add(session)
        return session, True
