"""Service layer of the sessions module: use cases and business logic."""

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from cursora_api.modules.sessions.models import SessionState, SignalBatch, WidgetSession
from cursora_api.modules.sessions.repository import SessionRepository
from cursora_api.modules.sessions.schemas import SignalBatchIn
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


class SessionInvalidError(Exception):
    """No session cookie, or its session is unknown or expired."""


class RateLimitedError(Exception):
    """The session sent more signal batches than the rate limit allows."""


class BatchTooLargeError(Exception):
    """The signal batch is larger than allowed."""


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
            rejected_signal_batches=0,
        )
        await self._repository.add(session)
        return session, True


@dataclass(frozen=True, slots=True)
class SignalLimits:
    """Limits on the signal batches one session may send.

    TODO(team): the values come from settings and are placeholders (CAPTHCA-17 open questions).
    """

    max_signals: int
    rate_max_batches: int
    rate_window: timedelta


class SignalService:
    """Stores the widget's signal batches for live sessions (BR-6)."""

    def __init__(
        self,
        repository: SessionRepository,
        *,
        limits: SignalLimits,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._repository = repository
        self._limits = limits
        self._clock = clock

    async def require_live_session(self, session_id: str | None) -> WidgetSession:
        """The live session from the cookie, or ``SessionInvalidError``.

        Signals are accepted only for a live session; without one the widget opens a new
        session instead of retrying (CAPTHCA-17 AC4).
        """
        if session_id:
            session = await self._repository.get(session_id)
            if session is not None and session.expires_at > self._clock():
                return session
        raise SessionInvalidError

    async def check_rate(self, session: WidgetSession) -> None:
        """Raise ``RateLimitedError`` once the session reached the batch limit in the window.

        Runs before the body is read, so a flood costs one count query per request.
        Concurrent requests are not serialised: a burst can exceed the limit by a few batches,
        which is fine for a signal and needs no lock.
        """
        since = self._clock() - self._limits.rate_window
        sent = await self._repository.count_batches_since(session.id, since)
        if sent >= self._limits.rate_max_batches:
            await self.record_rejected(session)
            raise RateLimitedError

    async def record_rejected(self, session: WidgetSession) -> None:
        """Count a batch rejected as too large or too frequent (CAPTHCA-17 AC6)."""
        await self._repository.increment_rejected_batches(session.id)

    async def store(self, session: WidgetSession, batch: SignalBatchIn) -> None:
        """Store a validated batch as JSONB, linked to the session and its site."""
        if len(batch.signals) > self._limits.max_signals:
            await self.record_rejected(session)
            raise BatchTooLargeError
        await self._repository.add_batch(
            SignalBatch(
                session_id=session.id,
                site_id=session.site_id,
                received_at=self._clock(),
                payload=batch.model_dump(mode="json"),
                signal_count=len(batch.signals),
            )
        )
