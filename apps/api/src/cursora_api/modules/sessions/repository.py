"""Persistence layer of the sessions module: database access via SQLAlchemy sessions."""

from sqlalchemy.ext.asyncio import AsyncSession

from cursora_api.modules.sessions.models import WidgetSession


class SessionRepository:
    """Reads and writes ``widget_sessions`` rows."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, session_id: str) -> WidgetSession | None:
        return await self._db.get(WidgetSession, session_id)

    async def add(self, session: WidgetSession) -> None:
        self._db.add(session)
        await self._db.commit()
