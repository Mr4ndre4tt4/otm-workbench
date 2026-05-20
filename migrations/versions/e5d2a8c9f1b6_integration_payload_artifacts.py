"""integration payload artifacts

Revision ID: e5d2a8c9f1b6
Revises: e3b9c7a1d6f4
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e5d2a8c9f1b6"
down_revision: str | None = "e3b9c7a1d6f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_payload_artifacts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("definition_id", sa.String(), nullable=False),
        sa.Column("artifact_id", sa.String(), nullable=False),
        sa.Column("payload_role", sa.String(), nullable=False),
        sa.Column("payload_format", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"]),
        sa.ForeignKeyConstraint(["definition_id"], ["integration_definitions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("artifact_id", "created_by", "definition_id", "payload_format", "payload_role"):
        op.create_index(f"ix_integration_payload_artifacts_{column}", "integration_payload_artifacts", [column])


def downgrade() -> None:
    for column in ("payload_role", "payload_format", "definition_id", "created_by", "artifact_id"):
        op.drop_index(f"ix_integration_payload_artifacts_{column}", table_name="integration_payload_artifacts")
    op.drop_table("integration_payload_artifacts")
