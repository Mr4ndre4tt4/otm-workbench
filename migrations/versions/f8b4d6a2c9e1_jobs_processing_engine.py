"""jobs processing engine

Revision ID: f8b4d6a2c9e1
Revises: e6b1c9d4a7f2
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f8b4d6a2c9e1"
down_revision: str | None = "e6b1c9d4a7f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("profile_id", sa.String(), nullable=True))
    op.add_column("jobs", sa.Column("environment_id", sa.String(), nullable=True))
    op.add_column("jobs", sa.Column("domain_name", sa.String(), nullable=True))
    op.add_column("jobs", sa.Column("message", sa.Text(), nullable=False, server_default=""))
    op.add_column("jobs", sa.Column("error_code", sa.String(), nullable=True))
    op.add_column("jobs", sa.Column("error_details_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("jobs", sa.Column("created_by", sa.String(), nullable=True))
    op.add_column("jobs", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("jobs", sa.Column("finished_at", sa.DateTime(), nullable=True))
    op.add_column("jobs", sa.Column("cancelled_at", sa.DateTime(), nullable=True))
    for column in ["profile_id", "environment_id", "domain_name", "job_type", "source_module", "status", "created_by"]:
        op.create_index(f"ix_jobs_{column}", "jobs", [column])

    op.create_table(
        "job_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("status_before", sa.String(), nullable=True),
        sa.Column("status_after", sa.String(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_events_job_id", "job_events", ["job_id"])
    op.create_index("ix_job_events_event_type", "job_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_job_events_event_type", table_name="job_events")
    op.drop_index("ix_job_events_job_id", table_name="job_events")
    op.drop_table("job_events")
    for column in ["created_by", "status", "source_module", "job_type", "domain_name", "environment_id", "profile_id"]:
        op.drop_index(f"ix_jobs_{column}", table_name="jobs")
    for column in [
        "cancelled_at",
        "finished_at",
        "started_at",
        "created_by",
        "error_details_json",
        "error_code",
        "message",
        "domain_name",
        "environment_id",
        "profile_id",
    ]:
        op.drop_column("jobs", column)
