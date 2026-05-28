"""integration enrichment pipeline

Revision ID: c2e5a9d8f1b4
Revises: c1f4a8e7d9b2
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c2e5a9d8f1b4"
down_revision: str | None = "c1f4a8e7d9b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_enrichment_steps",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("definition_id", sa.String(), nullable=False),
        sa.Column("source_schema_document_id", sa.String(), nullable=False),
        sa.Column("response_schema_document_id", sa.String(), nullable=False),
        sa.Column("endpoint_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("step_type", sa.String(), nullable=False),
        sa.Column("key_template", sa.String(), nullable=False),
        sa.Column("key_source_fields_json", sa.Text(), nullable=False),
        sa.Column("response_field_mappings_json", sa.Text(), nullable=False),
        sa.Column("loop_source_path", sa.String(), nullable=False),
        sa.Column("loop_filter_expression", sa.String(), nullable=False),
        sa.Column("on_empty_response", sa.String(), nullable=False),
        sa.Column("on_error", sa.String(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["definition_id"], ["integration_definitions.id"]),
        sa.ForeignKeyConstraint(["endpoint_id"], ["integration_endpoints.id"]),
        sa.ForeignKeyConstraint(["response_schema_document_id"], ["integration_schema_documents.id"]),
        sa.ForeignKeyConstraint(["source_schema_document_id"], ["integration_schema_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "created_by",
        "definition_id",
        "endpoint_id",
        "loop_source_path",
        "on_empty_response",
        "on_error",
        "response_schema_document_id",
        "sequence_index",
        "source_schema_document_id",
        "status",
        "step_type",
    ):
        op.create_index(f"ix_integration_enrichment_steps_{column}", "integration_enrichment_steps", [column])

    op.create_table(
        "integration_enrichment_substeps",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("definition_id", sa.String(), nullable=False),
        sa.Column("enrichment_step_id", sa.String(), nullable=False),
        sa.Column("endpoint_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("request_path_template", sa.String(), nullable=False),
        sa.Column("request_key_bindings_json", sa.Text(), nullable=False),
        sa.Column("response_schema_document_id", sa.String(), nullable=False),
        sa.Column("response_field_mappings_json", sa.Text(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["definition_id"], ["integration_definitions.id"]),
        sa.ForeignKeyConstraint(["endpoint_id"], ["integration_endpoints.id"]),
        sa.ForeignKeyConstraint(["enrichment_step_id"], ["integration_enrichment_steps.id"]),
        sa.ForeignKeyConstraint(["response_schema_document_id"], ["integration_schema_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "created_by",
        "definition_id",
        "endpoint_id",
        "enrichment_step_id",
        "response_schema_document_id",
        "sequence_index",
        "status",
    ):
        op.create_index(f"ix_integration_enrichment_substeps_{column}", "integration_enrichment_substeps", [column])

    op.create_table(
        "integration_enriched_fields",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("definition_id", sa.String(), nullable=False),
        sa.Column("enrichment_step_id", sa.String(), nullable=False),
        sa.Column("enrichment_substep_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("data_type", sa.String(), nullable=False),
        sa.Column("cardinality", sa.String(), nullable=False),
        sa.Column("response_path", sa.String(), nullable=False),
        sa.Column("fallback_policy_json", sa.Text(), nullable=False),
        sa.Column("source_trace_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["definition_id"], ["integration_definitions.id"]),
        sa.ForeignKeyConstraint(["enrichment_step_id"], ["integration_enrichment_steps.id"]),
        sa.ForeignKeyConstraint(["enrichment_substep_id"], ["integration_enrichment_substeps.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "cardinality",
        "created_by",
        "data_type",
        "definition_id",
        "enrichment_step_id",
        "enrichment_substep_id",
        "name",
        "response_path",
        "status",
    ):
        op.create_index(f"ix_integration_enriched_fields_{column}", "integration_enriched_fields", [column])


def downgrade() -> None:
    for column in (
        "status",
        "response_path",
        "name",
        "enrichment_substep_id",
        "enrichment_step_id",
        "definition_id",
        "data_type",
        "created_by",
        "cardinality",
    ):
        op.drop_index(f"ix_integration_enriched_fields_{column}", table_name="integration_enriched_fields")
    op.drop_table("integration_enriched_fields")

    for column in (
        "status",
        "sequence_index",
        "response_schema_document_id",
        "enrichment_step_id",
        "endpoint_id",
        "definition_id",
        "created_by",
    ):
        op.drop_index(f"ix_integration_enrichment_substeps_{column}", table_name="integration_enrichment_substeps")
    op.drop_table("integration_enrichment_substeps")

    for column in (
        "step_type",
        "status",
        "source_schema_document_id",
        "sequence_index",
        "response_schema_document_id",
        "on_error",
        "on_empty_response",
        "loop_source_path",
        "endpoint_id",
        "definition_id",
        "created_by",
    ):
        op.drop_index(f"ix_integration_enrichment_steps_{column}", table_name="integration_enrichment_steps")
    op.drop_table("integration_enrichment_steps")
