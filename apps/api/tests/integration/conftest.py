from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from sqlalchemy import delete
from support.db_guard import ensure_database

from cursora_api.core.config import Settings
from cursora_api.modules.tenant.models import Site
from cursora_api.modules.tenant.service import TenantService


@pytest.fixture(autouse=True)
async def _database(settings: Settings) -> None:
    await ensure_database(settings.database_url)


@pytest.fixture
async def site(app: FastAPI) -> AsyncIterator[Site]:
    """A registered site. Deleting it afterwards cascades to its sessions, signal batches and
    decisions, so reruns start clean."""
    async with app.state.sessionmaker() as db:
        site, _ = await TenantService.for_db(db).create_site("example.com", ["https://example.com"])
    yield site
    async with app.state.sessionmaker() as db:
        await db.execute(delete(Site).where(Site.id == site.id))
        await db.commit()
