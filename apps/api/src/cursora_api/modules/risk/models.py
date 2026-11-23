"""ORM models of the risk module (subclasses of cursora_api.core.db.Base)."""

from datetime import datetime
from ipaddress import IPv4Network, IPv6Network

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Identity,
    Index,
    SmallInteger,
    String,
)
from sqlalchemy.dialects.postgresql import CIDR
from sqlalchemy.orm import Mapped, mapped_column

from cursora_api.core.db import Base
from cursora_api.modules.risk.evaluator import Decision

# Same length as the session id column in the sessions module.
SESSION_ID_MAX_LENGTH = 64


class RiskDecision(Base):
    """One Risk Engine assessment of a session: score and initial decision (BR-6, BR-9).

    ``session_id`` is a plain column without a foreign key: assessments are kept for 14 months,
    far longer than the session row, and must stay grouped after it is deleted (BR-44). The
    client IP is kept only as its /24 (IPv4) or /48 (IPv6) prefix, never in full (BR-44).

    TODO(team): the score range and how rules and the ML score combine (OQ-16); rule evidence
    and model version (FR-20, Proposed); the daily clean-up after 14 months (BR-44).
    """

    __tablename__ = "decisions"
    __table_args__ = (Index("ix_decisions_site_id_created_at", "site_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(SESSION_ID_MAX_LENGTH), index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    decision: Mapped[Decision] = mapped_column(
        # VARCHAR + CHECK instead of a native enum, like the session state.
        Enum(
            Decision,
            name="decision",
            native_enum=False,
            create_constraint=True,
            length=16,
            values_callable=lambda decisions: [decision.value for decision in decisions],
        )
    )
    score: Mapped[float] = mapped_column(Float)
    ml_score: Mapped[float | None] = mapped_column(Float)
    # The sensitivity in force when the decision was made.
    sensitivity: Mapped[int] = mapped_column(SmallInteger)
    # asyncpg maps CIDR to ipaddress networks.
    ip_prefix: Mapped[IPv4Network | IPv6Network | None] = mapped_column(CIDR)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
