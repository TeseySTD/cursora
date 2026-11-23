"""add sites, signal batches and decisions

Revision ID: e9681b770093
Revises: b7dddd0e06f1
Create Date: 2026-11-23 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e9681b770093"
down_revision: str | Sequence[str] | None = "b7dddd0e06f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("site_key", sa.String(length=64), nullable=False),
        sa.Column("secret_key_hash", sa.String(length=64), nullable=False),
        sa.Column("domain", sa.String(length=253), nullable=False),
        sa.Column("allowed_origins", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("sensitivity", sa.SmallInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("sensitivity BETWEEN 0 AND 100", name=op.f("ck_sites_sensitivity")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sites")),
        sa.UniqueConstraint("site_key", name=op.f("uq_sites_site_key")),
    )

    # Every session now belongs to a site. Existing rows are short-lived sessions created before
    # sites existed and cannot be assigned to one, so they are dropped: their visitors simply get
    # a new session on the next page load.
    op.execute("DELETE FROM widget_sessions")
    op.add_column("widget_sessions", sa.Column("site_id", sa.Integer(), nullable=False))
    op.create_index(
        op.f("ix_widget_sessions_site_id"), "widget_sessions", ["site_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_widget_sessions_site_id_sites"),
        "widget_sessions",
        "sites",
        ["site_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "signal_batches",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        # No foreign key to widget_sessions: batches outlive their session (BR-44).
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("signal_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.id"],
            name=op.f("fk_signal_batches_site_id_sites"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_signal_batches")),
    )
    op.create_index(
        "ix_signal_batches_session_id_received_at",
        "signal_batches",
        ["session_id", "received_at"],
        unique=False,
    )

    op.create_table(
        "decisions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        # No foreign key to widget_sessions: assessments outlive their session (BR-44).
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        # Non-native enum: VARCHAR plus the CHECK constraint below.
        sa.Column(
            "decision",
            sa.Enum("allow", "challenge", "block", name="decision", native_enum=False, length=16),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("ml_score", sa.Float(), nullable=True),
        sa.Column("sensitivity", sa.SmallInteger(), nullable=False),
        sa.Column("ip_prefix", postgresql.CIDR(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "decision IN ('allow', 'challenge', 'block')", name=op.f("ck_decisions_decision")
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.id"],
            name=op.f("fk_decisions_site_id_sites"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decisions")),
    )
    op.create_index(op.f("ix_decisions_session_id"), "decisions", ["session_id"], unique=False)
    op.create_index(
        "ix_decisions_site_id_created_at", "decisions", ["site_id", "created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_decisions_site_id_created_at", table_name="decisions")
    op.drop_index(op.f("ix_decisions_session_id"), table_name="decisions")
    op.drop_table("decisions")
    op.drop_index("ix_signal_batches_session_id_received_at", table_name="signal_batches")
    op.drop_table("signal_batches")
    op.drop_constraint(
        op.f("fk_widget_sessions_site_id_sites"), "widget_sessions", type_="foreignkey"
    )
    op.drop_index(op.f("ix_widget_sessions_site_id"), table_name="widget_sessions")
    op.drop_column("widget_sessions", "site_id")
    op.drop_table("sites")
