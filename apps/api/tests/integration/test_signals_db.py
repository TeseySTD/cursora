"""Signal ingestion against a real PostgreSQL."""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select, text
from support.sessions import session_cookie, with_session

from cursora_api.core.config import Settings
from cursora_api.modules.sessions.models import SignalBatch, WidgetSession
from cursora_api.modules.tenant.models import Site

pytestmark = pytest.mark.integration

URL = "/v1/sessions/signals"
MOVE = {"type": "move", "t": 120.5, "x": 10, "y": 20, "pointer": "mouse"}


async def _open_session(client: AsyncClient, site: Site) -> str:
    response = await client.post("/v1/sessions", json={"site_key": site.site_key})
    assert response.status_code == 201
    return session_cookie(response).value


async def test_batch_is_stored_as_jsonb_linked_to_the_session(
    client: AsyncClient, app: FastAPI, site: Site
) -> None:
    session_id = await _open_session(client, site)

    response = await client.post(
        URL, json={"t": 2000, "signals": [MOVE]}, headers=with_session(session_id)
    )

    assert response.status_code == 204
    async with app.state.sessionmaker() as db:
        [batch] = (
            await db.scalars(select(SignalBatch).where(SignalBatch.session_id == session_id))
        ).all()
        pointer = await db.scalar(
            text(
                "SELECT payload -> 'signals' -> 0 ->> 'pointer' FROM signal_batches WHERE id = :id"
            ),
            {"id": batch.id},
        )
    assert batch.site_id == site.id
    assert batch.signal_count == 1
    assert batch.payload["t"] == 2000
    assert pointer == "mouse"


async def test_rate_limit_counts_stored_batches_and_rejections(
    client: AsyncClient, app: FastAPI, site: Site, settings: Settings
) -> None:
    session_id = await _open_session(client, site)
    headers = with_session(session_id)
    batch = {"t": 1, "signals": []}

    statuses = [
        (await client.post(URL, json=batch, headers=headers)).status_code
        for _ in range(settings.signal_rate_max_batches + 2)
    ]

    assert statuses == [204] * settings.signal_rate_max_batches + [429, 429]
    async with app.state.sessionmaker() as db:
        stored = await db.scalar(
            text("SELECT count(*) FROM signal_batches WHERE session_id = :id"), {"id": session_id}
        )
        session = await db.get(WidgetSession, session_id)
    assert stored == settings.signal_rate_max_batches
    assert session is not None
    assert session.rejected_signal_batches == 2


async def test_new_sessions_start_with_no_rejected_batches(
    client: AsyncClient, app: FastAPI, site: Site
) -> None:
    session_id = await _open_session(client, site)

    async with app.state.sessionmaker() as db:
        stored = await db.scalar(
            text("SELECT rejected_signal_batches FROM widget_sessions WHERE id = :id"),
            {"id": session_id},
        )
    assert stored == 0
