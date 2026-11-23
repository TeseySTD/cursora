"""ORM models of the sessions module (subclasses of cursora_api.core.db.Base)."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Identity, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from cursora_api.core.db import Base

# Length of the session id column; ids from ``new_session_id`` are 43 characters.
SESSION_ID_MAX_LENGTH = 64


class SessionState(StrEnum):
    NEW = "new"
    CHALLENGE_REQUIRED = "challenge_required"
    VERIFIED = "verified"
    BLOCKED = "blocked"


class WidgetSession(Base):
    """Server-side widget session: the source of truth for a visitor's state.

    The id is an opaque random token that is also the session cookie value. Rows are never
    reused: an expired session stays in the table, so its id can never belong to another one.
    Every session belongs to exactly one site (BR-4).

    TODO(team): rate limit for anonymous creation and retention of expired rows.
    """

    __tablename__ = "widget_sessions"

    id: Mapped[str] = mapped_column(String(SESSION_ID_MAX_LENGTH), primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    state: Mapped[SessionState] = mapped_column(
        # VARCHAR + CHECK instead of a native enum. Autogenerate does not detect a new state: add
        # it with a manual migration that drops and recreates ck_widget_sessions_state.
        Enum(
            SessionState,
            name="state",
            native_enum=False,
            create_constraint=True,
            length=32,
            values_callable=lambda states: [state.value for state in states],
        )
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Signal batches rejected as too large or too frequent: a request signal for the Risk Engine.
    rejected_signal_batches: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class SignalBatch(Base):
    """One batch of behavioural signals sent by the widget, stored as JSONB (BR-6).

    ``session_id`` is a plain column without a foreign key: raw signals are kept for 30 days,
    longer than the session row they belong to, and must stay grouped after it is deleted
    (BR-44).

    TODO(team): the daily clean-up of batches older than 30 days (BR-44).
    """

    __tablename__ = "signal_batches"
    # Per-session reads, newest last.
    __table_args__ = (
        Index("ix_signal_batches_session_id_received_at", "session_id", "received_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(SESSION_ID_MAX_LENGTH))
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    signal_count: Mapped[int] = mapped_column(Integer)
