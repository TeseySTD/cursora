"""Constraints and column types of the sites, signal_batches and decisions tables."""

from datetime import UTC, datetime
from ipaddress import IPv4Network, IPv6Network

import pytest
from fastapi import FastAPI
from sqlalchemy import delete, select, text, update
from sqlalchemy.exc import IntegrityError

from cursora_api.modules.risk.evaluator import Decision
from cursora_api.modules.risk.models import RiskDecision
from cursora_api.modules.sessions.models import SignalBatch
from cursora_api.modules.sessions.service import new_session_id
from cursora_api.modules.tenant.models import Site

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)


async def test_signal_batch_payload_round_trips_as_jsonb(app: FastAPI, site: Site) -> None:
    payload = {"t": 2000.5, "signals": [{"type": "move", "t": 1.5, "x": 10, "y": 20}]}
    batch = SignalBatch(
        session_id=new_session_id(),
        site_id=site.id,
        received_at=NOW,
        payload=payload,
        signal_count=1,
    )
    async with app.state.sessionmaker() as db:
        db.add(batch)
        await db.commit()

    async with app.state.sessionmaker() as db:
        stored = await db.get(SignalBatch, batch.id)
        column_type = await db.scalar(
            text("SELECT jsonb_typeof(payload -> 'signals') FROM signal_batches WHERE id = :id"),
            {"id": batch.id},
        )
    assert stored is not None
    assert stored.payload == payload
    assert column_type == "array"


async def test_signal_batches_outlive_their_session(app: FastAPI, site: Site) -> None:
    # No foreign key to widget_sessions (BR-44): a batch of a deleted or never-seen session id
    # is accepted by the database.
    async with app.state.sessionmaker() as db:
        db.add(
            SignalBatch(
                session_id="not-a-session",
                site_id=site.id,
                received_at=NOW,
                payload={},
                signal_count=0,
            )
        )
        await db.commit()


@pytest.mark.parametrize(
    "prefix", [IPv4Network("203.0.113.0/24"), IPv6Network("2001:db8:1::/48")], ids=["v4", "v6"]
)
async def test_decision_is_stored_with_an_ip_prefix(
    app: FastAPI, site: Site, prefix: IPv4Network | IPv6Network
) -> None:
    decision = RiskDecision(
        session_id=new_session_id(),
        site_id=site.id,
        decision=Decision.CHALLENGE,
        score=0.5,
        ml_score=None,
        sensitivity=50,
        ip_prefix=prefix,
        created_at=NOW,
    )
    async with app.state.sessionmaker() as db:
        db.add(decision)
        await db.commit()

    async with app.state.sessionmaker() as db:
        stored = await db.get(RiskDecision, decision.id)
        raw = await db.scalar(
            text("SELECT decision FROM decisions WHERE id = :id"), {"id": decision.id}
        )
    assert stored is not None
    assert stored.decision is Decision.CHALLENGE
    assert stored.ip_prefix == prefix
    # The enum's value (not its name) is what lands in the column.
    assert raw == "challenge"


async def test_decisions_reject_an_unknown_decision(app: FastAPI, site: Site) -> None:
    async with app.state.sessionmaker() as db:
        with pytest.raises(IntegrityError, match="ck_decisions_decision"):
            await db.execute(
                text(
                    "INSERT INTO decisions (session_id, site_id, decision, score, sensitivity,"
                    " created_at) VALUES ('s', :site_id, 'maybe', 0, 0, now())"
                ),
                {"site_id": site.id},
            )


@pytest.mark.parametrize("sensitivity", [-1, 101])
async def test_site_sensitivity_must_be_0_to_100(
    app: FastAPI, site: Site, sensitivity: int
) -> None:
    async with app.state.sessionmaker() as db:
        with pytest.raises(IntegrityError, match="ck_sites_sensitivity"):
            await db.execute(update(Site).where(Site.id == site.id).values(sensitivity=sensitivity))


async def test_site_keys_are_unique(app: FastAPI, site: Site) -> None:
    duplicate = Site(
        site_key=site.site_key,
        secret_key_hash="0" * 64,
        domain="other.example",
        allowed_origins=[],
        created_at=NOW,
    )
    async with app.state.sessionmaker() as db:
        db.add(duplicate)
        with pytest.raises(IntegrityError, match="uq_sites_site_key"):
            await db.commit()


async def test_deleting_a_site_deletes_its_rows(app: FastAPI, site: Site) -> None:
    async with app.state.sessionmaker() as db:
        db.add(
            SignalBatch(
                session_id="s", site_id=site.id, received_at=NOW, payload={}, signal_count=0
            )
        )
        await db.commit()
        await db.execute(delete(Site).where(Site.id == site.id))
        await db.commit()
        left = await db.scalars(select(SignalBatch.id).where(SignalBatch.site_id == site.id))
    assert left.all() == []
