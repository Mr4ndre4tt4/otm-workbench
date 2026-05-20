"""coordinate quality batches

Revision ID: c3a8f7b2d9e4
Revises: a7c9d2e5f6b1
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c3a8f7b2d9e4"
down_revision: str | None = "a7c9d2e5f6b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "master_data_coordinate_quality_batches",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_batch_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("geocoder_base_url", sa.String(), nullable=True),
        sa.Column("provider_mode", sa.String(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("processed_count", sa.Integer(), nullable=False),
        sa.Column("ok_count", sa.Integer(), nullable=False),
        sa.Column("corrected_count", sa.Integer(), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("divergent_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("issues_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_master_data_coordinate_quality_batches_source_batch_id",
        "master_data_coordinate_quality_batches",
        ["source_batch_id"],
    )
    op.create_index(
        "ix_master_data_coordinate_quality_batches_status",
        "master_data_coordinate_quality_batches",
        ["status"],
    )
    op.create_table(
        "master_data_coordinate_quality_results",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("location_gid", sa.String(), nullable=False),
        sa.Column("location_name", sa.String(), nullable=True),
        sa.Column("address_json", sa.Text(), nullable=False),
        sa.Column("country_code3_gid", sa.String(), nullable=True),
        sa.Column("province_code", sa.String(), nullable=True),
        sa.Column("postal_code", sa.String(), nullable=True),
        sa.Column("lat_orig", sa.String(), nullable=True),
        sa.Column("lon_orig", sa.String(), nullable=True),
        sa.Column("lat_new", sa.String(), nullable=True),
        sa.Column("lon_new", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("diff_lat", sa.String(), nullable=True),
        sa.Column("diff_lon", sa.String(), nullable=True),
        sa.Column("orig_valid_uf", sa.Boolean(), nullable=False),
        sa.Column("new_valid_uf", sa.Boolean(), nullable=False),
        sa.Column("issue_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["master_data_coordinate_quality_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_master_data_coordinate_quality_results_batch_id",
        "master_data_coordinate_quality_results",
        ["batch_id"],
    )
    op.create_index(
        "ix_master_data_coordinate_quality_results_location_gid",
        "master_data_coordinate_quality_results",
        ["location_gid"],
    )
    op.create_index(
        "ix_master_data_coordinate_quality_results_status",
        "master_data_coordinate_quality_results",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_master_data_coordinate_quality_results_status",
        table_name="master_data_coordinate_quality_results",
    )
    op.drop_index(
        "ix_master_data_coordinate_quality_results_location_gid",
        table_name="master_data_coordinate_quality_results",
    )
    op.drop_index(
        "ix_master_data_coordinate_quality_results_batch_id",
        table_name="master_data_coordinate_quality_results",
    )
    op.drop_table("master_data_coordinate_quality_results")
    op.drop_index(
        "ix_master_data_coordinate_quality_batches_status",
        table_name="master_data_coordinate_quality_batches",
    )
    op.drop_index(
        "ix_master_data_coordinate_quality_batches_source_batch_id",
        table_name="master_data_coordinate_quality_batches",
    )
    op.drop_table("master_data_coordinate_quality_batches")
