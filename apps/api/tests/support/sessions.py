"""Test doubles for the sessions module."""

from datetime import datetime, timedelta
from http.cookies import Morsel, SimpleCookie

from httpx import Response

from cursora_api.modules.sessions.models import SignalBatch, WidgetSession
from cursora_api.modules.sessions.repository import SessionRepository
from cursora_api.modules.sessions.router import SESSION_COOKIE


class InMemorySessionRepository(SessionRepository):
    """Keeps sessions and signal batches in memory instead of the database."""

    def __init__(self) -> None:
        self.rows: dict[str, WidgetSession] = {}
        self.batches: list[SignalBatch] = []

    async def get(self, session_id: str) -> WidgetSession | None:
        return self.rows.get(session_id)

    async def add(self, session: WidgetSession) -> None:
        assert session.id not in self.rows, "primary key violation"
        self.rows[session.id] = session

    async def count_batches_since(self, session_id: str, since: datetime) -> int:
        return sum(
            batch.session_id == session_id and batch.received_at > since for batch in self.batches
        )

    async def add_batch(self, batch: SignalBatch) -> None:
        batch.id = len(self.batches) + 1
        self.batches.append(batch)

    async def increment_rejected_batches(self, session_id: str) -> None:
        if session := self.rows.get(session_id):
            session.rejected_signal_batches += 1


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, delta: timedelta) -> None:
        self.now += delta


def session_cookie(response: Response) -> Morsel[str]:
    """The session cookie from the response's Set-Cookie header, with its attributes."""
    return SimpleCookie(response.headers["set-cookie"])[SESSION_COOKIE]


def with_session(session_id: str) -> dict[str, str]:
    """Request headers that send ``session_id`` in the session cookie."""
    return {"Cookie": f"{SESSION_COOKIE}={session_id}"}
