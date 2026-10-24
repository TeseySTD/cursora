from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import delete, text
from support.sessions import session_cookie, with_session

from cursora_api.modules.sessions.models import SessionState, WidgetSession
from cursora_api.modules.sessions.service import new_session_id

pytestmark = pytest.mark.integration


@pytest.fixture
async def session_ids(app: FastAPI) -> AsyncIterator[list[str]]:
    """Ids of the rows a test touched; deleted afterwards so reruns start clean."""
    ids: list[str] = []
    yield ids
    async with app.state.sessionmaker() as db:
        await db.execute(delete(WidgetSession).where(WidgetSession.id.in_(ids)))
        await db.commit()


async def test_session_is_created_then_reused(
    client: AsyncClient, app: FastAPI, session_ids: list[str]
) -> None:
    created = await client.post("/v1/sessions")
    assert created.status_code == 201
    session_id = session_cookie(created).value
    session_ids.append(session_id)

    reused = await client.post("/v1/sessions", headers=with_session(session_id))

    assert reused.status_code == 200
    assert reused.json() == created.json()
    async with app.state.sessionmaker() as db:
        # The enum's value (not its name) is what lands in the column.
        stored = await db.scalar(
            text("SELECT state FROM widget_sessions WHERE id = :id"), {"id": session_id}
        )
    assert stored == "new"


async def test_expired_session_is_replaced(
    client: AsyncClient, app: FastAPI, session_ids: list[str]
) -> None:
    now = datetime.now(UTC)
    expired = WidgetSession(
        id=new_session_id(),
        state=SessionState.VERIFIED,
        created_at=now - timedelta(days=2),
        expires_at=now - timedelta(days=1),
    )
    session_ids.append(expired.id)
    async with app.state.sessionmaker() as db:
        db.add(expired)
        await db.commit()

    response = await client.post("/v1/sessions", headers=with_session(expired.id))

    assert response.status_code == 201
    new_id = session_cookie(response).value
    session_ids.append(new_id)
    assert new_id != expired.id
    async with app.state.sessionmaker() as db:
        old = await db.get(WidgetSession, expired.id)
        new = await db.get(WidgetSession, new_id)
    assert old is not None and old.state is SessionState.VERIFIED
    assert new is not None and new.state is SessionState.NEW
