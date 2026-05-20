"""integration systems

Revision ID: e3b9c7a1d6f4
Revises: e1f6a8b3c9d2
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e3b9c7a1d6f4"
down_revision: str | None = "e1f6a8b3c9d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_systems",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("system_type", sa.String(), nullable=False),
        sa.Column("base_url", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    for column in ("code", "created_by", "status", "system_type"):
        op.create_index(f"ix_integration_systems_{column}", "integration_systems", [column])

    op.create_table(
        "integration_endpoints",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("system_id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("payload_format", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["system_id"], ["integration_systems.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("code", "created_by", "method", "payload_format", "status", "system_id"):
        op.create_index(f"ix_integration_endpoints_{column}", "integration_endpoints", [column])


def downgrade() -> None:
    for column in ("system_id", "status", "payload_format", "method", "created_by", "code"):
        op.drop_index(f"ix_integration_endpoints_{column}", table_name="integration_endpoints")
    op.drop_table("integration_endpoints")
    for column in ("system_type", "status", "created_by", "code"):
        op.drop_index(f"ix_integration_systems_{column}", table_name="integration_systems")
    op.drop_table("integration_systems")
