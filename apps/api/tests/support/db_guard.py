"""Decides whether integration tests run, skip or fail, based on DB reachability.

- Database reachable            -> tests run.
- Unreachable, REQUIRE_DB unset -> tests are skipped (local dev without Postgres).
- Unreachable, REQUIRE_DB=1     -> tests FAIL (CI must never silently skip them).
"""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


def require_db_enabled() -> bool:
    return os.environ.get("REQUIRE_DB", "").strip() == "1"


async def ensure_database(url: str, timeout_s: float = 3.0) -> None:
    engine = create_async_engine(url, connect_args={"timeout": timeout_s})
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        reason = f"database not reachable at {engine.url.render_as_string()}: {exc!r}"
        if require_db_enabled():
            pytest.fail(f"REQUIRE_DB=1 but {reason}", pytrace=False)
        pytest.skip(reason)
    finally:
        await engine.dispose()
