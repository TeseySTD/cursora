"""Register a site for local development and print its keys.

There is no admin API for sites yet; this stands in for it. The secret key is printed once and
only its hash is stored, so copy it now.

Usage: pnpm api:create-site --domain localhost --origin http://localhost:5174
"""

import argparse
import asyncio

from cursora_api.core.config import get_settings
from cursora_api.core.db import create_engine, create_sessionmaker
from cursora_api.modules.tenant.service import TenantService


async def create_site(domain: str, origins: list[str]) -> None:
    engine = create_engine(get_settings())
    try:
        async with create_sessionmaker(engine)() as db:
            site, secret_key = await TenantService.for_db(db).create_site(domain, origins)
    finally:
        await engine.dispose()
    print(f"site key:   {site.site_key}")
    print(f"secret key: {secret_key}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Register a site for local development.")
    parser.add_argument("--domain", required=True, help="the site's domain, e.g. example.com")
    parser.add_argument(
        "--origin",
        action="append",
        default=[],
        dest="origins",
        help="an allowed request origin, e.g. https://example.com (repeatable)",
    )
    args = parser.parse_args()
    asyncio.run(create_site(args.domain, args.origins))


if __name__ == "__main__":
    main()
