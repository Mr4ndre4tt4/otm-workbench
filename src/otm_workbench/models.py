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


class ActiveContext(Base, TimestampMixin):
    __tablename__ = "active_contexts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    profile_id: Mapped[str | None] = mapped_column(ForeignKey("profiles.id"), nullable=True)
    environment_id: Mapped[str | None] = mapped_column(ForeignKey("environments.id"), nullable=True)
    domain_name: Mapped[str | None] = mapped_column(String, nullable=True)
    can_view_all_domains: Mapped[bool] = mapped_column(Boolean, default=False)


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
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True)
    domain_name: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text, default="")
    input_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    error_code: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class JobEvent(Base):
    __tablename__ = "job_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    event_type: Mapped[str] = mapped_column(String, index=True)
    status_before: Mapped[str | None] = mapped_column(String, nullable=True)
    status_after: Mapped[str | None] = mapped_column(String, nullable=True)
    message: Mapped[str] = mapped_column(Text, default="")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


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


class AssetClassification(Base, TimestampMixin):
    __tablename__ = "asset_classifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    classification_type: Mapped[str] = mapped_column(String, index=True)
    code: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    system_protected: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    asset_type: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    visibility: Mapped[str] = mapped_column(String, index=True)
    scope_type: Mapped[str] = mapped_column(String, index=True)
    sensitivity: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="DRAFT", index=True)
    module_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    macro_object_code: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    otm_table_name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    current_version_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class AssetVersion(Base, TimestampMixin):
    __tablename__ = "asset_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String, default="CURRENT", index=True)
    file_name: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String)
    storage_path: Mapped[str] = mapped_column(String)
    sha256: Mapped[str] = mapped_column(String, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    uploaded_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class AssetLink(Base, TimestampMixin):
    __tablename__ = "asset_links"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    link_type: Mapped[str] = mapped_column(String, index=True)
    target_id: Mapped[str] = mapped_column(String, index=True)
    target_label: Mapped[str] = mapped_column(String, default="")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class OrderReleaseTemplate(Base, TimestampMixin):
    __tablename__ = "order_release_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer, default=1, index=True)
    status: Mapped[str] = mapped_column(String, default="DRAFT", index=True)
    macro_object_code: Mapped[str] = mapped_column(String, default="ORDER_RELEASE", index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    required_columns_json: Mapped[str] = mapped_column(Text, default="[]")
    optional_columns_json: Mapped[str] = mapped_column(Text, default="[]")
    defaults_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class OrderReleaseBatch(Base, TimestampMixin):
    __tablename__ = "order_release_batches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    template_id: Mapped[str] = mapped_column(ForeignKey("order_release_templates.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="PARSED", index=True)
    file_name: Mapped[str] = mapped_column(String)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    release_count: Mapped[int] = mapped_column(Integer, default=0)
    issue_count: Mapped[int] = mapped_column(Integer, default=0)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class OrderReleaseBatchRow(Base, TimestampMixin):
    __tablename__ = "order_release_batch_rows"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("order_release_batches.id"), index=True)
    row_number: Mapped[int] = mapped_column(Integer, index=True)
    release_gid: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, default="VALID", index=True)
    normalized_json: Mapped[str] = mapped_column(Text, default="{}")
    issues_json: Mapped[str] = mapped_column(Text, default="[]")


class IntegrationDefinition(Base, TimestampMixin):
    __tablename__ = "integration_definitions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    source_system: Mapped[str] = mapped_column(String, index=True)
    target_system: Mapped[str] = mapped_column(String, index=True)
    source_format: Mapped[str] = mapped_column(String, index=True)
    target_format: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="DRAFT", index=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class IntegrationSystem(Base, TimestampMixin):
    __tablename__ = "integration_systems"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    system_type: Mapped[str] = mapped_column(String, index=True)
    base_url: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="ACTIVE", index=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class IntegrationEndpoint(Base, TimestampMixin):
    __tablename__ = "integration_endpoints"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    system_id: Mapped[str] = mapped_column(ForeignKey("integration_systems.id"), index=True)
    code: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    path: Mapped[str] = mapped_column(String)
    method: Mapped[str] = mapped_column(String, index=True)
    payload_format: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="ACTIVE", index=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class IntegrationPayloadArtifact(Base, TimestampMixin):
    __tablename__ = "integration_payload_artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    definition_id: Mapped[str] = mapped_column(ForeignKey("integration_definitions.id"), index=True)
    artifact_id: Mapped[str] = mapped_column(ForeignKey("artifacts.id"), index=True)
    payload_role: Mapped[str] = mapped_column(String, index=True)
    payload_format: Mapped[str] = mapped_column(String, index=True)
    file_name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class MasterDataTemplate(Base, TimestampMixin):
    __tablename__ = "master_data_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="DRAFT")
    catalog_macro_object_code: Mapped[str] = mapped_column(String, index=True)
    data_category: Mapped[str] = mapped_column(String, default="MASTER_DATA")
    target_tables_json: Mapped[str] = mapped_column(Text, default="[]")
    sheets_json: Mapped[str] = mapped_column(Text, default="[]")
    description: Mapped[str] = mapped_column(Text, default="")


class MasterDataBatch(Base, TimestampMixin):
    __tablename__ = "master_data_batches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    template_id: Mapped[str] = mapped_column(ForeignKey("master_data_templates.id"), index=True)
    template_code: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="PARSED")
    file_name: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String)
    sheet_summaries_json: Mapped[str] = mapped_column(Text, default="[]")
    parsed_rows_json: Mapped[str] = mapped_column(Text, default="{}")
    issues_json: Mapped[str] = mapped_column(Text, default="[]")
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    issue_count: Mapped[int] = mapped_column(Integer, default=0)


class MasterDataCanonicalRecord(Base, TimestampMixin):
    __tablename__ = "master_data_canonical_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("master_data_batches.id"), index=True)
    template_code: Mapped[str] = mapped_column(String, index=True)
    sheet_code: Mapped[str] = mapped_column(String, index=True)
    target_table: Mapped[str] = mapped_column(String, index=True)
    record_index: Mapped[int] = mapped_column(Integer)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")


class MasterDataOutputRecord(Base, TimestampMixin):
    __tablename__ = "master_data_output_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("master_data_batches.id"), index=True)
    template_code: Mapped[str] = mapped_column(String, index=True)
    target_table: Mapped[str] = mapped_column(String, index=True)
    record_index: Mapped[int] = mapped_column(Integer)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")


class MasterDataCsvFile(Base, TimestampMixin):
    __tablename__ = "master_data_csv_files"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("master_data_batches.id"), index=True)
    template_code: Mapped[str] = mapped_column(String, index=True)
    table_name: Mapped[str] = mapped_column(String, index=True)
    file_name: Mapped[str] = mapped_column(String)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text, default="")


class MasterDataCoordinateQualityBatch(Base, TimestampMixin):
    __tablename__ = "master_data_coordinate_quality_batches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    source_type: Mapped[str] = mapped_column(String, default="api")
    source_batch_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, default="PROCESSED", index=True)
    geocoder_base_url: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_mode: Mapped[str] = mapped_column(String, default="fake")
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    ok_count: Mapped[int] = mapped_column(Integer, default=0)
    corrected_count: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    divergent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    input_json: Mapped[str] = mapped_column(Text, default="[]")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    issues_json: Mapped[str] = mapped_column(Text, default="[]")


class MasterDataCoordinateQualityResult(Base, TimestampMixin):
    __tablename__ = "master_data_coordinate_quality_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(
        ForeignKey("master_data_coordinate_quality_batches.id"), index=True
    )
    location_gid: Mapped[str] = mapped_column(String, index=True)
    location_name: Mapped[str | None] = mapped_column(String, nullable=True)
    address_json: Mapped[str] = mapped_column(Text, default="{}")
    country_code3_gid: Mapped[str | None] = mapped_column(String, nullable=True)
    province_code: Mapped[str | None] = mapped_column(String, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String, nullable=True)
    lat_orig: Mapped[str | None] = mapped_column(String, nullable=True)
    lon_orig: Mapped[str | None] = mapped_column(String, nullable=True)
    lat_new: Mapped[str | None] = mapped_column(String, nullable=True)
    lon_new: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    diff_lat: Mapped[str | None] = mapped_column(String, nullable=True)
    diff_lon: Mapped[str | None] = mapped_column(String, nullable=True)
    orig_valid_uf: Mapped[bool] = mapped_column(Boolean, default=False)
    new_valid_uf: Mapped[bool] = mapped_column(Boolean, default=False)
    issue_json: Mapped[str] = mapped_column(Text, default="{}")


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


class OtmMacroObject(Base, TimestampMixin):
    __tablename__ = "otm_macro_objects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    default_load_order: Mapped[int] = mapped_column(Integer, default=0)
    default_method: Mapped[str] = mapped_column(String, default="NA")
    method_options_json: Mapped[str] = mapped_column(Text, default="[]")
    allow_cutover: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_csvutil: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_required_default: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class OtmMacroObjectTable(Base, TimestampMixin):
    __tablename__ = "otm_macro_object_tables"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    macro_object_id: Mapped[str] = mapped_column(ForeignKey("otm_macro_objects.id"), index=True)
    table_name: Mapped[str] = mapped_column(String, index=True)
    relationship_role: Mapped[str] = mapped_column(String, default="RELATED")
    is_primary_table: Mapped[bool] = mapped_column(Boolean, default=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    data_category: Mapped[str] = mapped_column(String, default="UNKNOWN")
    validated_by_datadict: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_csvutil: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_cutover: Mapped[bool] = mapped_column(Boolean, default=False)


class OtmMacroObjectDependency(Base, TimestampMixin):
    __tablename__ = "otm_macro_object_dependencies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    macro_object_id: Mapped[str] = mapped_column(ForeignKey("otm_macro_objects.id"), index=True)
    depends_on_macro_object_id: Mapped[str] = mapped_column(ForeignKey("otm_macro_objects.id"), index=True)
    dependency_type: Mapped[str] = mapped_column(String, default="MUST_LOAD_BEFORE")
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")


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


class CutoverChecklistTemplate(Base, TimestampMixin):
    __tablename__ = "cutover_checklist_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="PUBLISHED", index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    system_seeded: Mapped[bool] = mapped_column(Boolean, default=True)


class CutoverChecklistTemplateItem(Base, TimestampMixin):
    __tablename__ = "cutover_checklist_template_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    template_id: Mapped[str] = mapped_column(ForeignKey("cutover_checklist_templates.id"), index=True)
    item_code: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    default_method: Mapped[str] = mapped_column(String, default="REVIEW")
    applies_to_package_type: Mapped[str] = mapped_column(String, default="*")
    required_evidence_type: Mapped[str | None] = mapped_column(String, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)


class CutoverChecklist(Base, TimestampMixin):
    __tablename__ = "cutover_checklists"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    template_id: Mapped[str] = mapped_column(ForeignKey("cutover_checklist_templates.id"), index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="DRAFT", index=True)
    package_type: Mapped[str] = mapped_column(String, index=True)
    catalog_macro_object_code: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class CutoverChecklistItem(Base, TimestampMixin):
    __tablename__ = "cutover_checklist_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    checklist_id: Mapped[str] = mapped_column(ForeignKey("cutover_checklists.id"), index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    template_item_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    item_code: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="PENDING", index=True)
    method: Mapped[str] = mapped_column(String, default="REVIEW", index=True)
    table_name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    evidence_required: Mapped[bool] = mapped_column(Boolean, default=True)
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}")


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


class LoadPlanCutoverHandoff(Base, TimestampMixin):
    __tablename__ = "load_plan_cutover_handoffs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    readiness_id: Mapped[str] = mapped_column(ForeignKey("load_plan_cutover_readiness.id"), index=True)
    readiness_export_id: Mapped[str] = mapped_column(ForeignKey("load_plan_readiness_exports.id"), index=True)
    archive_evidence_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="READY_FOR_CUTOVER", index=True)
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    committed_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    committed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
