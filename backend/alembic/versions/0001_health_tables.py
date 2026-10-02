"""Health tables (weight_entries, weight_goals).

This revision matches EXACTLY what the original app created with
Base.metadata.create_all(). If your database already has these two
tables (from the pre-Alembic version of LifeOps), do NOT run this
revision; mark it as applied instead:

    alembic stamp 0001_health_tables
    alembic upgrade head

Revision ID: 0001_health_tables
Revises:
Create Date: 2026-10-01
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_health_tables"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "weight_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("measurement_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_weight_entries_id"), "weight_entries", ["id"], unique=False
    )

    op.create_table(
        "weight_goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("starting_weight", sa.Float(), nullable=False),
        sa.Column("goal_weight", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_weight_goals_id"), "weight_goals", ["id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_weight_goals_id"), table_name="weight_goals")
    op.drop_table("weight_goals")
    op.drop_index(op.f("ix_weight_entries_id"), table_name="weight_entries")
    op.drop_table("weight_entries")
