"""ORM models of the sessions module (subclasses of cursora_api.core.db.Base)."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, String
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

    TODO(team): link the session to a site once the tenant module defines sites.
    """

    __tablename__ = "widget_sessions"

    id: Mapped[str] = mapped_column(String(SESSION_ID_MAX_LENGTH), primary_key=True)
    state: Mapped[SessionState] = mapped_column(
        # VARCHAR + CHECK instead of a native enum: adding a state is a one-line migration.
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
