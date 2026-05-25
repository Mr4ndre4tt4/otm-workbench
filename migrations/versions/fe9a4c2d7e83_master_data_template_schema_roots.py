"""master data template schema roots

Revision ID: fe9a4c2d7e83
Revises: fe8d3b1a6c72
Create Date: 2026-05-25 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "fe9a4c2d7e83"
down_revision: str | None = "fe8d3b1a6c72"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if "schema_root_ids_json" not in table_columns("master_data_templates"):
        op.add_column(
            "master_data_templates",
            sa.Column("schema_root_ids_json", sa.Text(), nullable=False, server_default="[]"),
        )


def downgrade() -> None:
    if "schema_root_ids_json" in table_columns("master_data_templates"):
        op.drop_column("master_data_templates", "schema_root_ids_json")
