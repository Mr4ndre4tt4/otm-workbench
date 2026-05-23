"""drop order release template code unique

Revision ID: fa2b7c9d4e6f
Revises: f9d8c2a6b4e1
Create Date: 2026-05-23 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "fa2b7c9d4e6f"
down_revision: str | None = "f9d8c2a6b4e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def replacement_table_name() -> str:
    return "_order_release_templates_rebuild"


def create_replacement_table(table_name: str) -> None:
    op.create_table(
        table_name,
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("macro_object_code", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_columns_json", sa.Text(), nullable=False),
        sa.Column("optional_columns_json", sa.Text(), nullable=False),
        sa.Column("defaults_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "version", name="uq_order_release_templates_code_version"),
    )


def copy_template_rows(target_table: str) -> None:
    op.execute(
        f"""
        INSERT INTO {target_table} (
            id, code, name, version, status, macro_object_code, description,
            required_columns_json, optional_columns_json, defaults_json,
            created_by, created_at, updated_at
        )
        SELECT
            id, code, name, version, status, macro_object_code, description,
            required_columns_json, optional_columns_json, defaults_json,
            created_by, created_at, updated_at
        FROM order_release_templates
        """
    )


def recreate_template_indexes() -> None:
    for column in ("code", "created_by", "macro_object_code", "status", "version"):
        op.create_index(f"ix_order_release_templates_{column}", "order_release_templates", [column])


def upgrade() -> None:
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint("uq_order_release_templates_code", "order_release_templates", type_="unique")
        op.create_unique_constraint(
            "uq_order_release_templates_code_version",
            "order_release_templates",
            ["code", "version"],
        )
        return

    table_name = replacement_table_name()
    op.execute("PRAGMA foreign_keys=OFF")
    create_replacement_table(table_name)
    copy_template_rows(table_name)
    for column in ("version", "status", "macro_object_code", "created_by", "code"):
        op.drop_index(f"ix_order_release_templates_{column}", table_name="order_release_templates")
    op.drop_table("order_release_templates")
    op.rename_table(table_name, "order_release_templates")
    recreate_template_indexes()
    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    raise NotImplementedError("Downgrade is not supported after versioned Order Release templates may exist.")
