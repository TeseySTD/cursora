import re
from datetime import UTC, datetime, timedelta

import pytest
from support.sessions import FakeClock, InMemorySessionRepository

from cursora_api.modules.sessions.models import SESSION_ID_MAX_LENGTH, SessionState
from cursora_api.modules.sessions.service import SessionService, new_session_id

NOW = datetime(2026, 10, 24, 12, 0, tzinfo=UTC)
TTL = timedelta(minutes=30)


@pytest.fixture
def repository() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def service(repository: InMemorySessionRepository, clock: FakeClock) -> SessionService:
    return SessionService(repository, ttl=TTL, clock=clock)


def test_session_ids_are_random_and_cookie_safe() -> None:
    ids = {new_session_id() for _ in range(1000)}
    assert len(ids) == 1000
    for session_id in ids:
        assert re.fullmatch(r"[A-Za-z0-9_-]{43}", session_id)
        assert len(session_id) <= SESSION_ID_MAX_LENGTH


async def test_without_id_creates_a_new_session(
    service: SessionService, repository: InMemorySessionRepository
) -> None:
    session, created = await service.get_or_create(None)

    assert created
    assert session.state is SessionState.NEW
    assert session.created_at == NOW
    assert session.expires_at == NOW + TTL
    assert repository.rows == {session.id: session}


async def test_live_session_is_reused_as_is(
    service: SessionService, repository: InMemorySessionRepository, clock: FakeClock
) -> None:
    session, _ = await service.get_or_create(None)
    session.state = SessionState.VERIFIED
    clock.advance(TTL - timedelta(seconds=1))

    reused, created = await service.get_or_create(session.id)

    assert not created
    assert reused is session
    assert reused.state is SessionState.VERIFIED
    assert reused.expires_at == NOW + TTL
    assert len(repository.rows) == 1


@pytest.mark.parametrize("age", [TTL, TTL + timedelta(days=1)], ids=["at-expiry", "long-expired"])
async def test_expired_session_is_replaced(
    service: SessionService,
    repository: InMemorySessionRepository,
    clock: FakeClock,
    age: timedelta,
) -> None:
    old, _ = await service.get_or_create(None)
    old.state = SessionState.VERIFIED
    clock.advance(age)

    session, created = await service.get_or_create(old.id)

    assert created
    assert session.id != old.id
    assert session.state is SessionState.NEW
    assert session.expires_at == clock.now + TTL
    # The old row stays, so its id can never be handed out again.
    assert repository.rows[old.id] is old
    assert old.state is SessionState.VERIFIED


@pytest.mark.parametrize("session_id", ["", "unknown"])
async def test_unknown_id_is_ignored(
    service: SessionService, repository: InMemorySessionRepository, session_id: str
) -> None:
    session, created = await service.get_or_create(session_id)

    assert created
    assert session.id != session_id
    assert list(repository.rows) == [session.id]
