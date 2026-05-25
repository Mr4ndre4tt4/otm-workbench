"""rate batch schema roots

Revision ID: fea5d8c3b971
Revises: fe9a4c2d7e83
Create Date: 2026-05-25 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "fea5d8c3b971"
down_revision: str | None = "fe9a4c2d7e83"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if "schema_root_ids_json" not in table_columns("rate_batches"):
        op.add_column(
            "rate_batches",
            sa.Column("schema_root_ids_json", sa.Text(), nullable=False, server_default="[]"),
        )


def downgrade() -> None:
    if "schema_root_ids_json" in table_columns("rate_batches"):
        op.drop_column("rate_batches", "schema_root_ids_json")
