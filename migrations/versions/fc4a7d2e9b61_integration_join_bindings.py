"""integration join bindings

Revision ID: fc4a7d2e9b61
Revises: fb3a6d8c1e92
Create Date: 2026-05-25 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "fc4a7d2e9b61"
down_revision: str | None = "fb3a6d8c1e92"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_join_bindings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("definition_id", sa.String(), nullable=False),
        sa.Column("source_schema_document_id", sa.String(), nullable=False),
        sa.Column("root_collection_path", sa.String(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "created_by",
        "definition_id",
        "root_collection_path",
        "sequence_index",
        "source_schema_document_id",
        "status",
        "target_collection_path",
    ):
        op.create_index(f"ix_integration_join_bindings_{column}", "integration_join_bindings", [column])

    op.create_table(
        "integration_join_binding_hops",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("binding_id", sa.String(), nullable=False),
        sa.Column("definition_id", sa.String(), nullable=False),
        sa.Column("source_schema_document_id", sa.String(), nullable=False),
        sa.Column("hop_sequence", sa.Integer(), nullable=False),
        sa.Column("left_collection_path", sa.String(), nullable=False),
        sa.Column("left_value_path", sa.String(), nullable=False),
        sa.Column("right_collection_path", sa.String(), nullable=False),
        sa.Column("right_value_path", sa.String(), nullable=False),
        sa.Column("operator", sa.String(), nullable=False),
        sa.Column("result_alias", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["binding_id"], ["integration_join_bindings.id"]),
        sa.ForeignKeyConstraint(["definition_id"], ["integration_definitions.id"]),
        sa.ForeignKeyConstraint(["source_schema_document_id"], ["integration_schema_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "binding_id",
        "created_by",
        "definition_id",
        "hop_sequence",
        "left_collection_path",
        "operator",
        "result_alias",
        "right_collection_path",
        "source_schema_document_id",
        "status",
    ):
        op.create_index(f"ix_integration_join_binding_hops_{column}", "integration_join_binding_hops", [column])


def downgrade() -> None:
    for column in (
        "status",
        "source_schema_document_id",
        "right_collection_path",
        "result_alias",
        "operator",
        "left_collection_path",
        "hop_sequence",
        "definition_id",
        "created_by",
        "binding_id",
    ):
        op.drop_index(f"ix_integration_join_binding_hops_{column}", table_name="integration_join_binding_hops")
    op.drop_table("integration_join_binding_hops")

    for column in (
        "target_collection_path",
        "status",
        "source_schema_document_id",
        "sequence_index",
        "root_collection_path",
        "definition_id",
        "created_by",
    ):
        op.drop_index(f"ix_integration_join_bindings_{column}", table_name="integration_join_bindings")
    op.drop_table("integration_join_bindings")
