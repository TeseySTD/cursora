import re
from datetime import UTC, datetime, timedelta

import pytest
from support.sessions import FakeClock, InMemorySessionRepository
from support.tenant import InMemorySiteRepository

from cursora_api.modules.sessions.models import SESSION_ID_MAX_LENGTH, SessionState
from cursora_api.modules.sessions.service import SessionService, SiteNotFoundError, new_session_id
from cursora_api.modules.tenant.models import Site
from cursora_api.modules.tenant.service import TenantService

NOW = datetime(2026, 10, 24, 12, 0, tzinfo=UTC)
TTL = timedelta(minutes=30)


@pytest.fixture
def repository() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def tenant() -> TenantService:
    return TenantService(InMemorySiteRepository())


@pytest.fixture
async def site(tenant: TenantService) -> Site:
    site, _ = await tenant.create_site("example.com", [])
    return site


@pytest.fixture
def service(
    repository: InMemorySessionRepository, tenant: TenantService, clock: FakeClock
) -> SessionService:
    return SessionService(repository, tenant, ttl=TTL, clock=clock)


def test_session_ids_are_random_and_cookie_safe() -> None:
    ids = {new_session_id() for _ in range(1000)}
    assert len(ids) == 1000
    for session_id in ids:
        assert re.fullmatch(r"[A-Za-z0-9_-]{43}", session_id)
        assert len(session_id) <= SESSION_ID_MAX_LENGTH


async def test_without_id_creates_a_new_session_on_the_site(
    service: SessionService, repository: InMemorySessionRepository, site: Site
) -> None:
    session, created = await service.get_or_create(None, site.site_key)

    assert created
    assert session.site_id == site.id
    assert session.state is SessionState.NEW
    assert session.created_at == NOW
    assert session.expires_at == NOW + TTL
    assert repository.rows == {session.id: session}


async def test_unknown_site_key_is_rejected(
    service: SessionService, repository: InMemorySessionRepository
) -> None:
    with pytest.raises(SiteNotFoundError):
        await service.get_or_create(None, "unknown-site-key")

    assert repository.rows == {}


async def test_live_session_is_reused_as_is(
    service: SessionService, repository: InMemorySessionRepository, clock: FakeClock, site: Site
) -> None:
    session, _ = await service.get_or_create(None, site.site_key)
    session.state = SessionState.VERIFIED
    clock.advance(TTL - timedelta(seconds=1))

    reused, created = await service.get_or_create(session.id, site.site_key)

    assert not created
    assert reused is session
    assert reused.state is SessionState.VERIFIED
    assert reused.expires_at == NOW + TTL
    assert len(repository.rows) == 1


async def test_session_of_another_site_is_not_reused(
    service: SessionService,
    repository: InMemorySessionRepository,
    tenant: TenantService,
    site: Site,
) -> None:
    other_site, _ = await tenant.create_site("other.example", [])
    other, _ = await service.get_or_create(None, other_site.site_key)
    other.state = SessionState.VERIFIED

    session, created = await service.get_or_create(other.id, site.site_key)

    assert created
    assert session.id != other.id
    assert session.site_id == site.id
    assert session.state is SessionState.NEW
    assert repository.rows[other.id] is other
    assert other.state is SessionState.VERIFIED


@pytest.mark.parametrize("age", [TTL, TTL + timedelta(days=1)], ids=["at-expiry", "long-expired"])
async def test_expired_session_is_replaced(
    service: SessionService,
    repository: InMemorySessionRepository,
    clock: FakeClock,
    site: Site,
    age: timedelta,
) -> None:
    old, _ = await service.get_or_create(None, site.site_key)
    old.state = SessionState.VERIFIED
    clock.advance(age)

    session, created = await service.get_or_create(old.id, site.site_key)

    assert created
    assert session.id != old.id
    assert session.state is SessionState.NEW
    assert session.expires_at == clock.now + TTL
    # The old row stays, so its id can never be handed out again.
    assert repository.rows[old.id] is old
    assert old.state is SessionState.VERIFIED


@pytest.mark.parametrize("session_id", ["", "unknown"])
async def test_unknown_id_is_ignored(
    service: SessionService, repository: InMemorySessionRepository, site: Site, session_id: str
) -> None:
    session, created = await service.get_or_create(session_id, site.site_key)

    assert created
    assert session.id != session_id
    assert list(repository.rows) == [session.id]
