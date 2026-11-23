import hashlib
from datetime import UTC, datetime

import pytest
from support.sessions import FakeClock
from support.tenant import InMemorySiteRepository

from cursora_api.modules.tenant.service import TenantService

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)


@pytest.fixture
def repository() -> InMemorySiteRepository:
    return InMemorySiteRepository()


@pytest.fixture
def service(repository: InMemorySiteRepository) -> TenantService:
    return TenantService(repository, clock=FakeClock(NOW))


async def test_create_site_stores_only_the_secret_hash(
    service: TenantService, repository: InMemorySiteRepository
) -> None:
    site, secret_key = await service.create_site("example.com", ["https://example.com"])

    assert repository.rows == {site.id: site}
    assert site.domain == "example.com"
    assert site.allowed_origins == ["https://example.com"]
    assert site.sensitivity is None
    assert site.created_at == NOW
    assert site.secret_key_hash == hashlib.sha256(secret_key.encode()).hexdigest()
    assert secret_key not in vars(site).values()


async def test_every_site_gets_its_own_keys(service: TenantService) -> None:
    sites = [await service.create_site("example.com", []) for _ in range(50)]

    assert len({site.site_key for site, _ in sites}) == 50
    assert len({secret for _, secret in sites}) == 50
    assert not {site.site_key for site, _ in sites} & {secret for _, secret in sites}


async def test_find_by_site_key(service: TenantService) -> None:
    site, _ = await service.create_site("example.com", [])

    assert await service.find_by_site_key(site.site_key) is site
    assert await service.find_by_site_key("unknown") is None
