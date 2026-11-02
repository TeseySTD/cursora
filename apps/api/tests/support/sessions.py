"""Test doubles for the sessions module."""

from datetime import datetime, timedelta
from http.cookies import Morsel, SimpleCookie

from httpx import Response

from cursora_api.modules.sessions.models import WidgetSession
from cursora_api.modules.sessions.repository import SessionRepository
from cursora_api.modules.sessions.router import SESSION_COOKIE


class InMemorySessionRepository(SessionRepository):
    """Keeps sessions in a dict instead of the database."""

    def __init__(self) -> None:
        self.rows: dict[str, WidgetSession] = {}

    async def get(self, session_id: str) -> WidgetSession | None:
        return self.rows.get(session_id)

    async def add(self, session: WidgetSession) -> None:
        assert session.id not in self.rows, "primary key violation"
        self.rows[session.id] = session


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
