"""workbench assistant foundation

Revision ID: c3f7a2b9d4e6
Revises: c2e5a9d8f1b4
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c3f7a2b9d4e6"
down_revision: str | None = "c2e5a9d8f1b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def create_indexes(table_name: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(f"ix_{table_name}_{column}", table_name, [column])


def drop_indexes(table_name: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.drop_index(f"ix_{table_name}_{column}", table_name=table_name)


def upgrade() -> None:
    op.create_table(
        "assistant_sources",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_uri", sa.Text(), nullable=False),
        sa.Column("module_id", sa.String(), nullable=True),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("domain_name", sa.String(), nullable=True),
        sa.Column("visibility", sa.String(), nullable=False),
        sa.Column("access_policy_id", sa.String(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_indexes(
        "assistant_sources",
        (
            "access_policy_id",
            "content_hash",
            "created_by",
            "domain_name",
            "environment_id",
            "module_id",
            "profile_id",
            "project_id",
            "source_type",
            "status",
            "title",
            "visibility",
        ),
    )

    op.create_table(
        "assistant_chunks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("heading", sa.String(), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["assistant_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    create_indexes("assistant_chunks", ("source_id",))

    op.create_table(
        "assistant_index_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_indexes("assistant_index_runs", ("status",))

    op.create_table(
        "assistant_saved_queries",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("sql_text", sa.Text(), nullable=False),
        sa.Column("module_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("visibility", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("domain_name", sa.String(), nullable=True),
        sa.Column("access_policy_id", sa.String(), nullable=True),
        sa.Column("warnings_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_indexes(
        "assistant_saved_queries",
        (
            "access_policy_id",
            "created_by",
            "domain_name",
            "environment_id",
            "module_id",
            "name",
            "profile_id",
            "project_id",
            "reviewed_by",
            "status",
            "visibility",
        ),
    )

    op.create_table(
        "assistant_saved_query_tables",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("query_id", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("alias", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["query_id"], ["assistant_saved_queries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    create_indexes("assistant_saved_query_tables", ("query_id", "role", "table_name"))

    op.create_table(
        "assistant_saved_query_columns",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("query_id", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("column_name", sa.String(), nullable=False),
        sa.Column("alias", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["query_id"], ["assistant_saved_queries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    create_indexes("assistant_saved_query_columns", ("column_name", "query_id", "role", "table_name"))

    op.create_table(
        "assistant_join_patterns",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("module_id", sa.String(), nullable=True),
        sa.Column("left_table", sa.String(), nullable=False),
        sa.Column("left_column", sa.String(), nullable=False),
        sa.Column("right_table", sa.String(), nullable=False),
        sa.Column("right_column", sa.String(), nullable=False),
        sa.Column("join_type", sa.String(), nullable=False),
        sa.Column("business_meaning", sa.Text(), nullable=False),
        sa.Column("confidence", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("warnings_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_indexes(
        "assistant_join_patterns",
        (
            "confidence",
            "created_by",
            "join_type",
            "left_column",
            "left_table",
            "module_id",
            "name",
            "reviewed_by",
            "right_column",
            "right_table",
            "source_id",
            "source_type",
            "status",
        ),
    )

    op.create_table(
        "assistant_oracle_doc_cache",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("source_domain", sa.String(), nullable=False),
        sa.Column("product_area", sa.String(), nullable=False),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("version_label", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_indexes(
        "assistant_oracle_doc_cache",
        (
            "created_by",
            "product_area",
            "reviewed_by",
            "source_domain",
            "status",
            "title",
            "topic",
            "version_label",
        ),
    )


def downgrade() -> None:
    drop_indexes(
        "assistant_oracle_doc_cache",
        ("version_label", "topic", "title", "status", "source_domain", "reviewed_by", "product_area", "created_by"),
    )
    op.drop_table("assistant_oracle_doc_cache")

    drop_indexes(
        "assistant_join_patterns",
        (
            "status",
            "source_type",
            "source_id",
            "right_table",
            "right_column",
            "reviewed_by",
            "name",
            "module_id",
            "left_table",
            "left_column",
            "join_type",
            "created_by",
            "confidence",
        ),
    )
    op.drop_table("assistant_join_patterns")

    drop_indexes("assistant_saved_query_columns", ("table_name", "role", "query_id", "column_name"))
    op.drop_table("assistant_saved_query_columns")

    drop_indexes("assistant_saved_query_tables", ("table_name", "role", "query_id"))
    op.drop_table("assistant_saved_query_tables")

    drop_indexes(
        "assistant_saved_queries",
        (
            "visibility",
            "status",
            "reviewed_by",
            "project_id",
            "profile_id",
            "name",
            "module_id",
            "environment_id",
            "domain_name",
            "created_by",
            "access_policy_id",
        ),
    )
    op.drop_table("assistant_saved_queries")

    drop_indexes("assistant_index_runs", ("status",))
    op.drop_table("assistant_index_runs")

    drop_indexes("assistant_chunks", ("source_id",))
    op.drop_table("assistant_chunks")

    drop_indexes(
        "assistant_sources",
        (
            "visibility",
            "title",
            "status",
            "source_type",
            "project_id",
            "profile_id",
            "module_id",
            "environment_id",
            "domain_name",
            "created_by",
            "content_hash",
            "access_policy_id",
        ),
    )
    op.drop_table("assistant_sources")
