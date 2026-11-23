"""POST /v1/sessions/signals over HTTP, with the database replaced by an in-memory repository."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from support.sessions import FakeClock, InMemorySessionRepository, with_session

from cursora_api.core.config import Settings
from cursora_api.modules.sessions.models import SessionState, WidgetSession
from cursora_api.modules.sessions.router import get_signal_service
from cursora_api.modules.sessions.service import SignalLimits, SignalService, new_session_id

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)
SITE_ID = 7
URL = "/v1/sessions/signals"

MOVE = {"type": "move", "t": 120.5, "x": 10, "y": 20.5, "pointer": "mouse"}
CLICK = {"type": "click", "t": 300, "x": 11, "y": 21, "button": 0, "pointer": ""}
ENV = {
    "type": "env",
    "t": 0,
    "viewport": {"width": 1280, "height": 720},
    "devicePixelRatio": 1.5,
    "maxTouchPoints": 0,
    "webdriver": False,
    "cookieEnabled": True,
}


@pytest.fixture
def repository() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture(autouse=True)
def _in_memory_signals(
    app: FastAPI, repository: InMemorySessionRepository, clock: FakeClock, settings: Settings
) -> None:
    limits = SignalLimits(
        max_signals=settings.signal_batch_max_signals,
        rate_max_batches=settings.signal_rate_max_batches,
        rate_window=timedelta(seconds=settings.signal_rate_window_s),
    )
    app.dependency_overrides[get_signal_service] = lambda: SignalService(
        repository, limits=limits, clock=clock
    )


@pytest.fixture
def session(repository: InMemorySessionRepository) -> WidgetSession:
    session = WidgetSession(
        id=new_session_id(),
        site_id=SITE_ID,
        state=SessionState.NEW,
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=30),
        rejected_signal_batches=0,
    )
    repository.rows[session.id] = session
    return session


@pytest.fixture
def cookie(session: WidgetSession) -> dict[str, str]:
    return with_session(session.id)


async def test_batch_is_stored_as_sent_linked_to_the_session(
    client: AsyncClient,
    repository: InMemorySessionRepository,
    session: WidgetSession,
    cookie: dict[str, str],
) -> None:
    batch = {"t": 2000, "signals": [ENV, MOVE, CLICK]}

    response = await client.post(URL, json=batch, headers=cookie)

    assert response.status_code == 204
    [stored] = repository.batches
    assert stored.session_id == session.id
    assert stored.site_id == SITE_ID
    assert stored.received_at == NOW
    assert stored.signal_count == 3
    assert stored.payload == {
        "t": 2000.0,
        "signals": [
            {**ENV, "t": 0.0, "devicePixelRatio": 1.5},
            {**MOVE, "x": 10.0},
            {**CLICK, "t": 300.0, "x": 11.0, "y": 21.0},
        ],
    }
    assert session.rejected_signal_batches == 0


async def test_batch_without_signals_still_carries_time_on_page(
    client: AsyncClient, repository: InMemorySessionRepository, cookie: dict[str, str]
) -> None:
    response = await client.post(URL, json={"t": 15000, "signals": []}, headers=cookie)

    assert response.status_code == 204
    [stored] = repository.batches
    assert stored.payload == {"t": 15000.0, "signals": []}
    assert stored.signal_count == 0


async def test_without_a_cookie_the_batch_is_rejected(
    client: AsyncClient, repository: InMemorySessionRepository
) -> None:
    response = await client.post(URL, json={"t": 1, "signals": [MOVE]})

    assert response.status_code == 401
    assert "set-cookie" not in response.headers
    assert repository.batches == []


async def test_unknown_session_is_rejected(
    client: AsyncClient, repository: InMemorySessionRepository
) -> None:
    response = await client.post(
        URL, json={"t": 1, "signals": [MOVE]}, headers=with_session("forged-session-id")
    )

    assert response.status_code == 401
    assert repository.batches == []


async def test_expired_session_is_rejected(
    client: AsyncClient,
    repository: InMemorySessionRepository,
    clock: FakeClock,
    session: WidgetSession,
    cookie: dict[str, str],
) -> None:
    clock.now = session.expires_at

    response = await client.post(URL, json={"t": 1, "signals": [MOVE]}, headers=cookie)

    assert response.status_code == 401
    assert repository.batches == []


@pytest.mark.parametrize(
    "batch",
    [
        {"t": 1, "signals": [{**MOVE, "value": "hunter2"}]},
        {"t": 1, "signals": [{"type": "key", "t": 1, "key": "a"}]},
        {"t": 1, "signals": [{**ENV, "language": "uk-UA", "timezone": "Europe/Kyiv"}]},
        {"t": 1, "signals": [], "text": "typed by the visitor"},
        {"t": 1, "signals": [{**MOVE, "pointer": "robot"}]},
        {"t": -1, "signals": []},
        {"signals": []},
    ],
    ids=[
        "form-value",
        "keystroke",
        "fingerprint-attributes",
        "extra-batch-field",
        "unknown-pointer",
        "negative-time",
        "no-time",
    ],
)
async def test_batch_with_anything_beyond_the_schema_is_rejected(
    client: AsyncClient,
    repository: InMemorySessionRepository,
    session: WidgetSession,
    cookie: dict[str, str],
    batch: dict[str, Any],
) -> None:
    response = await client.post(URL, json=batch, headers=cookie)

    assert response.status_code == 422
    assert all(error["loc"][0] == "body" for error in response.json()["detail"])
    assert repository.batches == []
    # Not too large or too frequent, so not a request signal.
    assert session.rejected_signal_batches == 0


async def test_invalid_json_is_rejected(
    client: AsyncClient, repository: InMemorySessionRepository, cookie: dict[str, str]
) -> None:
    response = await client.post(
        URL, content=b"{not json", headers={**cookie, "Content-Type": "application/json"}
    )

    assert response.status_code == 422
    assert repository.batches == []


def _oversized_batch(settings: Settings) -> bytes:
    # Valid JSON of the right shape, only too long.
    body = json.dumps({"t": 1, "signals": [MOVE] * 1000}).encode()
    assert len(body) > settings.signal_batch_max_bytes
    return body


async def test_oversized_batch_is_rejected_and_counted(
    client: AsyncClient,
    repository: InMemorySessionRepository,
    session: WidgetSession,
    cookie: dict[str, str],
    settings: Settings,
) -> None:
    response = await client.post(
        URL,
        content=_oversized_batch(settings),
        headers={**cookie, "Content-Type": "application/json"},
    )

    assert response.status_code == 413
    assert repository.batches == []
    assert session.rejected_signal_batches == 1


async def test_oversized_batch_without_content_length_is_rejected(
    client: AsyncClient,
    repository: InMemorySessionRepository,
    session: WidgetSession,
    cookie: dict[str, str],
    settings: Settings,
) -> None:
    body = _oversized_batch(settings)

    async def chunks() -> AsyncIterator[bytes]:
        for start in range(0, len(body), 4096):
            yield body[start : start + 4096]

    response = await client.post(
        URL, content=chunks(), headers={**cookie, "Content-Type": "application/json"}
    )

    assert response.request.headers.get("content-length") is None
    assert response.status_code == 413
    assert repository.batches == []
    assert session.rejected_signal_batches == 1


async def test_batch_with_too_many_signals_is_rejected_and_counted(
    client: AsyncClient,
    repository: InMemorySessionRepository,
    session: WidgetSession,
    cookie: dict[str, str],
    settings: Settings,
) -> None:
    # Small signals: under the byte limit, over the signal count limit.
    signal = {"type": "move", "t": 1, "x": 1, "y": 1, "pointer": ""}
    batch = {"t": 1, "signals": [signal] * (settings.signal_batch_max_signals + 1)}
    assert len(json.dumps(batch)) <= settings.signal_batch_max_bytes

    response = await client.post(URL, json=batch, headers=cookie)

    assert response.status_code == 413
    assert repository.batches == []
    assert session.rejected_signal_batches == 1


async def test_too_frequent_batches_are_rejected_and_counted(
    client: AsyncClient,
    repository: InMemorySessionRepository,
    clock: FakeClock,
    session: WidgetSession,
    cookie: dict[str, str],
    settings: Settings,
) -> None:
    batch = {"t": 1, "signals": [MOVE]}
    for _ in range(settings.signal_rate_max_batches):
        assert (await client.post(URL, json=batch, headers=cookie)).status_code == 204
        clock.advance(timedelta(milliseconds=100))

    response = await client.post(URL, json=batch, headers=cookie)

    assert response.status_code == 429
    assert response.headers["retry-after"] == str(settings.signal_rate_window_s)
    assert len(repository.batches) == settings.signal_rate_max_batches
    assert session.rejected_signal_batches == 1

    # Once the window has moved past the earlier batches, batches are accepted again.
    clock.advance(timedelta(seconds=settings.signal_rate_window_s))
    assert (await client.post(URL, json=batch, headers=cookie)).status_code == 204


async def test_rate_limit_is_per_session(
    client: AsyncClient,
    repository: InMemorySessionRepository,
    session: WidgetSession,
    cookie: dict[str, str],
    settings: Settings,
) -> None:
    batch = {"t": 1, "signals": []}
    for _ in range(settings.signal_rate_max_batches):
        await client.post(URL, json=batch, headers=cookie)
    other = WidgetSession(
        id=new_session_id(),
        site_id=SITE_ID,
        state=SessionState.NEW,
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=30),
        rejected_signal_batches=0,
    )
    repository.rows[other.id] = other

    response = await client.post(URL, json=batch, headers=with_session(other.id))

    assert response.status_code == 204


def test_request_body_is_typed_in_the_contract(app: FastAPI) -> None:
    body = app.openapi()["paths"][URL]["post"]["requestBody"]

    schema = body["content"]["application/json"]["schema"]
    assert body["required"]
    assert set(schema["properties"]) == {"t", "signals"}
    assert "$ref" not in json.dumps(body)
