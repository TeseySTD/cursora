"""count rejected signal batches

Revision ID: 98f5239bcdab
Revises: e9681b770093
Create Date: 2026-11-23 18:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "98f5239bcdab"
down_revision: str | Sequence[str] | None = "e9681b770093"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "widget_sessions",
        sa.Column("rejected_signal_batches", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("widget_sessions", "rejected_signal_batches")
