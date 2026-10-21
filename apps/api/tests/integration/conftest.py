import pytest
from support.db_guard import ensure_database

from cursora_api.core.config import Settings


@pytest.fixture(autouse=True)
async def _database(settings: Settings) -> None:
    await ensure_database(settings.database_url)
