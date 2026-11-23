"""Test doubles for the tenant module."""

from cursora_api.modules.tenant.models import Site
from cursora_api.modules.tenant.repository import SiteRepository


class InMemorySiteRepository(SiteRepository):
    """Keeps sites in a dict instead of the database, assigning ids like the identity column."""

    def __init__(self) -> None:
        self.rows: dict[int, Site] = {}

    async def get_by_site_key(self, site_key: str) -> Site | None:
        return next((site for site in self.rows.values() if site.site_key == site_key), None)

    async def add(self, site: Site) -> None:
        assert await self.get_by_site_key(site.site_key) is None, "unique violation: site_key"
        site.id = len(self.rows) + 1
        self.rows[site.id] = site
