"""integration schema documents

Revision ID: e7c1b2a9d4f8
Revises: e5d2a8c9f1b6
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e7c1b2a9d4f8"
down_revision: str | None = "e5d2a8c9f1b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_schema_documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("definition_id", sa.String(), nullable=False),
        sa.Column("payload_artifact_id", sa.String(), nullable=False),
        sa.Column("payload_format", sa.String(), nullable=False),
        sa.Column("root_name", sa.String(), nullable=False),
        sa.Column("node_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["definition_id"], ["integration_definitions.id"]),
        sa.ForeignKeyConstraint(["payload_artifact_id"], ["integration_payload_artifacts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("created_by", "definition_id", "payload_artifact_id", "payload_format", "status"):
        op.create_index(f"ix_integration_schema_documents_{column}", "integration_schema_documents", [column])

    op.create_table(
        "integration_schema_nodes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("schema_document_id", sa.String(), nullable=False),
        sa.Column("parent_path", sa.String(), nullable=True),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("node_type", sa.String(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["schema_document_id"], ["integration_schema_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("name", "node_type", "parent_path", "path", "schema_document_id", "sequence_index"):
        op.create_index(f"ix_integration_schema_nodes_{column}", "integration_schema_nodes", [column])


def downgrade() -> None:
    for column in ("sequence_index", "schema_document_id", "path", "parent_path", "node_type", "name"):
        op.drop_index(f"ix_integration_schema_nodes_{column}", table_name="integration_schema_nodes")
    op.drop_table("integration_schema_nodes")
    for column in ("status", "payload_format", "payload_artifact_id", "definition_id", "created_by"):
        op.drop_index(f"ix_integration_schema_documents_{column}", table_name="integration_schema_documents")
    op.drop_table("integration_schema_documents")
