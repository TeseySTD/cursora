"""Persistence layer of the tenant module: database access via SQLAlchemy sessions."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cursora_api.modules.tenant.models import Site


class SiteRepository:
    """Reads and writes ``sites`` rows."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_site_key(self, site_key: str) -> Site | None:
        result = await self._db.scalars(select(Site).where(Site.site_key == site_key))
        return result.one_or_none()

    async def add(self, site: Site) -> None:
        self._db.add(site)
        await self._db.commit()
