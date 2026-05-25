"""schema pack contract catalog

Revision ID: fd6b1a9c3e42
Revises: fc4a7d2e9b61
Create Date: 2026-05-25 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "fd6b1a9c3e42"
down_revision: str | None = "fc4a7d2e9b61"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schema_packs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("otm_version", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_path", sa.String(), nullable=False),
        sa.Column("asset_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("namespace_count", sa.Integer(), nullable=False),
        sa.Column("root_count", sa.Integer(), nullable=False),
        sa.Column("operation_count", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "otm_version", name="uq_schema_packs_code_version"),
    )
    for column in ("asset_id", "code", "content_hash", "created_by", "otm_version", "source_type", "status"):
        op.create_index(f"ix_schema_packs_{column}", "schema_packs", [column])

    op.create_table(
        "schema_files",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("schema_pack_id", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("relative_path", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("namespace", sa.String(), nullable=False),
        sa.Column("import_count", sa.Integer(), nullable=False),
        sa.Column("top_level_element_count", sa.Integer(), nullable=False),
        sa.Column("complex_type_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["schema_pack_id"], ["schema_packs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("file_name", "file_type", "namespace", "schema_pack_id", "status"):
        op.create_index(f"ix_schema_files_{column}", "schema_files", [column])

    op.create_table(
        "schema_roots",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("schema_pack_id", sa.String(), nullable=False),
        sa.Column("schema_file_id", sa.String(), nullable=False),
        sa.Column("root_name", sa.String(), nullable=False),
        sa.Column("namespace", sa.String(), nullable=False),
        sa.Column("domain_area", sa.String(), nullable=False),
        sa.Column("root_type", sa.String(), nullable=False),
        sa.Column("envelope_role", sa.String(), nullable=False),
        sa.Column("recommended_modules_json", sa.Text(), nullable=False),
        sa.Column("documentation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["schema_file_id"], ["schema_files.id"]),
        sa.ForeignKeyConstraint(["schema_pack_id"], ["schema_packs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("domain_area", "envelope_role", "namespace", "root_name", "root_type", "schema_file_id", "schema_pack_id"):
        op.create_index(f"ix_schema_roots_{column}", "schema_roots", [column])

    op.create_table(
        "schema_paths",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("schema_root_id", sa.String(), nullable=False),
        sa.Column("parent_path", sa.String(), nullable=True),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("node_name", sa.String(), nullable=False),
        sa.Column("data_type", sa.String(), nullable=True),
        sa.Column("min_occurs", sa.String(), nullable=False),
        sa.Column("max_occurs", sa.String(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("is_repeatable", sa.Boolean(), nullable=False),
        sa.Column("documentation", sa.Text(), nullable=False),
        sa.Column("source_file", sa.String(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["schema_root_id"], ["schema_roots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("is_repeatable", "is_required", "node_name", "parent_path", "path", "schema_root_id", "sequence_index"):
        op.create_index(f"ix_schema_paths_{column}", "schema_paths", [column])

    op.create_table(
        "service_operations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("schema_pack_id", sa.String(), nullable=False),
        sa.Column("schema_file_id", sa.String(), nullable=False),
        sa.Column("service_name", sa.String(), nullable=False),
        sa.Column("operation_name", sa.String(), nullable=False),
        sa.Column("input_message", sa.String(), nullable=False),
        sa.Column("output_message", sa.String(), nullable=False),
        sa.Column("fault_message", sa.String(), nullable=False),
        sa.Column("target_namespace", sa.String(), nullable=False),
        sa.Column("related_roots_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["schema_file_id"], ["schema_files.id"]),
        sa.ForeignKeyConstraint(["schema_pack_id"], ["schema_packs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("operation_name", "schema_file_id", "schema_pack_id", "service_name"):
        op.create_index(f"ix_service_operations_{column}", "service_operations", [column])

    op.create_table(
        "macro_object_schema_links",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("macro_object_code", sa.String(), nullable=False),
        sa.Column("schema_root_id", sa.String(), nullable=False),
        sa.Column("relationship_role", sa.String(), nullable=False),
        sa.Column("confidence", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["schema_root_id"], ["schema_roots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("confidence", "macro_object_code", "relationship_role", "schema_root_id"):
        op.create_index(f"ix_macro_object_schema_links_{column}", "macro_object_schema_links", [column])


def downgrade() -> None:
    for column in ("confidence", "macro_object_code", "relationship_role", "schema_root_id"):
        op.drop_index(f"ix_macro_object_schema_links_{column}", table_name="macro_object_schema_links")
    op.drop_table("macro_object_schema_links")

    for column in ("operation_name", "schema_file_id", "schema_pack_id", "service_name"):
        op.drop_index(f"ix_service_operations_{column}", table_name="service_operations")
    op.drop_table("service_operations")

    for column in ("is_repeatable", "is_required", "node_name", "parent_path", "path", "schema_root_id", "sequence_index"):
        op.drop_index(f"ix_schema_paths_{column}", table_name="schema_paths")
    op.drop_table("schema_paths")

    for column in ("domain_area", "envelope_role", "namespace", "root_name", "root_type", "schema_file_id", "schema_pack_id"):
        op.drop_index(f"ix_schema_roots_{column}", table_name="schema_roots")
    op.drop_table("schema_roots")

    for column in ("file_name", "file_type", "namespace", "schema_pack_id", "status"):
        op.drop_index(f"ix_schema_files_{column}", table_name="schema_files")
    op.drop_table("schema_files")

    for column in ("asset_id", "code", "content_hash", "created_by", "otm_version", "source_type", "status"):
        op.drop_index(f"ix_schema_packs_{column}", table_name="schema_packs")
    op.drop_table("schema_packs")
