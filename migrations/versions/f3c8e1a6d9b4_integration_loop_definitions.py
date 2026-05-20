"""integration loop definitions

Revision ID: f3c8e1a6d9b4
Revises: f1a6c8d2e9b4
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f3c8e1a6d9b4"
down_revision: str | None = "f1a6c8d2e9b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_loop_definitions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("definition_id", sa.String(), nullable=False),
        sa.Column("source_schema_document_id", sa.String(), nullable=False),
        sa.Column("target_schema_document_id", sa.String(), nullable=False),
        sa.Column("source_collection_path", sa.String(), nullable=False),
        sa.Column("target_collection_path", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
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
        "source_collection_path",
        "source_schema_document_id",
        "status",
        "target_collection_path",
        "target_schema_document_id",
    ):
        op.create_index(f"ix_integration_loop_definitions_{column}", "integration_loop_definitions", [column])


def downgrade() -> None:
    for column in (
        "target_schema_document_id",
        "target_collection_path",
        "status",
        "source_schema_document_id",
        "source_collection_path",
        "sequence_index",
        "definition_id",
        "created_by",
    ):
        op.drop_index(f"ix_integration_loop_definitions_{column}", table_name="integration_loop_definitions")
    op.drop_table("integration_loop_definitions")
