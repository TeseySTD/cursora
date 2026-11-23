"""Persistence layer of the sessions module: database access via SQLAlchemy sessions."""

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from cursora_api.modules.sessions.models import SignalBatch, WidgetSession


class SessionRepository:
    """Reads and writes ``widget_sessions`` and ``signal_batches`` rows."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, session_id: str) -> WidgetSession | None:
        return await self._db.get(WidgetSession, session_id)

    async def add(self, session: WidgetSession) -> None:
        self._db.add(session)
        await self._db.commit()

    async def count_batches_since(self, session_id: str, since: datetime) -> int:
        count = await self._db.scalar(
            select(func.count())
            .select_from(SignalBatch)
            .where(SignalBatch.session_id == session_id, SignalBatch.received_at > since)
        )
        return count or 0

    async def add_batch(self, batch: SignalBatch) -> None:
        self._db.add(batch)
        await self._db.commit()

    async def increment_rejected_batches(self, session_id: str) -> None:
        # One atomic UPDATE: concurrent rejections of the same session are all counted.
        await self._db.execute(
            update(WidgetSession)
            .where(WidgetSession.id == session_id)
            .values(rejected_signal_batches=WidgetSession.rejected_signal_batches + 1)
        )
        await self._db.commit()
