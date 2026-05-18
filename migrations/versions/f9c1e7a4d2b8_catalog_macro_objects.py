"""catalog macro objects

Revision ID: f9c1e7a4d2b8
Revises: f8b4d6a2c9e1
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f9c1e7a4d2b8"
down_revision: str | None = "f8b4d6a2c9e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "otm_macro_objects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("default_load_order", sa.Integer(), nullable=False),
        sa.Column("default_method", sa.String(), nullable=False),
        sa.Column("method_options_json", sa.Text(), nullable=False),
        sa.Column("allow_cutover", sa.Boolean(), nullable=False),
        sa.Column("allow_csvutil", sa.Boolean(), nullable=False),
        sa.Column("evidence_required_default", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_otm_macro_objects_code", "otm_macro_objects", ["code"])
    op.create_index("ix_otm_macro_objects_category", "otm_macro_objects", ["category"])

    op.create_table(
        "otm_macro_object_tables",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("macro_object_id", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("relationship_role", sa.String(), nullable=False),
        sa.Column("is_primary_table", sa.Boolean(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("data_category", sa.String(), nullable=False),
        sa.Column("validated_by_datadict", sa.Boolean(), nullable=False),
        sa.Column("allow_csvutil", sa.Boolean(), nullable=False),
        sa.Column("allow_cutover", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["macro_object_id"], ["otm_macro_objects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_otm_macro_object_tables_macro_object_id", "otm_macro_object_tables", ["macro_object_id"])
    op.create_index("ix_otm_macro_object_tables_table_name", "otm_macro_object_tables", ["table_name"])

    op.create_table(
        "otm_macro_object_dependencies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("macro_object_id", sa.String(), nullable=False),
        sa.Column("depends_on_macro_object_id", sa.String(), nullable=False),
        sa.Column("dependency_type", sa.String(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["depends_on_macro_object_id"], ["otm_macro_objects.id"]),
        sa.ForeignKeyConstraint(["macro_object_id"], ["otm_macro_objects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_otm_macro_object_dependencies_macro_object_id", "otm_macro_object_dependencies", ["macro_object_id"])
    op.create_index(
        "ix_otm_macro_object_dependencies_depends_on_macro_object_id",
        "otm_macro_object_dependencies",
        ["depends_on_macro_object_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_otm_macro_object_dependencies_depends_on_macro_object_id",
        table_name="otm_macro_object_dependencies",
    )
    op.drop_index("ix_otm_macro_object_dependencies_macro_object_id", table_name="otm_macro_object_dependencies")
    op.drop_table("otm_macro_object_dependencies")
    op.drop_index("ix_otm_macro_object_tables_table_name", table_name="otm_macro_object_tables")
    op.drop_index("ix_otm_macro_object_tables_macro_object_id", table_name="otm_macro_object_tables")
    op.drop_table("otm_macro_object_tables")
    op.drop_index("ix_otm_macro_objects_category", table_name="otm_macro_objects")
    op.drop_index("ix_otm_macro_objects_code", table_name="otm_macro_objects")
    op.drop_table("otm_macro_objects")
