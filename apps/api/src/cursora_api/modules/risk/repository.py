"""Persistence layer of the risk module: database access via SQLAlchemy sessions."""

from sqlalchemy.ext.asyncio import AsyncSession

from cursora_api.modules.risk.models import RiskDecision


class DecisionRepository:
    """Writes ``decisions`` rows."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, decision: RiskDecision) -> None:
        self._db.add(decision)
        await self._db.commit()
