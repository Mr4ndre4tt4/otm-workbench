"""rates reference catalog

Revision ID: b7d4a6f1c2a9
Revises: a4e08b3ed2e6
Create Date: 2026-05-18 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d4a6f1c2a9"
down_revision: Union[str, None] = "a4e08b3ed2e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reference_object_types",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_reference_object_types_code"), "reference_object_types", ["code"])

    op.create_table(
        "reference_objects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("object_type", sa.String(), nullable=False),
        sa.Column("gid", sa.String(), nullable=False),
        sa.Column("xid", sa.String(), nullable=False),
        sa.Column("domain_name", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("sync_batch_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reference_objects_project_id"), "reference_objects", ["project_id"])
    op.create_index(op.f("ix_reference_objects_environment_id"), "reference_objects", ["environment_id"])
    op.create_index(op.f("ix_reference_objects_object_type"), "reference_objects", ["object_type"])
    op.create_index(op.f("ix_reference_objects_gid"), "reference_objects", ["gid"])
    op.create_index(op.f("ix_reference_objects_domain_name"), "reference_objects", ["domain_name"])
    op.create_index(op.f("ix_reference_objects_sync_batch_id"), "reference_objects", ["sync_batch_id"])

    op.create_table(
        "reference_field_policies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("module_id", sa.String(), nullable=False),
        sa.Column("field_name", sa.String(), nullable=False),
        sa.Column("object_type", sa.String(), nullable=False),
        sa.Column("policy", sa.String(), nullable=False),
        sa.Column("severity_when_missing", sa.String(), nullable=False),
        sa.Column("allow_manual_value", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reference_field_policies_module_id"), "reference_field_policies", ["module_id"])
    op.create_index(op.f("ix_reference_field_policies_field_name"), "reference_field_policies", ["field_name"])
    op.create_index(op.f("ix_reference_field_policies_object_type"), "reference_field_policies", ["object_type"])

    op.create_table(
        "reference_import_batches",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_description", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("records_received", sa.Integer(), nullable=False),
        sa.Column("records_inserted", sa.Integer(), nullable=False),
        sa.Column("records_updated", sa.Integer(), nullable=False),
        sa.Column("records_rejected", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reference_import_batches_project_id"), "reference_import_batches", ["project_id"])
    op.create_index(op.f("ix_reference_import_batches_environment_id"), "reference_import_batches", ["environment_id"])
    op.create_index(op.f("ix_reference_import_batches_profile_id"), "reference_import_batches", ["profile_id"])

    op.create_table(
        "reference_snapshots",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("snapshot_name", sa.String(), nullable=False),
        sa.Column("object_types_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("source_import_batch_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reference_snapshots_project_id"), "reference_snapshots", ["project_id"])
    op.create_index(op.f("ix_reference_snapshots_environment_id"), "reference_snapshots", ["environment_id"])
    op.create_index(op.f("ix_reference_snapshots_profile_id"), "reference_snapshots", ["profile_id"])

    op.create_table(
        "reference_snapshot_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("snapshot_id", sa.String(), nullable=False),
        sa.Column("reference_object_id", sa.String(), nullable=False),
        sa.Column("object_type", sa.String(), nullable=False),
        sa.Column("gid", sa.String(), nullable=False),
        sa.Column("domain_name", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["snapshot_id"], ["reference_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reference_snapshot_items_snapshot_id"), "reference_snapshot_items", ["snapshot_id"])
    op.create_index(
        op.f("ix_reference_snapshot_items_reference_object_id"),
        "reference_snapshot_items",
        ["reference_object_id"],
    )

    op.create_table(
        "otm_table_definitions",
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("schema_name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("primary_key_json", sa.Text(), nullable=False),
        sa.Column("source_path", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("table_name"),
    )

    op.create_table(
        "otm_table_columns",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("column_name", sa.String(), nullable=False),
        sa.Column("data_type", sa.String(), nullable=False),
        sa.Column("is_nullable", sa.Boolean(), nullable=False),
        sa.Column("is_constraint", sa.Boolean(), nullable=False),
        sa.Column("constraint_values", sa.Text(), nullable=False),
        sa.Column("default_value", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_otm_table_columns_table_name"), "otm_table_columns", ["table_name"])
    op.create_index(op.f("ix_otm_table_columns_column_name"), "otm_table_columns", ["column_name"])

    op.create_table(
        "otm_table_foreign_keys",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("foreign_key_name", sa.String(), nullable=False),
        sa.Column("column_name", sa.String(), nullable=False),
        sa.Column("parent_table_name", sa.String(), nullable=False),
        sa.Column("parent_column_name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_otm_table_foreign_keys_table_name"), "otm_table_foreign_keys", ["table_name"])
    op.create_index(
        op.f("ix_otm_table_foreign_keys_parent_table_name"),
        "otm_table_foreign_keys",
        ["parent_table_name"],
    )

    op.create_table(
        "otm_load_sequences",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("module_id", sa.String(), nullable=False),
        sa.Column("sequence_name", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "otm_csv_contracts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("module_id", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("date_format", sa.String(), nullable=False),
        sa.Column("special_rules_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_otm_csv_contracts_table_name"), "otm_csv_contracts", ["table_name"])


def downgrade() -> None:
    op.drop_index(op.f("ix_otm_csv_contracts_table_name"), table_name="otm_csv_contracts")
    op.drop_table("otm_csv_contracts")
    op.drop_table("otm_load_sequences")
    op.drop_index(op.f("ix_otm_table_foreign_keys_parent_table_name"), table_name="otm_table_foreign_keys")
    op.drop_index(op.f("ix_otm_table_foreign_keys_table_name"), table_name="otm_table_foreign_keys")
    op.drop_table("otm_table_foreign_keys")
    op.drop_index(op.f("ix_otm_table_columns_column_name"), table_name="otm_table_columns")
    op.drop_index(op.f("ix_otm_table_columns_table_name"), table_name="otm_table_columns")
    op.drop_table("otm_table_columns")
    op.drop_table("otm_table_definitions")
    op.drop_index(op.f("ix_reference_snapshot_items_reference_object_id"), table_name="reference_snapshot_items")
    op.drop_index(op.f("ix_reference_snapshot_items_snapshot_id"), table_name="reference_snapshot_items")
    op.drop_table("reference_snapshot_items")
    op.drop_index(op.f("ix_reference_snapshots_profile_id"), table_name="reference_snapshots")
    op.drop_index(op.f("ix_reference_snapshots_environment_id"), table_name="reference_snapshots")
    op.drop_index(op.f("ix_reference_snapshots_project_id"), table_name="reference_snapshots")
    op.drop_table("reference_snapshots")
    op.drop_index(op.f("ix_reference_import_batches_profile_id"), table_name="reference_import_batches")
    op.drop_index(op.f("ix_reference_import_batches_environment_id"), table_name="reference_import_batches")
    op.drop_index(op.f("ix_reference_import_batches_project_id"), table_name="reference_import_batches")
    op.drop_table("reference_import_batches")
    op.drop_index(op.f("ix_reference_field_policies_object_type"), table_name="reference_field_policies")
    op.drop_index(op.f("ix_reference_field_policies_field_name"), table_name="reference_field_policies")
    op.drop_index(op.f("ix_reference_field_policies_module_id"), table_name="reference_field_policies")
    op.drop_table("reference_field_policies")
    op.drop_index(op.f("ix_reference_objects_sync_batch_id"), table_name="reference_objects")
    op.drop_index(op.f("ix_reference_objects_domain_name"), table_name="reference_objects")
    op.drop_index(op.f("ix_reference_objects_gid"), table_name="reference_objects")
    op.drop_index(op.f("ix_reference_objects_object_type"), table_name="reference_objects")
    op.drop_index(op.f("ix_reference_objects_environment_id"), table_name="reference_objects")
    op.drop_index(op.f("ix_reference_objects_project_id"), table_name="reference_objects")
    op.drop_table("reference_objects")
    op.drop_index(op.f("ix_reference_object_types_code"), table_name="reference_object_types")
    op.drop_table("reference_object_types")
