from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from otm_workbench.catalog.services import (
    list_dictionary_tables,
    list_schema_packs,
    list_schema_roots,
    safe_load_table,
    serialize_columns,
    serialize_schema_pack,
    serialize_schema_root,
    serialize_table_definition,
)
from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_admin, require_user
from otm_workbench.models import (
    Artifact,
    ActiveContext,
    AuditLog,
    Capability,
    Environment,
    Evidence,
    FeatureFlag,
    Job,
    JobEvent,
    Manifest,
    Profile,
    Project,
    Role,
    RoleCapability,
    User,
    UserPreference,
    UserProjectRole,
    Workspace,
    utcnow,
)
from otm_workbench.platform.audit import write_audit
from otm_workbench.platform.jobs import (
    cancel_pending_job,
    create_job as create_platform_job,
    parse_json_object,
    run_pending_job,
    serialize_job,
    serialize_job_event,
)
from otm_workbench.platform.navigation import flag_enabled, navigation_items, registered_modules
from otm_workbench.platform.services import authenticate, create_session, file_sha256, resolve_artifact_storage_path

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


def dictionary_root() -> Path:
    return Path(get_settings().otm_data_dictionary_root)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    is_admin: bool


class FeatureFlagRequest(BaseModel):
    name: str
    enabled: bool
    scope: str = "global"


class WorkspaceCreate(BaseModel):
    name: str


class ProjectCreate(BaseModel):
    workspace_id: str
    name: str


class ProfileCreate(BaseModel):
    project_id: str
    name: str


class EnvironmentCreate(BaseModel):
    project_id: str
    name: str
    environment_type: str = "DEV"


class ActiveContextUpdate(BaseModel):
    project_id: str | None = None
    profile_id: str | None = None
    environment_id: str | None = None
    domain_name: str | None = None
    can_view_all_domains: bool = False


class UserPreferencesPayload(BaseModel):
    theme_mode: Literal["light", "dark", "system"] = "light"
    follow_system_theme: bool = False
    density: Literal["comfortable", "compact"] = "comfortable"
    sidebar_mode: Literal["expanded", "collapsed"] = "expanded"

    @model_validator(mode="after")
    def validate_system_theme_consistency(self):
        if self.follow_system_theme and self.theme_mode != "system":
            raise ValueError("follow_system_theme requires theme_mode=system.")
        if self.theme_mode == "system" and not self.follow_system_theme:
            raise ValueError("theme_mode=system requires follow_system_theme=true.")
        return self


class IdNameResponse(BaseModel):
    id: str
    name: str


class ModuleResponse(BaseModel):
    id: str
    display_name: str
    route_base: str
    status: str
    label_key: str
    description: str
    icon_key: str
    icon_family: str
    icon_variant: str
    icon_style: str
    icon_name: str


class NavigationItem(BaseModel):
    id: str
    label: str
    label_key: str
    description: str
    path: str
    status: str
    icon_key: str
    icon_family: str
    icon_variant: str
    icon_style: str
    icon_name: str
    icon_light_ref: dict[str, object]
    icon_dark_ref: dict[str, object]


def allowed_domains_for_context(domain_name: str | None, can_view_all_domains: bool) -> list[str]:
    if can_view_all_domains:
        return ["*"]
    domains = ["PUBLIC"]
    if domain_name and domain_name.upper() not in domains:
        domains.append(domain_name.upper())
    return domains


def serialize_active_context(context: ActiveContext | None, user: User) -> dict[str, object]:
    domain_name = context.domain_name if context and context.domain_name else None
    can_view_all_domains = bool(context and context.can_view_all_domains)
    return {
        "user_id": user.id,
        "project_id": context.project_id if context else None,
        "profile_id": context.profile_id if context else None,
        "environment_id": context.environment_id if context else None,
        "domain_name": domain_name,
        "allowed_domains": allowed_domains_for_context(domain_name, can_view_all_domains),
        "can_view_all_domains": can_view_all_domains,
    }


def default_user_preferences(user: User) -> UserPreference:
    return UserPreference(
        user_id=user.id,
        theme_mode="light",
        follow_system_theme=False,
        density="comfortable",
        sidebar_mode="expanded",
    )


def serialize_user_preferences(preferences: UserPreference) -> dict[str, object]:
    return {
        "theme_mode": preferences.theme_mode,
        "follow_system_theme": preferences.follow_system_theme,
        "density": preferences.density,
        "sidebar_mode": preferences.sidebar_mode,
    }


def project_setup_status_payload(db: Session, project_id: str, user: User) -> dict[str, object]:
    project = db.get(Project, project_id)
    if project is None:
        raise api_error(404, "PROJECT_NOT_FOUND", "Project not found.")
    profile_count = db.query(Profile).filter(Profile.project_id == project_id).count()
    environment_count = db.query(Environment).filter(Environment.project_id == project_id).count()
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    active_context_selected = bool(active_context and active_context.project_id == project_id)
    missing_requirements = []
    if profile_count == 0:
        missing_requirements.append("PROFILE")
    if environment_count == 0:
        missing_requirements.append("ENVIRONMENT")
    if not active_context_selected:
        missing_requirements.append("ACTIVE_CONTEXT")
    return {
        "project_id": project.id,
        "project_name": project.name,
        "status": "READY" if not missing_requirements else "INCOMPLETE",
        "profile_count": profile_count,
        "environment_count": environment_count,
        "active_context_selected": active_context_selected,
        "missing_requirements": missing_requirements,
    }


def available_action(
    *,
    key: str,
    label: str,
    method: str,
    href: str,
    icon_key: str,
    disabled: bool = False,
    disabled_reason: str | None = None,
    variant: str = "secondary",
) -> dict[str, object]:
    return {
        "key": key,
        "label": label,
        "method": method,
        "href": href,
        "variant": variant,
        "icon_key": icon_key,
        "disabled": disabled,
        "disabled_reason": disabled_reason,
        "requires_confirmation": False,
    }


def module_summary_payload(db: Session, user: User) -> dict[str, object]:
    items = navigation_items(db, user)
    counts_by_status: dict[str, int] = {}
    for item in items:
        status = item["status"]
        counts_by_status[status] = counts_by_status.get(status, 0) + 1
    return {
        "total": len(items),
        "counts_by_status": counts_by_status,
        "items": items,
    }


def serialize_cockpit_job(job: Job) -> dict[str, object]:
    return {
        "id": job.id,
        "job_type": job.job_type,
        "source_module": job.source_module,
        "project_id": job.project_id,
        "profile_id": job.profile_id,
        "environment_id": job.environment_id,
        "domain_name": job.domain_name,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "input_present": bool(parse_json_object(job.input_json)),
        "result_present": bool(parse_json_object(job.result_json)),
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


def serialize_dev_tools_run(job: Job) -> dict[str, object]:
    return {
        "id": job.id,
        "job_type": job.job_type,
        "source_module": job.source_module,
        "project_id": job.project_id,
        "profile_id": job.profile_id,
        "environment_id": job.environment_id,
        "domain_name": job.domain_name,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "input_present": bool(parse_json_object(job.input_json)),
        "result_present": bool(parse_json_object(job.result_json)),
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


def serialize_cockpit_artifact(artifact: Artifact) -> dict[str, object]:
    return {
        "id": artifact.id,
        "project_id": artifact.project_id,
        "source_module": artifact.source_module,
        "artifact_type": artifact.artifact_type,
        "file_name": artifact.file_name,
        "content_type": artifact.content_type,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "sensitivity_level": artifact.sensitivity_level,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
    }


def client_safe_evidence_summary(evidence: Evidence) -> dict[str, object]:
    summary = parse_json_object(evidence.summary_json)
    safe_keys = {
        "status",
        "readiness_status",
        "decision_status",
        "package_type",
        "artifact_type",
        "source_module",
        "error_count",
        "warning_count",
        "blocker_count",
        "row_count",
        "table_count",
        "file_count",
    }
    return {key: value for key, value in summary.items() if key in safe_keys}


def serialize_cockpit_evidence(evidence: Evidence) -> dict[str, object]:
    return {
        "id": evidence.id,
        "project_id": evidence.project_id,
        "source_module": evidence.source_module,
        "evidence_type": evidence.evidence_type,
        "status": evidence.status,
        "summary": client_safe_evidence_summary(evidence),
        "artifact_id": evidence.artifact_id,
        "manifest_id": evidence.manifest_id,
        "client_safe": evidence.client_safe,
        "sensitivity_level": evidence.sensitivity_level,
        "created_at": evidence.created_at.isoformat() if evidence.created_at else None,
    }


def filter_by_active_project(query, model, project_id: str | None):
    if project_id:
        return query.filter(model.project_id == project_id)
    return query


def project_cockpit_summary_payload(db: Session, user: User) -> dict[str, object]:
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    active_context_payload = serialize_active_context(active_context, user)
    project_id = active_context.project_id if active_context else None
    setup_status = project_setup_status_payload(db, project_id, user) if project_id else None
    recent_jobs = []
    recent_artifacts = []
    recent_evidence = []
    if project_id:
        recent_jobs = (
            filter_by_active_project(db.query(Job), Job, project_id).order_by(Job.created_at.desc()).limit(5).all()
        )
        recent_artifacts = (
            filter_by_active_project(db.query(Artifact), Artifact, project_id)
            .order_by(Artifact.created_at.desc())
            .limit(5)
            .all()
        )
        recent_evidence = (
            filter_by_active_project(db.query(Evidence).filter(Evidence.client_safe.is_(True)), Evidence, project_id)
            .order_by(Evidence.created_at.desc())
            .limit(5)
            .all()
        )
    status = "ready" if setup_status and setup_status["status"] == "READY" else "needs_context"
    return {
        "module_id": "home",
        "title": "Project Cockpit",
        "status": status,
        "description": "Project-level operational overview for the active OTM workbench context.",
        "active_context": active_context_payload,
        "setup_status": setup_status,
        "counts": {
            "recent_jobs": len(recent_jobs),
            "recent_artifacts": len(recent_artifacts),
            "recent_evidence": len(recent_evidence),
        },
        "module_summary": module_summary_payload(db, user),
        "recent_jobs": [serialize_cockpit_job(job) for job in recent_jobs],
        "recent_artifacts": [serialize_cockpit_artifact(artifact) for artifact in recent_artifacts],
        "recent_evidence": [serialize_cockpit_evidence(evidence) for evidence in recent_evidence],
        "available_actions": [
            available_action(
                key="set_active_context",
                label="Set active context",
                method="POST",
                href="/api/v1/platform/active-context",
                icon_key="context",
                variant="primary",
            ),
            available_action(
                key="view_jobs",
                label="View jobs",
                method="GET",
                href="/api/v1/platform/jobs",
                icon_key="activity",
            ),
            available_action(
                key="view_evidence",
                label="View evidence",
                method="GET",
                href="/api/v1/evidence-hub/evidence",
                icon_key="evidence",
            ),
        ],
    }


def dev_tools_summary_payload(db: Session, user: User) -> dict[str, object]:
    if not flag_enabled(db, "dev_tools"):
        raise api_error(403, "DEV_TOOLS_DISABLED", "Developer Tools is disabled by feature flag.")
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    active_context_payload = serialize_active_context(active_context, user)
    project_id = active_context.project_id if active_context else None
    recent_runs_query = db.query(Job).filter(Job.source_module == "dev_tools")
    if project_id:
        recent_runs_query = recent_runs_query.filter(Job.project_id == project_id)
    recent_runs = recent_runs_query.order_by(Job.created_at.desc()).limit(5).all()
    tools = [
        {
            "key": "data_dictionary",
            "label": "Data Dictionary Explorer",
            "status": "AVAILABLE",
            "href": "/dev-tools/data-dictionary",
            "required_capability": "dev_tools.data_dictionary.view",
            "disabled_reason": None,
        },
        {
            "key": "fk_catalog",
            "label": "FK Catalog Explorer",
            "status": "AVAILABLE",
            "href": "/dev-tools/fk-catalog",
            "required_capability": "dev_tools.fk_catalog.view",
            "disabled_reason": None,
        },
        {
            "key": "schema_packs",
            "label": "Schema Pack Diagnostics",
            "status": "AVAILABLE",
            "href": "/dev-tools/schema-packs",
            "required_capability": "dev_tools.schema_packs.view",
            "disabled_reason": None,
        },
        {
            "key": "environment_readiness",
            "label": "Environment Readiness",
            "status": "AVAILABLE",
            "href": "/dev-tools/environment-readiness",
            "required_capability": "dev_tools.environment_readiness.view",
            "disabled_reason": None,
        },
        {
            "key": "otm_explorer",
            "label": "Guarded OTM Explorer",
            "status": "DISABLED",
            "href": None,
            "required_capability": "dev_tools.otm_explorer.view",
            "disabled_reason": "Requires approved governed OTM connection and masking contract.",
        },
        {
            "key": "oracle_lab",
            "label": "Oracle Lab",
            "status": "DISABLED",
            "href": None,
            "required_capability": "dev_tools.oracle_lab.run",
            "disabled_reason": "Disabled until governance approves SQL lab execution.",
        },
    ]
    available_tools = [tool for tool in tools if tool["status"] == "AVAILABLE"]
    disabled_tools = [tool for tool in tools if tool["status"] == "DISABLED"]
    return {
        "module_id": "dev_tools",
        "title": "Technical Diagnostics Hub",
        "status": "guarded",
        "description": "Controlled technical diagnostics for authorized implementation support users.",
        "active_context": active_context_payload,
        "guards": [
            {
                "key": "feature_flag",
                "label": "Feature flag",
                "status": "READY",
                "message": "dev_tools is enabled.",
            },
            {
                "key": "capability",
                "label": "Capability",
                "status": "READY",
                "message": "Admin access authorizes technical diagnostics.",
            },
            {
                "key": "safe_output",
                "label": "Safe output",
                "status": "READY",
                "message": "Summary returns metadata only; raw inputs and results stay hidden.",
            },
        ],
        "counts": {
            "available_tools": len(available_tools),
            "disabled_tools": len(disabled_tools),
            "recent_runs": len(recent_runs),
        },
        "tools": tools,
        "recent_runs": [serialize_dev_tools_run(job) for job in recent_runs],
    }


def require_dev_tools_enabled(db: Session) -> None:
    if not flag_enabled(db, "dev_tools"):
        raise api_error(403, "DEV_TOOLS_DISABLED", "Developer Tools is disabled by feature flag.")


def dev_tools_data_dictionary_payload(
    db: Session,
    user: User,
    *,
    query: str | None,
    limit: int,
) -> dict[str, object]:
    require_dev_tools_enabled(db)
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    items, total = list_dictionary_tables(dictionary_root(), query=query, limit=limit)
    return {
        "module_id": "dev_tools",
        "tool_key": "data_dictionary",
        "title": "Data Dictionary Explorer",
        "status": "ready",
        "description": "Read-only technical table metadata from the backend Data Dictionary.",
        "query": query or "",
        "limit": limit,
        "total": total,
        "source_contract": "/api/v1/catalog/tables",
        "active_context": serialize_active_context(active_context, user),
        "items": items,
    }


def dev_tools_data_dictionary_table_payload(db: Session, user: User, table_name: str) -> dict[str, object]:
    require_dev_tools_enabled(db)
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    definition = safe_load_table(dictionary_root(), table_name)
    if definition is None:
        raise api_error(404, "DEV_TOOLS_DATA_DICTIONARY_TABLE_NOT_FOUND", "Data Dictionary table not found.")
    columns = serialize_columns(definition)
    return {
        "module_id": "dev_tools",
        "tool_key": "data_dictionary",
        "title": "Data Dictionary Table Detail",
        "status": "ready",
        "source_contract": "/api/v1/catalog/tables/{table_name}",
        "active_context": serialize_active_context(active_context, user),
        "table": serialize_table_definition(definition),
        "columns": columns,
        "column_total": len(columns),
    }


def dev_tools_fk_catalog_payload(
    db: Session,
    user: User,
    *,
    source_table: str,
    limit: int,
) -> dict[str, object]:
    require_dev_tools_enabled(db)
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    normalized_table = source_table.strip().upper()
    definition = safe_load_table(dictionary_root(), normalized_table)
    if definition is None:
        raise api_error(404, "DEV_TOOLS_FK_SOURCE_TABLE_NOT_FOUND", "FK Catalog source table not found.")
    max_items = max(1, min(limit, 200))
    items = [
        {
            "source_table_name": definition.table_name,
            "column_name": foreign_key.column_name,
            "parent_table_name": foreign_key.parent_table_name,
            "parent_column_name": foreign_key.parent_column_name,
            "relationship_type": "FOREIGN_KEY",
            "parent_table_href": f"/dev-tools/data-dictionary/tables/{foreign_key.parent_table_name}",
        }
        for foreign_key in definition.foreign_keys[:max_items]
    ]
    return {
        "module_id": "dev_tools",
        "tool_key": "fk_catalog",
        "title": "FK Catalog Explorer",
        "status": "ready",
        "description": "Read-only foreign-key relationships from the backend Data Dictionary.",
        "source_table": definition.table_name,
        "limit": limit,
        "total": len(definition.foreign_keys),
        "source_contract": f"/api/v1/catalog/tables/{definition.table_name}",
        "active_context": serialize_active_context(active_context, user),
        "items": items,
    }


def dev_tools_schema_packs_payload(
    db: Session,
    user: User,
    *,
    otm_version: str | None,
    code: str | None,
    status: str | None,
    limit: int,
) -> dict[str, object]:
    require_dev_tools_enabled(db)
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    max_items = max(1, min(limit, 100))
    packs = list_schema_packs(db, otm_version=otm_version, status=status)
    if code:
        normalized_code = code.upper()
        packs = [pack for pack in packs if pack.code == normalized_code]
    items = []
    for pack in packs[:max_items]:
        roots = list_schema_roots(db, schema_pack_id=pack.id)
        pack_payload = serialize_schema_pack(pack)
        pack_payload["root_preview"] = [serialize_schema_root(root) for root in roots[:5]]
        pack_payload["root_total"] = len(roots)
        items.append(pack_payload)
    return {
        "module_id": "dev_tools",
        "tool_key": "schema_packs",
        "title": "Schema Pack Diagnostics",
        "status": "ready",
        "description": "Read-only WSDL/XSD schema-pack diagnostics from Catalog Core.",
        "otm_version": otm_version.upper() if otm_version else "",
        "code": code.upper() if code else "",
        "filter_status": status.upper() if status else "",
        "limit": max_items,
        "total": len(packs),
        "source_contract": "/api/v1/catalog/schema-packs",
        "root_contract": "/api/v1/catalog/schema-roots",
        "active_context": serialize_active_context(active_context, user),
        "items": items,
    }


def dev_tools_environment_readiness_payload(db: Session, user: User) -> dict[str, object]:
    require_dev_tools_enabled(db)
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    active_context_payload = serialize_active_context(active_context, user)
    project_id = active_context.project_id if active_context else None
    active_environment_id = active_context.environment_id if active_context else None
    environments = []
    if project_id:
        environment_rows = db.query(Environment).filter(Environment.project_id == project_id).order_by(Environment.name).all()
        environments = [
            {
                "id": environment.id,
                "name": environment.name,
                "environment_type": environment.environment_type,
                "status": "ACTIVE" if environment.id == active_environment_id else "AVAILABLE",
                "is_active": environment.id == active_environment_id,
            }
            for environment in environment_rows
        ]

    checks = [
        {
            "key": "active_project",
            "label": "Active project",
            "status": "READY" if project_id else "BLOCKED",
            "message": "Project context is selected." if project_id else "Select a project before running environment diagnostics.",
        },
        {
            "key": "active_profile",
            "label": "Active profile",
            "status": "READY" if active_context and active_context.profile_id else "BLOCKED",
            "message": "Profile context is selected."
            if active_context and active_context.profile_id
            else "Select a profile before running environment diagnostics.",
        },
        {
            "key": "active_environment",
            "label": "Active environment",
            "status": "READY" if active_environment_id else "BLOCKED",
            "message": "Environment context is selected."
            if active_environment_id
            else "Select an environment before running environment diagnostics.",
        },
        {
            "key": "domain_scope",
            "label": "Domain scope",
            "status": "READY" if active_context and active_context.domain_name else "BLOCKED",
            "message": "Domain scope is set."
            if active_context and active_context.domain_name
            else "Set a domain scope before running environment diagnostics.",
        },
    ]
    ready_checks = len([check for check in checks if check["status"] == "READY"])
    blocked_checks = len(checks) - ready_checks
    return {
        "module_id": "dev_tools",
        "tool_key": "environment_readiness",
        "title": "Environment Readiness",
        "status": "ready" if blocked_checks == 0 else "needs_context",
        "description": "Read-only environment readiness checks for the active implementation context.",
        "active_context": active_context_payload,
        "active_environment_id": active_environment_id,
        "counts": {
            "environments": len(environments),
            "ready_checks": ready_checks,
            "blocked_checks": blocked_checks,
        },
        "environments": environments,
        "checks": checks,
        "source_contract": "/api/v1/platform/active-context",
    }


def effective_capabilities_payload(db: Session, user: User) -> dict[str, object]:
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    project_id = active_context.project_id if active_context else None
    if user.is_admin:
        return {
            "user_id": user.id,
            "project_id": project_id,
            "is_admin": True,
            "roles": ["ADMIN"],
            "capabilities": ["*"],
        }
    if not project_id:
        return {
            "user_id": user.id,
            "project_id": None,
            "is_admin": False,
            "roles": [],
            "capabilities": [],
        }
    rows = (
        db.query(Role, Capability)
        .join(UserProjectRole, UserProjectRole.role_id == Role.id)
        .join(RoleCapability, RoleCapability.role_id == Role.id)
        .join(Capability, Capability.id == RoleCapability.capability_id)
        .filter(UserProjectRole.user_id == user.id, UserProjectRole.project_id == project_id)
        .all()
    )
    roles = sorted({role.name for role, _capability in rows})
    capabilities = sorted({capability.name for _role, capability in rows})
    return {
        "user_id": user.id,
        "project_id": project_id,
        "is_admin": False,
        "roles": roles,
        "capabilities": capabilities,
    }


class JobCreate(BaseModel):
    job_type: str
    source_module: str
    project_id: str | None = None
    profile_id: str | None = None
    environment_id: str | None = None
    domain_name: str | None = None
    input: dict[str, object] = Field(default_factory=dict)
    input_json: str | None = None
    execute_now: bool = False


class ArtifactCreate(BaseModel):
    source_module: str
    artifact_type: str
    file_path: str
    file_name: str
    content_type: str
    sensitivity_level: str = "internal"


class ManifestCreate(BaseModel):
    source_module: str
    manifest_json: str
    status: str = "CREATED"


class EvidenceCreate(BaseModel):
    source_module: str
    evidence_type: str
    summary_json: str
    artifact_id: str | None = None
    manifest_id: str | None = None


@router.post("/session/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate(db, payload.email, payload.password)
    if not user:
        raise api_error(401, "UNAUTHENTICATED", "Invalid email or password.")
    session = create_session(db, user)
    return TokenResponse(access_token=session.token)


@router.get("/session/me", response_model=CurrentUserResponse)
def me(user: User = Depends(require_user)) -> CurrentUserResponse:
    return CurrentUserResponse(id=user.id, email=user.email, is_admin=user.is_admin)


@router.post("/feature-flags")
def upsert_feature_flag(
    payload: FeatureFlagRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    flag = db.query(FeatureFlag).filter(FeatureFlag.name == payload.name).first()
    if not flag:
        flag = FeatureFlag(name=payload.name, enabled=payload.enabled, scope=payload.scope)
        db.add(flag)
    else:
        flag.enabled = payload.enabled
        flag.scope = payload.scope
    db.commit()
    db.refresh(flag)
    write_audit(db, user, "feature_flag.upsert", "feature_flag", flag.id)
    return {"id": flag.id, "name": flag.name, "enabled": flag.enabled, "scope": flag.scope}


@router.get("/feature-flags")
def list_feature_flags(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    flags = db.query(FeatureFlag).order_by(FeatureFlag.name).all()
    items = [{"id": flag.id, "name": flag.name, "enabled": flag.enabled, "scope": flag.scope} for flag in flags]
    return PageResponse(items=items, total=len(items))


@router.post("/workspaces", response_model=IdNameResponse)
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> IdNameResponse:
    workspace = Workspace(name=payload.name)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return IdNameResponse(id=workspace.id, name=workspace.name)


@router.get("/workspaces", response_model=list[IdNameResponse])
def list_workspaces(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
) -> list[IdNameResponse]:
    return [IdNameResponse(id=item.id, name=item.name) for item in db.query(Workspace).all()]


@router.post("/projects", response_model=IdNameResponse)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> IdNameResponse:
    project = Project(workspace_id=payload.workspace_id, name=payload.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return IdNameResponse(id=project.id, name=project.name)


@router.get("/projects", response_model=PageResponse[IdNameResponse])
def list_projects(
    workspace_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
) -> PageResponse[IdNameResponse]:
    query = db.query(Project)
    if workspace_id:
        query = query.filter(Project.workspace_id == workspace_id)
    projects = query.order_by(Project.name).all()
    items = [IdNameResponse(id=item.id, name=item.name) for item in projects]
    return PageResponse(items=items, total=len(items))


@router.get("/projects/{project_id}/setup-status")
def get_project_setup_status(
    project_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    return project_setup_status_payload(db, project_id, user)


@router.post("/profiles", response_model=IdNameResponse)
def create_profile(
    payload: ProfileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> IdNameResponse:
    profile = Profile(project_id=payload.project_id, name=payload.name)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return IdNameResponse(id=profile.id, name=profile.name)


@router.get("/profiles", response_model=PageResponse[IdNameResponse])
def list_profiles(
    project_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
) -> PageResponse[IdNameResponse]:
    query = db.query(Profile)
    if project_id:
        query = query.filter(Profile.project_id == project_id)
    profiles = query.order_by(Profile.name).all()
    items = [IdNameResponse(id=item.id, name=item.name) for item in profiles]
    return PageResponse(items=items, total=len(items))


@router.post("/environments", response_model=IdNameResponse)
def create_environment(
    payload: EnvironmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> IdNameResponse:
    environment = Environment(
        project_id=payload.project_id,
        name=payload.name,
        environment_type=payload.environment_type,
    )
    db.add(environment)
    db.commit()
    db.refresh(environment)
    return IdNameResponse(id=environment.id, name=environment.name)


@router.get("/environments", response_model=PageResponse[IdNameResponse])
def list_environments(
    project_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
) -> PageResponse[IdNameResponse]:
    query = db.query(Environment)
    if project_id:
        query = query.filter(Environment.project_id == project_id)
    environments = query.order_by(Environment.name).all()
    items = [IdNameResponse(id=item.id, name=item.name) for item in environments]
    return PageResponse(items=items, total=len(items))


@router.get("/active-context")
def get_active_context(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    return serialize_active_context(context, user)


@router.get("/active-context/capabilities")
def get_active_context_capabilities(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    return effective_capabilities_payload(db, user)


@router.get("/user-preferences")
def get_user_preferences(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    preferences = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    if preferences is None:
        preferences = default_user_preferences(user)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    return serialize_user_preferences(preferences)


@router.put("/user-preferences")
def update_user_preferences(
    payload: UserPreferencesPayload,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    preferences = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    if preferences is None:
        preferences = default_user_preferences(user)
        db.add(preferences)
    preferences.theme_mode = payload.theme_mode
    preferences.follow_system_theme = payload.follow_system_theme
    preferences.density = payload.density
    preferences.sidebar_mode = payload.sidebar_mode
    preferences.updated_at = utcnow()
    db.commit()
    db.refresh(preferences)
    write_audit(db, user, "user_preferences.update", "user_preference", preferences.id)
    return serialize_user_preferences(preferences)


@router.post("/active-context")
def set_active_context(
    payload: ActiveContextUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    if payload.project_id and db.get(Project, payload.project_id) is None:
        raise api_error(400, "ACTIVE_CONTEXT_INVALID_PROJECT", "Project not found.")
    if payload.profile_id and db.get(Profile, payload.profile_id) is None:
        raise api_error(400, "ACTIVE_CONTEXT_INVALID_PROFILE", "Profile not found.")
    if payload.environment_id and db.get(Environment, payload.environment_id) is None:
        raise api_error(400, "ACTIVE_CONTEXT_INVALID_ENVIRONMENT", "Environment not found.")

    context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    if context is None:
        context = ActiveContext(user_id=user.id)
        db.add(context)
    context.project_id = payload.project_id
    context.profile_id = payload.profile_id
    context.environment_id = payload.environment_id
    context.domain_name = payload.domain_name.upper() if payload.domain_name else None
    context.can_view_all_domains = payload.can_view_all_domains
    db.commit()
    db.refresh(context)
    write_audit(db, user, "active_context.update", "active_context", context.id)
    return serialize_active_context(context, user)


@router.get("/project-cockpit/summary")
def get_project_cockpit_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    return project_cockpit_summary_payload(db, user)


@router.get("/dev-tools/summary")
def get_dev_tools_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    return dev_tools_summary_payload(db, user)


@router.get("/dev-tools/data-dictionary")
def get_dev_tools_data_dictionary(
    query: str | None = None,
    limit: int = 25,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    return dev_tools_data_dictionary_payload(db, user, query=query, limit=limit)


@router.get("/dev-tools/data-dictionary/tables/{table_name}")
def get_dev_tools_data_dictionary_table(
    table_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    return dev_tools_data_dictionary_table_payload(db, user, table_name)


@router.get("/dev-tools/fk-catalog")
def get_dev_tools_fk_catalog(
    source_table: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    return dev_tools_fk_catalog_payload(db, user, source_table=source_table, limit=limit)


@router.get("/dev-tools/schema-packs")
def get_dev_tools_schema_packs(
    otm_version: str | None = None,
    code: str | None = None,
    status: str | None = None,
    limit: int = 25,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    return dev_tools_schema_packs_payload(db, user, otm_version=otm_version, code=code, status=status, limit=limit)


@router.get("/dev-tools/environment-readiness")
def get_dev_tools_environment_readiness(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    return dev_tools_environment_readiness_payload(db, user)


@router.get("/modules", response_model=PageResponse[ModuleResponse])
def list_modules(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
) -> PageResponse[ModuleResponse]:
    modules = registered_modules(db)
    items = [
        ModuleResponse(
            id=item.id,
            display_name=item.display_name,
            route_base=item.route_base,
            status=item.status,
            label_key=item.label_key,
            description=item.description,
            icon_key=item.icon_key,
            icon_family=item.icon_family,
            icon_variant=item.icon_variant,
            icon_style=item.icon_style,
            icon_name=item.icon_name,
        )
        for item in modules
    ]
    return PageResponse(items=items, total=len(items))


@router.get("/navigation", response_model=PageResponse[NavigationItem])
def navigation(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
) -> PageResponse[NavigationItem]:
    items = [NavigationItem(**item) for item in navigation_items(db, user)]
    return PageResponse(items=items, total=len(items))


@router.post("/jobs")
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    try:
        input_payload = parse_json_object(payload.input_json) if payload.input_json is not None else payload.input
        job = create_platform_job(
            db,
            job_type=payload.job_type,
            source_module=payload.source_module,
            project_id=payload.project_id,
            profile_id=payload.profile_id,
            environment_id=payload.environment_id,
            domain_name=payload.domain_name,
            input_payload=input_payload,
            execute_now=payload.execute_now,
            created_by=user.email,
        )
    except ValueError as exc:
        raise api_error(400, "JOB_INVALID", str(exc)) from exc
    return serialize_job(job)


@router.get("/jobs")
def list_jobs(
    source_module: str | None = None,
    job_type: str | None = None,
    status: str | None = None,
    project_id: str | None = None,
    profile_id: str | None = None,
    environment_id: str | None = None,
    domain_name: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(Job)
    if source_module:
        query = query.filter(Job.source_module == source_module)
    if job_type:
        query = query.filter(Job.job_type == job_type.upper())
    if status:
        query = query.filter(Job.status == status.upper())
    if project_id:
        query = query.filter(Job.project_id == project_id)
    if profile_id:
        query = query.filter(Job.profile_id == profile_id)
    if environment_id:
        query = query.filter(Job.environment_id == environment_id)
    if domain_name:
        query = query.filter(Job.domain_name == domain_name.upper())
    jobs = query.order_by(Job.created_at.desc()).all()
    return PageResponse(items=[serialize_job(job) for job in jobs], total=len(jobs))


@router.get("/jobs/{job_id}")
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise api_error(404, "JOB_NOT_FOUND", "Job not found.")
    return serialize_job(job)


@router.post("/jobs/{job_id}/cancel")
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise api_error(404, "JOB_NOT_FOUND", "Job not found.")
    try:
        return serialize_job(cancel_pending_job(db, job=job, actor=user.email))
    except ValueError as exc:
        raise api_error(400, "JOB_INVALID_TRANSITION", str(exc)) from exc


@router.post("/jobs/{job_id}/run")
def run_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise api_error(404, "JOB_NOT_FOUND", "Job not found.")
    try:
        return serialize_job(run_pending_job(db, job=job, actor=user.email))
    except ValueError as exc:
        raise api_error(400, "JOB_INVALID_TRANSITION", str(exc)) from exc


@router.get("/jobs/{job_id}/events")
def list_job_events(
    job_id: str,
    event_type: str | None = None,
    status_after: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise api_error(404, "JOB_NOT_FOUND", "Job not found.")
    query = db.query(JobEvent).filter(JobEvent.job_id == job.id)
    if event_type:
        query = query.filter(JobEvent.event_type == event_type.upper())
    if status_after:
        query = query.filter(JobEvent.status_after == status_after.upper())
    events = query.order_by(JobEvent.created_at).all()
    return PageResponse(items=[serialize_job_event(event) for event in events], total=len(events))


@router.post("/artifacts")
def create_artifact(
    payload: ArtifactCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    try:
        artifact_path = resolve_artifact_storage_path(payload.file_path)
    except ValueError as exc:
        raise api_error(
            400,
            "ARTIFACT_PATH_OUTSIDE_ROOT",
            "Artifact file must be inside the configured artifact root.",
        ) from exc
    if not artifact_path.exists() or not artifact_path.is_file():
        raise api_error(404, "ARTIFACT_FILE_NOT_FOUND", "Artifact file not found.")
    digest, size = file_sha256(str(artifact_path))
    artifact = Artifact(
        source_module=payload.source_module,
        artifact_type=payload.artifact_type,
        file_path=str(artifact_path),
        file_name=payload.file_name,
        content_type=payload.content_type,
        sha256=digest,
        size_bytes=size,
        sensitivity_level=payload.sensitivity_level,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return {"id": artifact.id, "sha256": artifact.sha256, "size_bytes": artifact.size_bytes}


@router.post("/manifests")
def create_manifest(
    payload: ManifestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    manifest = Manifest(
        source_module=payload.source_module,
        manifest_json=payload.manifest_json,
        status=payload.status,
    )
    db.add(manifest)
    db.commit()
    db.refresh(manifest)
    return {"id": manifest.id, "status": manifest.status}


@router.post("/evidence")
def create_evidence(
    payload: EvidenceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    evidence = Evidence(
        source_module=payload.source_module,
        evidence_type=payload.evidence_type,
        summary_json=payload.summary_json,
        artifact_id=payload.artifact_id,
        manifest_id=payload.manifest_id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return {"id": evidence.id, "client_safe": evidence.client_safe, "status": evidence.status}


@router.get("/audit-logs")
def list_audit_logs(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()
    items = [
        {
            "id": item.id,
            "action": item.action,
            "target_type": item.target_type,
            "target_id": item.target_id,
        }
        for item in logs
    ]
    return PageResponse(items=items, total=len(items))
