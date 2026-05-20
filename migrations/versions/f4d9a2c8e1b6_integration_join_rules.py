"""integration join rules

Revision ID: f4d9a2c8e1b6
Revises: f3c8e1a6d9b4
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f4d9a2c8e1b6"
down_revision: str | None = "f3c8e1a6d9b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_join_rules",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("definition_id", sa.String(), nullable=False),
        sa.Column("source_schema_document_id", sa.String(), nullable=False),
        sa.Column("left_path", sa.String(), nullable=False),
        sa.Column("right_path", sa.String(), nullable=False),
        sa.Column("operator", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["definition_id"], ["integration_definitions.id"]),
        sa.ForeignKeyConstraint(["source_schema_document_id"], ["integration_schema_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "created_by",
        "definition_id",
        "left_path",
        "operator",
        "right_path",
        "sequence_index",
        "source_schema_document_id",
        "status",
    ):
        op.create_index(f"ix_integration_join_rules_{column}", "integration_join_rules", [column])


def downgrade() -> None:
    for column in (
        "status",
        "source_schema_document_id",
        "sequence_index",
        "right_path",
        "operator",
        "left_path",
        "definition_id",
        "created_by",
    ):
        op.drop_index(f"ix_integration_join_rules_{column}", table_name="integration_join_rules")
    op.drop_table("integration_join_rules")
