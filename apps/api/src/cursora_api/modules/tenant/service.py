"""Service layer of the tenant module: use cases and business logic."""

import hashlib
import secrets
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

# Re-exported: other modules size their fields by it without importing tenant models.
from cursora_api.modules.tenant.models import SITE_KEY_MAX_LENGTH as SITE_KEY_MAX_LENGTH
from cursora_api.modules.tenant.models import Site
from cursora_api.modules.tenant.repository import SiteRepository

# 16 random bytes = 22 URL-safe characters: public, only has to be unguessable enough to be unique.
SITE_KEY_BYTES = 16
# 32 random bytes = 256 bits, like session ids: the secret authenticates the site's backend.
SECRET_KEY_BYTES = 32


def new_site_key() -> str:
    return secrets.token_urlsafe(SITE_KEY_BYTES)


def new_secret_key() -> str:
    return secrets.token_urlsafe(SECRET_KEY_BYTES)


def hash_secret_key(secret_key: str) -> str:
    """Hash under which a secret key is stored.

    A plain SHA-256 is enough: the secret is 256 random bits, so there is nothing to brute-force
    and no need for a slow password hash.
    """
    return hashlib.sha256(secret_key.encode()).hexdigest()


def utc_now() -> datetime:
    return datetime.now(UTC)


class TenantService:
    def __init__(
        self, repository: SiteRepository, *, clock: Callable[[], datetime] = utc_now
    ) -> None:
        self._repository = repository
        self._clock = clock

    @classmethod
    def for_db(cls, db: AsyncSession) -> Self:
        """The service on a request's database session, for other modules' dependencies."""
        return cls(SiteRepository(db))

    async def create_site(self, domain: str, allowed_origins: Sequence[str]) -> tuple[Site, str]:
        """Register a site. Returns ``(site, secret_key)``: the secret is never stored or shown
        again, only its hash is kept."""
        secret_key = new_secret_key()
        site = Site(
            site_key=new_site_key(),
            secret_key_hash=hash_secret_key(secret_key),
            domain=domain,
            allowed_origins=list(allowed_origins),
            sensitivity=None,
            created_at=self._clock(),
        )
        await self._repository.add(site)
        return site, secret_key

    async def find_by_site_key(self, site_key: str) -> Site | None:
        return await self._repository.get_by_site_key(site_key)
