"""artifact and evidence scope columns

Revision ID: c4a8e2f7b9d1
Revises: c3f7a2b9d4e6
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c4a8e2f7b9d1"
down_revision: str | None = "c3f7a2b9d4e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def index_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def add_scope_columns(table_name: str) -> None:
    columns = table_columns(table_name)
    additions = (
        ("profile_id", sa.Column("profile_id", sa.String(), nullable=True)),
        ("environment_id", sa.Column("environment_id", sa.String(), nullable=True)),
        ("domain_name", sa.Column("domain_name", sa.String(), nullable=True)),
        ("visibility", sa.Column("visibility", sa.String(), nullable=False, server_default="PRIVATE")),
        ("access_policy_id", sa.Column("access_policy_id", sa.String(), nullable=True)),
    )
    for column_name, column in additions:
        if column_name not in columns:
            op.add_column(table_name, column)

    indexes = index_names(table_name)
    for column_name in ("domain_name", "visibility", "access_policy_id"):
        index_name = f"ix_{table_name}_{column_name}"
        if index_name not in indexes:
            op.create_index(index_name, table_name, [column_name])


def drop_scope_columns(table_name: str) -> None:
    indexes = index_names(table_name)
    for column_name in ("access_policy_id", "visibility", "domain_name"):
        index_name = f"ix_{table_name}_{column_name}"
        if index_name in indexes:
            op.drop_index(index_name, table_name=table_name)

    columns = table_columns(table_name)
    for column_name in ("access_policy_id", "visibility", "domain_name", "environment_id", "profile_id"):
        if column_name in columns:
            op.drop_column(table_name, column_name)


def upgrade() -> None:
    add_scope_columns("artifacts")
    add_scope_columns("manifests")
    add_scope_columns("evidence")


def downgrade() -> None:
    drop_scope_columns("evidence")
    drop_scope_columns("manifests")
    drop_scope_columns("artifacts")
