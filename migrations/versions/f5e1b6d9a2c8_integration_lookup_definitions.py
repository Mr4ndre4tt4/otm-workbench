"""integration lookup definitions

Revision ID: f5e1b6d9a2c8
Revises: f4d9a2c8e1b6
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f5e1b6d9a2c8"
down_revision: str | None = "f4d9a2c8e1b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_lookup_definitions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("definition_id", sa.String(), nullable=False),
        sa.Column("source_schema_document_id", sa.String(), nullable=False),
        sa.Column("target_schema_document_id", sa.String(), nullable=False),
        sa.Column("input_path", sa.String(), nullable=False),
        sa.Column("output_path", sa.String(), nullable=False),
        sa.Column("lookup_type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("mock_response_json", sa.Text(), nullable=False),
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
        "input_path",
        "lookup_type",
        "output_path",
        "sequence_index",
        "source_schema_document_id",
        "status",
        "target_schema_document_id",
    ):
        op.create_index(f"ix_integration_lookup_definitions_{column}", "integration_lookup_definitions", [column])


def downgrade() -> None:
    for column in (
        "target_schema_document_id",
        "status",
        "source_schema_document_id",
        "sequence_index",
        "output_path",
        "lookup_type",
        "input_path",
        "definition_id",
        "created_by",
    ):
        op.drop_index(f"ix_integration_lookup_definitions_{column}", table_name="integration_lookup_definitions")
    op.drop_table("integration_lookup_definitions")
