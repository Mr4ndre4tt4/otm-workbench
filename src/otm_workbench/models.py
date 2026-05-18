from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from otm_workbench.database import Base


def new_id() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


class SessionToken(Base):
    __tablename__ = "session_tokens"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, unique=True)


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String)


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String)


class Environment(Base, TimestampMixin):
    __tablename__ = "environments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    environment_type: Mapped[str] = mapped_column(String, default="DEV")


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, unique=True)


class Capability(Base, TimestampMixin):
    __tablename__ = "capabilities"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, unique=True)


class UserProjectRole(Base, TimestampMixin):
    __tablename__ = "user_project_roles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), index=True)


class RoleCapability(Base):
    __tablename__ = "role_capabilities"

    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    capability_id: Mapped[str] = mapped_column(ForeignKey("capabilities.id"), primary_key=True)


class Module(Base, TimestampMixin):
    __tablename__ = "modules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String)
    route_base: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="PLANNED")
    required_capability: Mapped[str | None] = mapped_column(String, nullable=True)
    feature_flag: Mapped[str | None] = mapped_column(String, nullable=True)
    admin_only: Mapped[bool] = mapped_column(Boolean, default=False)
    dev_only: Mapped[bool] = mapped_column(Boolean, default=False)


class FeatureFlag(Base, TimestampMixin):
    __tablename__ = "feature_flags"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    scope: Mapped[str] = mapped_column(String, default="global")


class DomainEvent(Base, TimestampMixin):
    __tablename__ = "domain_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    event_type: Mapped[str] = mapped_column(String, index=True)
    source_module: Mapped[str] = mapped_column(String)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    aggregate_type: Mapped[str] = mapped_column(String)
    aggregate_id: Mapped[str] = mapped_column(String)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String, default="PENDING")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    job_type: Mapped[str] = mapped_column(String)
    source_module: Mapped[str] = mapped_column(String)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    input_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class Artifact(Base, TimestampMixin):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_module: Mapped[str] = mapped_column(String)
    artifact_type: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    file_name: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String)
    sha256: Mapped[str] = mapped_column(String)
    size_bytes: Mapped[int] = mapped_column(Integer)
    sensitivity_level: Mapped[str] = mapped_column(String, default="internal")


class Manifest(Base, TimestampMixin):
    __tablename__ = "manifests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_module: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="CREATED")
    manifest_json: Mapped[str] = mapped_column(Text, default="{}")


class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_module: Mapped[str] = mapped_column(String)
    evidence_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="CREATED")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    manifest_id: Mapped[str | None] = mapped_column(String, nullable=True)
    artifact_id: Mapped[str | None] = mapped_column(String, nullable=True)
    client_safe: Mapped[bool] = mapped_column(Boolean, default=True)
    sensitivity_level: Mapped[str] = mapped_column(String, default="client_safe")


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    actor_user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String, index=True)
    target_type: Mapped[str] = mapped_column(String)
    target_id: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class ReferenceObjectType(Base, TimestampMixin):
    __tablename__ = "reference_object_types"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ReferenceObject(Base, TimestampMixin):
    __tablename__ = "reference_objects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    object_type: Mapped[str] = mapped_column(String, index=True)
    gid: Mapped[str] = mapped_column(String, index=True)
    xid: Mapped[str] = mapped_column(String, default="")
    domain_name: Mapped[str] = mapped_column(String, index=True)
    display_name: Mapped[str] = mapped_column(String, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    source: Mapped[str] = mapped_column(String, default="manual")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sync_batch_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class ReferenceFieldPolicy(Base, TimestampMixin):
    __tablename__ = "reference_field_policies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    module_id: Mapped[str] = mapped_column(String, index=True)
    field_name: Mapped[str] = mapped_column(String, index=True)
    object_type: Mapped[str] = mapped_column(String, index=True)
    policy: Mapped[str] = mapped_column(String)
    severity_when_missing: Mapped[str] = mapped_column(String)
    allow_manual_value: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ReferenceImportBatch(Base, TimestampMixin):
    __tablename__ = "reference_import_batches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String)
    source_description: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="PENDING")
    records_received: Mapped[int] = mapped_column(Integer, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)


class ReferenceSnapshot(Base, TimestampMixin):
    __tablename__ = "reference_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    snapshot_name: Mapped[str] = mapped_column(String)
    object_types_json: Mapped[str] = mapped_column(Text, default="[]")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    source_import_batch_id: Mapped[str | None] = mapped_column(String, nullable=True)


class ReferenceSnapshotItem(Base):
    __tablename__ = "reference_snapshot_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey("reference_snapshots.id"), index=True)
    reference_object_id: Mapped[str] = mapped_column(String, index=True)
    object_type: Mapped[str] = mapped_column(String)
    gid: Mapped[str] = mapped_column(String)
    domain_name: Mapped[str] = mapped_column(String)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class OtmTableDefinition(Base, TimestampMixin):
    __tablename__ = "otm_table_definitions"

    table_name: Mapped[str] = mapped_column(String, primary_key=True)
    schema_name: Mapped[str] = mapped_column(String, default="glogowner")
    description: Mapped[str] = mapped_column(Text, default="")
    primary_key_json: Mapped[str] = mapped_column(Text, default="[]")
    source_path: Mapped[str] = mapped_column(String, default="")


class OtmTableColumn(Base):
    __tablename__ = "otm_table_columns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    table_name: Mapped[str] = mapped_column(String, index=True)
    column_name: Mapped[str] = mapped_column(String, index=True)
    data_type: Mapped[str] = mapped_column(String)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_constraint: Mapped[bool] = mapped_column(Boolean, default=False)
    constraint_values: Mapped[str] = mapped_column(Text, default="")
    default_value: Mapped[str] = mapped_column(String, default="")


class OtmTableForeignKey(Base):
    __tablename__ = "otm_table_foreign_keys"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    table_name: Mapped[str] = mapped_column(String, index=True)
    foreign_key_name: Mapped[str] = mapped_column(String)
    column_name: Mapped[str] = mapped_column(String)
    parent_table_name: Mapped[str] = mapped_column(String, index=True)
    parent_column_name: Mapped[str] = mapped_column(String)


class OtmLoadSequence(Base, TimestampMixin):
    __tablename__ = "otm_load_sequences"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    module_id: Mapped[str] = mapped_column(String, default="rates")
    sequence_name: Mapped[str] = mapped_column(String)
    table_name: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")


class OtmCsvContract(Base, TimestampMixin):
    __tablename__ = "otm_csv_contracts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    module_id: Mapped[str] = mapped_column(String, default="rates")
    table_name: Mapped[str] = mapped_column(String, index=True)
    date_format: Mapped[str] = mapped_column(String, default="YYYY-MM-DD HH24:MI:SS")
    special_rules_json: Mapped[str] = mapped_column(Text, default="{}")


class RateBatch(Base, TimestampMixin):
    __tablename__ = "rate_batches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    scenario_code: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String, default="DRAFT", index=True)
    source_type: Mapped[str] = mapped_column(String, default="api")
    domain_name: Mapped[str] = mapped_column(String, index=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    exported_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")


class RateBatchTable(Base, TimestampMixin):
    __tablename__ = "rate_batch_tables"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("rate_batches.id"), index=True)
    table_name: Mapped[str] = mapped_column(String, index=True)
    sequence_index: Mapped[int] = mapped_column(Integer)
    requirement_level: Mapped[str] = mapped_column(String, default="OPTIONAL")
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="PENDING", index=True)


class RateBatchRow(Base, TimestampMixin):
    __tablename__ = "rate_batch_rows"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("rate_batches.id"), index=True)
    batch_table_id: Mapped[str] = mapped_column(ForeignKey("rate_batch_tables.id"), index=True)
    table_name: Mapped[str] = mapped_column(String, index=True)
    row_index: Mapped[int] = mapped_column(Integer)
    row_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    normalized_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    row_hash: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="PENDING", index=True)


class RateBatchIssue(Base):
    __tablename__ = "rate_batch_issues"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("rate_batches.id"), index=True)
    batch_table_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    batch_row_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String, index=True)
    issue_code: Mapped[str] = mapped_column(String, index=True)
    table_name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    column_name: Mapped[str | None] = mapped_column(String, nullable=True)
    message: Mapped[str] = mapped_column(Text)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LoadPlanPackage(Base, TimestampMixin):
    __tablename__ = "load_plan_packages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    source_module: Mapped[str] = mapped_column(String, index=True)
    source_entity_type: Mapped[str] = mapped_column(String, index=True)
    source_entity_id: Mapped[str] = mapped_column(String, index=True)
    package_type: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="REGISTERED", index=True)
    artifact_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    manifest_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    approval_evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    load_sequence_json: Mapped[str] = mapped_column(Text, default="[]")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CsvutilBuild(Base, TimestampMixin):
    __tablename__ = "csvutil_builds"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="BUILT", index=True)
    ctl_artifact_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    cl_artifact_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    manifest_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    built_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LoadPlanZipAnalysis(Base, TimestampMixin):
    __tablename__ = "load_plan_zip_analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="ANALYZED", index=True)
    source_artifact_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    source_manifest_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    manifest_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    findings_json: Mapped[str] = mapped_column(Text, default="[]")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LoadPlanReviewItem(Base, TimestampMixin):
    __tablename__ = "load_plan_review_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    zip_analysis_id: Mapped[str] = mapped_column(ForeignKey("load_plan_zip_analyses.id"), index=True)
    source_type: Mapped[str] = mapped_column(String, default="zip_analysis_finding", index=True)
    source_code: Mapped[str] = mapped_column(String, index=True)
    severity: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="PENDING_REVIEW", index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    table_name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)


class LoadPlanReviewDecision(Base, TimestampMixin):
    __tablename__ = "load_plan_review_decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    review_item_id: Mapped[str] = mapped_column(ForeignKey("load_plan_review_items.id"), index=True)
    decision_status: Mapped[str] = mapped_column(String, index=True)
    decision_note: Mapped[str] = mapped_column(Text, default="")
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    decided_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LoadPlanSequenceSnapshot(Base, TimestampMixin):
    __tablename__ = "load_plan_sequence_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="BLOCKED", index=True)
    sequence_json: Mapped[str] = mapped_column(Text, default="[]")
    blockers_json: Mapped[str] = mapped_column(Text, default="[]")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    generated_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class LoadPlanCutoverReadiness(Base, TimestampMixin):
    __tablename__ = "load_plan_cutover_readiness"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    sequence_snapshot_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, default="MISSING_SEQUENCE", index=True)
    readiness_json: Mapped[str] = mapped_column(Text, default="{}")
    blockers_json: Mapped[str] = mapped_column(Text, default="[]")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    generated_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class LoadPlanReadinessExport(Base, TimestampMixin):
    __tablename__ = "load_plan_readiness_exports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    readiness_id: Mapped[str] = mapped_column(ForeignKey("load_plan_cutover_readiness.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="EXPORTED", index=True)
    artifact_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    manifest_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    exported_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    exported_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
