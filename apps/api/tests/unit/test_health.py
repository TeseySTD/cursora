from httpx import AsyncClient


async def test_health_is_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_gate_check_stub_allows(client: AsyncClient) -> None:
    response = await client.get("/v1/gate/check")
    assert response.status_code == 204
    assert response.content == b""
