"""integration definitions

Revision ID: e1f6a8b3c9d2
Revises: d5f8a2c9e1b7
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e1f6a8b3c9d2"
down_revision: str | None = "d5f8a2c9e1b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_definitions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_system", sa.String(), nullable=False),
        sa.Column("target_system", sa.String(), nullable=False),
        sa.Column("source_format", sa.String(), nullable=False),
        sa.Column("target_format", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    for column in (
        "code",
        "created_by",
        "source_format",
        "source_system",
        "status",
        "target_format",
        "target_system",
    ):
        op.create_index(f"ix_integration_definitions_{column}", "integration_definitions", [column])


def downgrade() -> None:
    for column in (
        "target_system",
        "target_format",
        "status",
        "source_system",
        "source_format",
        "created_by",
        "code",
    ):
        op.drop_index(f"ix_integration_definitions_{column}", table_name="integration_definitions")
    op.drop_table("integration_definitions")
