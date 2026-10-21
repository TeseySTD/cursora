"""Proves the REQUIRE_DB contract of the integration-test guard."""

import pytest
from support.db_guard import ensure_database

# Port 1 on loopback: nothing listens there, so the connection is refused fast.
UNREACHABLE = "postgresql+asyncpg://nobody:nothing@127.0.0.1:1/none"


async def test_unreachable_db_skips_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REQUIRE_DB", raising=False)
    with pytest.raises(pytest.skip.Exception):
        await ensure_database(UNREACHABLE, timeout_s=1)


async def test_unreachable_db_fails_when_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REQUIRE_DB", "1")
    with pytest.raises(pytest.fail.Exception, match="REQUIRE_DB=1"):
        await ensure_database(UNREACHABLE, timeout_s=1)
