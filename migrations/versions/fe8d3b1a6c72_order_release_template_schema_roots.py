"""order release template schema roots

Revision ID: fe8d3b1a6c72
Revises: fe7c2a9d4b61
Create Date: 2026-05-25 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "fe8d3b1a6c72"
down_revision: str | None = "fe7c2a9d4b61"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def table_indexes(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    columns = table_columns("order_release_templates")
    if "transmission_schema_root_id" not in columns:
        op.add_column("order_release_templates", sa.Column("transmission_schema_root_id", sa.String(), nullable=True))
    if "release_schema_root_id" not in columns:
        op.add_column("order_release_templates", sa.Column("release_schema_root_id", sa.String(), nullable=True))

    indexes = table_indexes("order_release_templates")
    if "ix_order_release_templates_transmission_schema_root_id" not in indexes:
        op.create_index(
            "ix_order_release_templates_transmission_schema_root_id",
            "order_release_templates",
            ["transmission_schema_root_id"],
        )
    if "ix_order_release_templates_release_schema_root_id" not in indexes:
        op.create_index(
            "ix_order_release_templates_release_schema_root_id",
            "order_release_templates",
            ["release_schema_root_id"],
        )
    if op.get_bind().dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_order_release_templates_transmission_schema_root_id_schema_roots",
            "order_release_templates",
            "schema_roots",
            ["transmission_schema_root_id"],
            ["id"],
        )
        op.create_foreign_key(
            "fk_order_release_templates_release_schema_root_id_schema_roots",
            "order_release_templates",
            "schema_roots",
            ["release_schema_root_id"],
            ["id"],
        )


def downgrade() -> None:
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint(
            "fk_order_release_templates_release_schema_root_id_schema_roots",
            "order_release_templates",
            type_="foreignkey",
        )
        op.drop_constraint(
            "fk_order_release_templates_transmission_schema_root_id_schema_roots",
            "order_release_templates",
            type_="foreignkey",
        )
    op.drop_index("ix_order_release_templates_release_schema_root_id", table_name="order_release_templates")
    op.drop_index("ix_order_release_templates_transmission_schema_root_id", table_name="order_release_templates")
    op.drop_column("order_release_templates", "release_schema_root_id")
    op.drop_column("order_release_templates", "transmission_schema_root_id")
