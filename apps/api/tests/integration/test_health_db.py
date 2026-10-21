import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_health_db_runs_select_1(client: AsyncClient) -> None:
    response = await client.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
