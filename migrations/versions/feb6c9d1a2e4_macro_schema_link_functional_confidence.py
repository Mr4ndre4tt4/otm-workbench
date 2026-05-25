"""macro schema link functional confidence

Revision ID: feb6c9d1a2e4
Revises: fea5d8c3b971
Create Date: 2026-05-25 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "feb6c9d1a2e4"
down_revision: str | None = "fea5d8c3b971"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def index_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    columns = table_columns("macro_object_schema_links")
    additions = [
        ("functional_confidence", sa.Column("functional_confidence", sa.String(), nullable=False, server_default="TECHNICAL_ONLY")),
        ("source_reference_status", sa.Column("source_reference_status", sa.String(), nullable=False, server_default="UNPINNED")),
        ("source_reference_label", sa.Column("source_reference_label", sa.String(), nullable=False, server_default="")),
        ("source_reference_url", sa.Column("source_reference_url", sa.String(), nullable=False, server_default="")),
    ]
    for column_name, column in additions:
        if column_name not in columns:
            op.add_column("macro_object_schema_links", column)

    indexes = index_names("macro_object_schema_links")
    for column_name in ("functional_confidence", "source_reference_status"):
        index_name = f"ix_macro_object_schema_links_{column_name}"
        if index_name not in indexes:
            op.create_index(index_name, "macro_object_schema_links", [column_name])


def downgrade() -> None:
    indexes = index_names("macro_object_schema_links")
    for column_name in ("source_reference_status", "functional_confidence"):
        index_name = f"ix_macro_object_schema_links_{column_name}"
        if index_name in indexes:
            op.drop_index(index_name, table_name="macro_object_schema_links")

    columns = table_columns("macro_object_schema_links")
    for column_name in (
        "source_reference_url",
        "source_reference_label",
        "source_reference_status",
        "functional_confidence",
    ):
        if column_name in columns:
            op.drop_column("macro_object_schema_links", column_name)
