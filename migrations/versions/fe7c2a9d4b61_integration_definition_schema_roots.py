"""integration definition schema roots

Revision ID: fe7c2a9d4b61
Revises: fd6b1a9c3e42
Create Date: 2026-05-25 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "fe7c2a9d4b61"
down_revision: str | None = "fd6b1a9c3e42"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def table_indexes(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    columns = table_columns("integration_definitions")
    if "source_schema_root_id" not in columns:
        op.add_column("integration_definitions", sa.Column("source_schema_root_id", sa.String(), nullable=True))
    if "target_schema_root_id" not in columns:
        op.add_column("integration_definitions", sa.Column("target_schema_root_id", sa.String(), nullable=True))

    indexes = table_indexes("integration_definitions")
    if "ix_integration_definitions_source_schema_root_id" not in indexes:
        op.create_index(
            "ix_integration_definitions_source_schema_root_id",
            "integration_definitions",
            ["source_schema_root_id"],
        )
    if "ix_integration_definitions_target_schema_root_id" not in indexes:
        op.create_index(
            "ix_integration_definitions_target_schema_root_id",
            "integration_definitions",
            ["target_schema_root_id"],
        )
    if op.get_bind().dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_integration_definitions_source_schema_root_id_schema_roots",
            "integration_definitions",
            "schema_roots",
            ["source_schema_root_id"],
            ["id"],
        )
        op.create_foreign_key(
            "fk_integration_definitions_target_schema_root_id_schema_roots",
            "integration_definitions",
            "schema_roots",
            ["target_schema_root_id"],
            ["id"],
        )


def downgrade() -> None:
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint(
            "fk_integration_definitions_target_schema_root_id_schema_roots",
            "integration_definitions",
            type_="foreignkey",
        )
        op.drop_constraint(
            "fk_integration_definitions_source_schema_root_id_schema_roots",
            "integration_definitions",
            type_="foreignkey",
        )
    op.drop_index("ix_integration_definitions_target_schema_root_id", table_name="integration_definitions")
    op.drop_index("ix_integration_definitions_source_schema_root_id", table_name="integration_definitions")
    op.drop_column("integration_definitions", "target_schema_root_id")
    op.drop_column("integration_definitions", "source_schema_root_id")
