"""integration transform types

Revision ID: f1a6c8d2e9b4
Revises: e9f4a1c7b2d6
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f1a6c8d2e9b4"
down_revision: str | None = "e9f4a1c7b2d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_transform_types",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requires_expression", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("system_seeded", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    for column in ("code", "requires_expression", "sequence_index", "status"):
        op.create_index(f"ix_integration_transform_types_{column}", "integration_transform_types", [column])


def downgrade() -> None:
    for column in ("status", "sequence_index", "requires_expression", "code"):
        op.drop_index(f"ix_integration_transform_types_{column}", table_name="integration_transform_types")
    op.drop_table("integration_transform_types")
