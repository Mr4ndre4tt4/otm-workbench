"""master data templates

Revision ID: b1d9c3e7a5f0
Revises: ab5d1e7c3f90
Create Date: 2026-05-19 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b1d9c3e7a5f0"
down_revision: str | None = "ab5d1e7c3f90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "master_data_templates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("catalog_macro_object_code", sa.String(), nullable=False),
        sa.Column("data_category", sa.String(), nullable=False),
        sa.Column("target_tables_json", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_master_data_templates_code", "master_data_templates", ["code"])
    op.create_index(
        "ix_master_data_templates_catalog_macro_object_code",
        "master_data_templates",
        ["catalog_macro_object_code"],
    )


def downgrade() -> None:
    op.drop_index("ix_master_data_templates_catalog_macro_object_code", table_name="master_data_templates")
    op.drop_index("ix_master_data_templates_code", table_name="master_data_templates")
    op.drop_table("master_data_templates")
