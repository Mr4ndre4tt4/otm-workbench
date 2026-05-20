"""integration mappings

Revision ID: e9f4a1c7b2d6
Revises: e7c1b2a9d4f8
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e9f4a1c7b2d6"
down_revision: str | None = "e7c1b2a9d4f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_mappings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("definition_id", sa.String(), nullable=False),
        sa.Column("source_schema_document_id", sa.String(), nullable=False),
        sa.Column("target_schema_document_id", sa.String(), nullable=False),
        sa.Column("source_path", sa.String(), nullable=False),
        sa.Column("target_path", sa.String(), nullable=False),
        sa.Column("transform_type", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["definition_id"], ["integration_definitions.id"]),
        sa.ForeignKeyConstraint(["source_schema_document_id"], ["integration_schema_documents.id"]),
        sa.ForeignKeyConstraint(["target_schema_document_id"], ["integration_schema_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "created_by",
        "definition_id",
        "sequence_index",
        "source_path",
        "source_schema_document_id",
        "status",
        "target_path",
        "target_schema_document_id",
        "transform_type",
    ):
        op.create_index(f"ix_integration_mappings_{column}", "integration_mappings", [column])


def downgrade() -> None:
    for column in (
        "transform_type",
        "target_schema_document_id",
        "target_path",
        "status",
        "source_schema_document_id",
        "source_path",
        "sequence_index",
        "definition_id",
        "created_by",
    ):
        op.drop_index(f"ix_integration_mappings_{column}", table_name="integration_mappings")
    op.drop_table("integration_mappings")
