"""POST /v1/sessions over HTTP, with the database replaced by an in-memory repository."""

from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from support.sessions import FakeClock, InMemorySessionRepository, session_cookie, with_session

from cursora_api.core.config import Settings
from cursora_api.main import create_app
from cursora_api.modules.sessions.models import SessionState
from cursora_api.modules.sessions.router import get_session_service
from cursora_api.modules.sessions.service import SessionService

NOW = datetime(2026, 10, 24, 12, 0, tzinfo=UTC)


@pytest.fixture
def repository() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def ttl(settings: Settings) -> timedelta:
    return timedelta(seconds=settings.session_ttl_s)


@pytest.fixture(autouse=True)
def _in_memory_sessions(
    app: FastAPI, repository: InMemorySessionRepository, clock: FakeClock, ttl: timedelta
) -> None:
    app.dependency_overrides[get_session_service] = lambda: SessionService(
        repository, ttl=ttl, clock=clock
    )


async def test_new_visitor_gets_a_new_session_in_an_httponly_cookie(
    client: AsyncClient, repository: InMemorySessionRepository, ttl: timedelta
) -> None:
    response = await client.post("/v1/sessions")

    assert response.status_code == 201
    assert response.json() == {"state": "new", "expires_at": "2026-10-24T12:30:00Z"}
    cookie = session_cookie(response)
    assert list(repository.rows) == [cookie.value]
    assert cookie["expires"] == format_datetime(NOW + ttl, usegmt=True)
    assert cookie["path"] == "/"
    assert cookie["httponly"]
    assert cookie["secure"]
    assert cookie["samesite"] == "lax"


async def test_cookie_flags_come_from_settings(
    repository: InMemorySessionRepository, clock: FakeClock
) -> None:
    settings = Settings(env="test", session_cookie_secure=False, session_cookie_samesite="strict")
    app = create_app(settings)
    app.dependency_overrides[get_session_service] = lambda: SessionService(
        repository, ttl=timedelta(seconds=settings.session_ttl_s), clock=clock
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/sessions")
    await app.state.engine.dispose()

    cookie = session_cookie(response)
    assert cookie["httponly"]
    assert not cookie["secure"]
    assert cookie["samesite"] == "strict"


async def test_returning_visitor_keeps_the_same_session_and_state(
    client: AsyncClient, repository: InMemorySessionRepository, clock: FakeClock
) -> None:
    created = await client.post("/v1/sessions")
    session_id = session_cookie(created).value
    repository.rows[session_id].state = SessionState.CHALLENGE_REQUIRED
    clock.advance(timedelta(minutes=1))

    response = await client.post("/v1/sessions", headers=with_session(session_id))

    assert response.status_code == 200
    assert response.json() == {
        "state": "challenge_required",
        "expires_at": created.json()["expires_at"],
    }
    assert "set-cookie" not in response.headers
    assert list(repository.rows) == [session_id]


async def test_expired_session_is_replaced_and_its_id_not_reused(
    client: AsyncClient, repository: InMemorySessionRepository, clock: FakeClock, ttl: timedelta
) -> None:
    created = await client.post("/v1/sessions")
    old_id = session_cookie(created).value
    repository.rows[old_id].state = SessionState.VERIFIED
    clock.advance(ttl)

    response = await client.post("/v1/sessions", headers=with_session(old_id))

    assert response.status_code == 201
    assert response.json()["state"] == "new"
    new_id = session_cookie(response).value
    assert new_id != old_id
    assert set(repository.rows) == {old_id, new_id}
    assert repository.rows[old_id].state is SessionState.VERIFIED


async def test_unknown_session_id_is_ignored(
    client: AsyncClient, repository: InMemorySessionRepository
) -> None:
    response = await client.post("/v1/sessions", headers=with_session("forged-session-id"))

    assert response.status_code == 201
    new_id = session_cookie(response).value
    assert new_id != "forged-session-id"
    assert list(repository.rows) == [new_id]
