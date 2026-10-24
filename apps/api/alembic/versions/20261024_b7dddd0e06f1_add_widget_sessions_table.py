"""add widget_sessions table

Revision ID: b7dddd0e06f1
Revises:
Create Date: 2026-10-24 21:34:21.897120

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7dddd0e06f1"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "widget_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        # Non-native enum: VARCHAR plus the CHECK constraint below.
        sa.Column(
            "state",
            sa.Enum(
                "new",
                "challenge_required",
                "verified",
                "blocked",
                name="state",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "state IN ('new', 'challenge_required', 'verified', 'blocked')",
            name=op.f("ck_widget_sessions_state"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_widget_sessions")),
    )


def downgrade() -> None:
    op.drop_table("widget_sessions")
