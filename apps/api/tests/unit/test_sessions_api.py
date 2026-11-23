"""POST /v1/sessions over HTTP, with the database replaced by an in-memory repository."""

from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from support.sessions import FakeClock, InMemorySessionRepository, session_cookie, with_session
from support.tenant import InMemorySiteRepository

from cursora_api.core.config import Settings
from cursora_api.main import create_app
from cursora_api.modules.sessions.models import SessionState
from cursora_api.modules.sessions.router import get_session_service
from cursora_api.modules.sessions.service import SessionService
from cursora_api.modules.tenant.models import Site
from cursora_api.modules.tenant.service import TenantService

NOW = datetime(2026, 10, 24, 12, 0, tzinfo=UTC)


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
def body(site: Site) -> dict[str, str]:
    return {"site_key": site.site_key}


@pytest.fixture
def ttl(settings: Settings) -> timedelta:
    return timedelta(seconds=settings.session_ttl_s)


@pytest.fixture(autouse=True)
def _in_memory_sessions(
    app: FastAPI,
    repository: InMemorySessionRepository,
    tenant: TenantService,
    clock: FakeClock,
    ttl: timedelta,
) -> None:
    app.dependency_overrides[get_session_service] = lambda: SessionService(
        repository, tenant, ttl=ttl, clock=clock
    )


async def test_new_visitor_gets_a_new_session_in_an_httponly_cookie(
    client: AsyncClient,
    repository: InMemorySessionRepository,
    site: Site,
    body: dict[str, str],
    ttl: timedelta,
) -> None:
    response = await client.post("/v1/sessions", json=body)

    assert response.status_code == 201
    assert response.json() == {"state": "new", "expires_at": "2026-10-24T12:30:00Z"}
    cookie = session_cookie(response)
    assert list(repository.rows) == [cookie.value]
    assert repository.rows[cookie.value].site_id == site.id
    assert cookie["expires"] == format_datetime(NOW + ttl, usegmt=True)
    assert cookie["path"] == "/"
    assert cookie["httponly"]
    assert cookie["secure"]
    assert cookie["samesite"] == "lax"


async def test_cookie_flags_come_from_settings(
    repository: InMemorySessionRepository,
    tenant: TenantService,
    clock: FakeClock,
    body: dict[str, str],
) -> None:
    settings = Settings(env="test", session_cookie_secure=False, session_cookie_samesite="strict")
    app = create_app(settings)
    app.dependency_overrides[get_session_service] = lambda: SessionService(
        repository, tenant, ttl=timedelta(seconds=settings.session_ttl_s), clock=clock
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/sessions", json=body)
    await app.state.engine.dispose()

    cookie = session_cookie(response)
    assert cookie["httponly"]
    assert not cookie["secure"]
    assert cookie["samesite"] == "strict"


async def test_returning_visitor_keeps_the_same_session_and_state(
    client: AsyncClient,
    repository: InMemorySessionRepository,
    clock: FakeClock,
    body: dict[str, str],
) -> None:
    created = await client.post("/v1/sessions", json=body)
    session_id = session_cookie(created).value
    repository.rows[session_id].state = SessionState.CHALLENGE_REQUIRED
    clock.advance(timedelta(minutes=1))

    response = await client.post("/v1/sessions", json=body, headers=with_session(session_id))

    assert response.status_code == 200
    assert response.json() == {
        "state": "challenge_required",
        "expires_at": created.json()["expires_at"],
    }
    assert "set-cookie" not in response.headers
    assert list(repository.rows) == [session_id]


async def test_expired_session_is_replaced_and_its_id_not_reused(
    client: AsyncClient,
    repository: InMemorySessionRepository,
    clock: FakeClock,
    body: dict[str, str],
    ttl: timedelta,
) -> None:
    created = await client.post("/v1/sessions", json=body)
    old_id = session_cookie(created).value
    repository.rows[old_id].state = SessionState.VERIFIED
    clock.advance(ttl)

    response = await client.post("/v1/sessions", json=body, headers=with_session(old_id))

    assert response.status_code == 201
    assert response.json()["state"] == "new"
    new_id = session_cookie(response).value
    assert new_id != old_id
    assert set(repository.rows) == {old_id, new_id}
    assert repository.rows[old_id].state is SessionState.VERIFIED


async def test_unknown_session_id_is_ignored(
    client: AsyncClient, repository: InMemorySessionRepository, body: dict[str, str]
) -> None:
    response = await client.post(
        "/v1/sessions", json=body, headers=with_session("forged-session-id")
    )

    assert response.status_code == 201
    new_id = session_cookie(response).value
    assert new_id != "forged-session-id"
    assert list(repository.rows) == [new_id]


async def test_unknown_site_key_gets_404_and_no_session(
    client: AsyncClient, repository: InMemorySessionRepository
) -> None:
    response = await client.post("/v1/sessions", json={"site_key": "unknown-site-key"})

    assert response.status_code == 404
    assert "set-cookie" not in response.headers
    assert repository.rows == {}


@pytest.mark.parametrize(
    "payload",
    [None, {}, {"site_key": ""}, {"site_key": "x" * 65}, {"site_key": "k", "extra": 1}],
    ids=["no-body", "no-key", "empty-key", "too-long", "extra-field"],
)
async def test_invalid_body_gets_422(
    client: AsyncClient, repository: InMemorySessionRepository, payload: dict[str, object] | None
) -> None:
    response = await client.post("/v1/sessions", json=payload)

    assert response.status_code == 422
    assert repository.rows == {}
