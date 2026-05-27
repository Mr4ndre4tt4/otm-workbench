from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import or_
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
    AccessPolicy,
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
from otm_workbench.platform.scoping import (
    OperationalScope,
    apply_operational_scope,
    normalize_domain_for_visibility,
    normalize_domain_name,
    normalize_visibility,
    operational_scope_from_context,
)
from otm_workbench.platform.services import authenticate, create_session, file_sha256, resolve_artifact_storage_path
from otm_workbench.security import hash_password

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


class UserCreate(BaseModel):
    email: str
    password: str
    is_active: bool = True


class RoleCreate(BaseModel):
    name: str
    capability_names: list[str] = Field(default_factory=list)


class GrantCreate(BaseModel):
    project_id: str
    environment_id: str | None = None
    domain_name: str | None = None
    user_id: str
    role_id: str


class AccessPolicyCreate(BaseModel):
    project_id: str | None = None
    name: str
    visibility: str = "PRIVATE"
    domain_name: str | None = None
    rule_json: str = "{}"


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
    scope = OperationalScope(domain_name=(domain_name or "PUBLIC").upper(), can_view_all_domains=can_view_all_domains)
    return list(scope.allowed_domain_names)


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


def capability_names_for_project(
    db: Session,
    user: User,
    project_id: str | None,
    active_context: ActiveContext | None = None,
) -> set[str]:
    if user.is_admin:
        return {"*"}
    if not project_id:
        return set()
    domain_name = normalize_domain_name(active_context.domain_name) if active_context and active_context.domain_name else None
    environment_id = active_context.environment_id if active_context else None
    filters = [UserProjectRole.user_id == user.id, UserProjectRole.project_id == project_id]
    if active_context is not None:
        filters.extend(
            [
                or_(UserProjectRole.environment_id.is_(None), UserProjectRole.environment_id == environment_id),
                or_(UserProjectRole.domain_name.is_(None), UserProjectRole.domain_name == domain_name),
            ]
        )
    rows = (
        db.query(Capability.name)
        .join(RoleCapability, RoleCapability.capability_id == Capability.id)
        .join(Role, Role.id == RoleCapability.role_id)
        .join(UserProjectRole, UserProjectRole.role_id == Role.id)
        .filter(*filters)
        .all()
    )
    return {row[0] for row in rows}


def settings_setup_visibility(db: Session, user: User, active_context: ActiveContext | None) -> dict[str, object]:
    project_id = active_context.project_id if active_context else None
    capabilities = capability_names_for_project(db, user, project_id, active_context)
    can_manage_project_setup = "settings.project.manage" in capabilities or "*" in capabilities
    can_manage_users = "settings.users.manage" in capabilities or "*" in capabilities
    can_manage_roles = "settings.roles.manage" in capabilities or "*" in capabilities
    can_manage_grants = "settings.grants.manage" in capabilities or "*" in capabilities
    can_manage_access_policies = "settings.access_policies.manage" in capabilities or "*" in capabilities
    if user.is_admin:
        level = "GLOBAL"
    elif can_manage_project_setup or can_manage_users or can_manage_roles or can_manage_grants or can_manage_access_policies:
        level = "PROJECT"
    else:
        level = "SCOPED"
    return {
        "level": level,
        "can_manage_users": user.is_admin or can_manage_users,
        "can_manage_workspaces": user.is_admin,
        "can_manage_projects": user.is_admin,
        "can_manage_profiles": user.is_admin or can_manage_project_setup,
        "can_manage_environments": user.is_admin or can_manage_project_setup,
        "can_manage_roles": user.is_admin or can_manage_roles,
        "can_manage_grants": user.is_admin or can_manage_grants,
        "can_manage_access_policies": user.is_admin or can_manage_access_policies,
    }


def settings_setup_counts(db: Session, user: User, active_context: ActiveContext | None) -> dict[str, int]:
    if user.is_admin:
        return {
            "workspaces": db.query(Workspace).count(),
            "projects": db.query(Project).count(),
            "profiles": db.query(Profile).count(),
            "environments": db.query(Environment).count(),
        }
    project_id = active_context.project_id if active_context else None
    if not project_id:
        return {"workspaces": 0, "projects": 0, "profiles": 0, "environments": 0}
    return {
        "workspaces": 0,
        "projects": db.query(Project).filter(Project.id == project_id).count(),
        "profiles": db.query(Profile).filter(Profile.project_id == project_id).count(),
        "environments": db.query(Environment).filter(Environment.project_id == project_id).count(),
    }


def granted_project_ids(db: Session, user: User) -> set[str]:
    if user.is_admin:
        return {project_id for (project_id,) in db.query(Project.id).all()}
    return {
        project_id
        for (project_id,) in db.query(UserProjectRole.project_id).filter(UserProjectRole.user_id == user.id).distinct().all()
    }


def can_read_project_setup(db: Session, user: User, project_id: str | None) -> bool:
    if user.is_admin:
        return True
    if not project_id:
        return False
    return project_id in granted_project_ids(db, user)


def can_use_active_context(db: Session, user: User, active_context: ActiveContext | None) -> bool:
    if user.is_admin:
        return True
    if not active_context or not active_context.project_id:
        return False
    domain_name = normalize_domain_name(active_context.domain_name) if active_context.domain_name else None
    return (
        db.query(UserProjectRole.id)
        .filter(
            UserProjectRole.user_id == user.id,
            UserProjectRole.project_id == active_context.project_id,
            or_(
                UserProjectRole.environment_id.is_(None),
                UserProjectRole.environment_id == active_context.environment_id,
            ),
            or_(UserProjectRole.domain_name.is_(None), UserProjectRole.domain_name == domain_name),
        )
        .first()
        is not None
    )


def disabled_reason_for_authority(has_authority: bool, missing_reason: str | None, authority_reason: str) -> str | None:
    if not has_authority:
        return authority_reason
    return missing_reason


def active_context_for_user(db: Session, user: User) -> ActiveContext | None:
    return db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()


def require_settings_setup_authority(
    db: Session,
    user: User,
    key: str,
    error_code: str,
    project_id: str | None = None,
) -> None:
    active_context = active_context_for_user(db, user)
    visibility = settings_setup_visibility(db, user, active_context)
    if project_id and not user.is_admin:
        if not active_context or active_context.project_id != project_id:
            raise api_error(403, error_code, "Settings setup authority is limited to the active project.")
    if not visibility[key]:
        raise api_error(403, error_code, "Settings setup authority is required.")


def serialize_role(db: Session, role: Role) -> dict[str, object]:
    capabilities = (
        db.query(Capability.name)
        .join(RoleCapability, RoleCapability.capability_id == Capability.id)
        .filter(RoleCapability.role_id == role.id)
        .order_by(Capability.name)
        .all()
    )
    return {
        "id": role.id,
        "name": role.name,
        "capability_names": [capability[0] for capability in capabilities],
    }


def serialize_settings_user(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
    }


def grant_binding_guidance(
    db: Session,
    grant: UserProjectRole,
    active_context: ActiveContext | None = None,
) -> dict[str, object]:
    user = db.get(User, grant.user_id)
    role = db.get(Role, grant.role_id)
    project = db.get(Project, grant.project_id)
    environment = db.get(Environment, grant.environment_id) if grant.environment_id else None
    project_label = project.name if project else grant.project_id
    environment_label = environment.name if environment else "Any environment"
    domain_label = grant.domain_name or "Project"
    active_context_match = False
    active_context_disabled_reason = "ACTIVE_CONTEXT_REQUIRED"
    if active_context and active_context.project_id:
        project_matches = grant.project_id == active_context.project_id
        environment_matches = grant.environment_id is None or grant.environment_id == active_context.environment_id
        active_domain = normalize_domain_name(active_context.domain_name)
        domain_matches = grant.domain_name is None or active_context.can_view_all_domains or active_domain == grant.domain_name
        active_context_match = project_matches and environment_matches and domain_matches
        if active_context_match:
            active_context_disabled_reason = None
        elif not project_matches:
            active_context_disabled_reason = "ACTIVE_PROJECT_MISMATCH"
        elif not environment_matches:
            active_context_disabled_reason = "ACTIVE_ENVIRONMENT_MISMATCH"
        else:
            active_context_disabled_reason = "ACTIVE_DOMAIN_MISMATCH"
    return {
        "binding_scope_label": f"{project_label} / {environment_label} / {domain_label}",
        "binding_requirements": [
            f"User: {user.email if user else grant.user_id}",
            f"Role: {role.name if role else grant.role_id}",
            f"Project: {project_label}",
            f"Environment: {environment_label}",
            f"Domain: {domain_label}",
        ],
        "active_context_match": active_context_match,
        "active_context_disabled_reason": active_context_disabled_reason,
    }


def serialize_grant(
    db: Session,
    grant: UserProjectRole,
    active_context: ActiveContext | None = None,
) -> dict[str, object]:
    user = db.get(User, grant.user_id)
    role = db.get(Role, grant.role_id)
    project = db.get(Project, grant.project_id)
    return {
        "id": grant.id,
        "project_id": grant.project_id,
        "project_name": project.name if project else None,
        "environment_id": grant.environment_id,
        "domain_name": grant.domain_name,
        "user_id": grant.user_id,
        "user_email": user.email if user else None,
        "role_id": grant.role_id,
        "role_name": role.name if role else None,
        **grant_binding_guidance(db, grant, active_context),
    }


def access_policy_binding_guidance(
    db: Session,
    policy: AccessPolicy,
    active_context: ActiveContext | None = None,
) -> dict[str, object]:
    project = db.get(Project, policy.project_id) if policy.project_id else None
    visibility = normalize_visibility(policy.visibility)
    domain_name = normalize_domain_for_visibility(policy.domain_name, visibility)
    project_label = project.name if project else "Public View"
    domain_label = domain_name or "Project"
    active_context_match = False
    active_context_disabled_reason = "ACTIVE_CONTEXT_REQUIRED"
    if active_context and active_context.project_id:
        active_project_matches = policy.project_id == active_context.project_id
        active_domain = normalize_domain_name(active_context.domain_name)
        active_domain_matches = (
            domain_name is None
            or domain_name == "PUBLIC"
            or active_context.can_view_all_domains
            or active_domain == domain_name
        )
        active_context_match = active_project_matches and active_domain_matches
        if active_context_match:
            active_context_disabled_reason = None
        elif not active_project_matches:
            active_context_disabled_reason = "ACTIVE_PROJECT_MISMATCH"
        else:
            active_context_disabled_reason = "ACTIVE_DOMAIN_MISMATCH"
    return {
        "binding_scope_label": f"{project_label} / {visibility} / {domain_label}",
        "binding_requirements": [
            f"Project: {project_label}",
            f"Visibility: {visibility}",
            f"Domain: {domain_label}",
        ],
        "active_context_match": active_context_match,
        "active_context_disabled_reason": active_context_disabled_reason,
    }


def serialize_access_policy(
    db: Session,
    policy: AccessPolicy,
    active_context: ActiveContext | None = None,
) -> dict[str, object]:
    project = db.get(Project, policy.project_id) if policy.project_id else None
    return {
        "id": policy.id,
        "project_id": policy.project_id,
        "project_name": project.name if project else None,
        "name": policy.name,
        "visibility": policy.visibility,
        "domain_name": policy.domain_name,
        "rule_json": policy.rule_json,
        "created_by": policy.created_by,
        **access_policy_binding_guidance(db, policy, active_context),
    }


def validate_access_policy_binding(
    db: Session,
    access_policy_id: str | None,
    *,
    project_id: str | None,
    domain_name: str | None,
    visibility: str,
) -> str | None:
    if access_policy_id is None:
        return None
    policy = db.get(AccessPolicy, access_policy_id)
    if policy is None:
        raise api_error(400, "ACCESS_POLICY_NOT_FOUND", "Access policy not found.")
    normalized_visibility = normalize_visibility(visibility)
    normalized_domain = normalize_domain_for_visibility(domain_name, normalized_visibility)
    policy_visibility = normalize_visibility(policy.visibility)
    policy_domain = normalize_domain_for_visibility(policy.domain_name, policy_visibility)
    if policy.project_id != project_id:
        raise api_error(400, "ACCESS_POLICY_SCOPE_MISMATCH", "Access policy project does not match record scope.")
    if policy_visibility != normalized_visibility:
        raise api_error(400, "ACCESS_POLICY_SCOPE_MISMATCH", "Access policy visibility does not match record scope.")
    if policy_domain != normalized_domain:
        raise api_error(400, "ACCESS_POLICY_SCOPE_MISMATCH", "Access policy domain does not match record scope.")
    return policy.id


def validate_operational_record_scope(
    db: Session,
    *,
    project_id: str | None,
    profile_id: str | None,
    environment_id: str | None,
) -> None:
    if project_id is None and (profile_id is not None or environment_id is not None):
        raise api_error(
            400,
            "OPERATIONAL_SCOPE_PROJECT_REQUIRED",
            "Project is required when profile or environment is provided.",
        )
    if project_id is not None and db.get(Project, project_id) is None:
        raise api_error(400, "OPERATIONAL_SCOPE_PROJECT_NOT_FOUND", "Project not found.")
    profile = db.get(Profile, profile_id) if profile_id is not None else None
    if profile_id is not None and profile is None:
        raise api_error(400, "OPERATIONAL_SCOPE_PROFILE_NOT_FOUND", "Profile not found.")
    if profile is not None and profile.project_id != project_id:
        raise api_error(
            400,
            "OPERATIONAL_SCOPE_PROFILE_PROJECT_MISMATCH",
            "Profile does not belong to the project.",
        )
    environment = db.get(Environment, environment_id) if environment_id is not None else None
    if environment_id is not None and environment is None:
        raise api_error(400, "OPERATIONAL_SCOPE_ENVIRONMENT_NOT_FOUND", "Environment not found.")
    if environment is not None and environment.project_id != project_id:
        raise api_error(
            400,
            "OPERATIONAL_SCOPE_ENVIRONMENT_PROJECT_MISMATCH",
            "Environment does not belong to the project.",
        )


def job_visible_in_active_context(job: Job, active_context: ActiveContext | None) -> bool:
    if not active_context or not active_context.project_id or not active_context.environment_id:
        return False
    if job.project_id != active_context.project_id:
        return False
    if job.environment_id != active_context.environment_id:
        return False
    if active_context.can_view_all_domains:
        return True
    allowed_domains = allowed_domains_for_context(active_context.domain_name, False)
    return job.domain_name in allowed_domains


def apply_job_visibility(query, db: Session, user: User):
    if user.is_admin:
        return query
    active_context = active_context_for_user(db, user)
    if not active_context or not active_context.project_id or not active_context.environment_id:
        return query.filter(Job.id == "__none__")
    query = query.filter(Job.project_id == active_context.project_id, Job.environment_id == active_context.environment_id)
    if not active_context.can_view_all_domains:
        query = query.filter(Job.domain_name.in_(allowed_domains_for_context(active_context.domain_name, False)))
    return query


def require_job_visible(job: Job, db: Session, user: User) -> None:
    if user.is_admin:
        return
    if not job_visible_in_active_context(job, active_context_for_user(db, user)):
        raise api_error(403, "JOB_FORBIDDEN", "Job is not visible in the active context.")


def require_job_creation_visible(payload, db: Session, user: User) -> None:
    if user.is_admin:
        return
    active_context = active_context_for_user(db, user)
    domain_name = normalize_domain_name(payload.domain_name) if payload.domain_name else None
    draft_job = Job(
        job_type=payload.job_type,
        source_module=payload.source_module,
        project_id=payload.project_id,
        profile_id=payload.profile_id,
        environment_id=payload.environment_id,
        domain_name=domain_name,
        input_json="{}",
        result_json="{}",
        error_details_json="{}",
        created_by=user.email,
    )
    if not job_visible_in_active_context(draft_job, active_context):
        raise api_error(403, "JOB_FORBIDDEN", "Job is not visible in the active context.")


def settings_scope_authority_payload(db: Session, user: User) -> dict[str, object]:
    active_context = active_context_for_user(db, user)
    setup_counts = settings_setup_counts(db, user, active_context)
    setup_visibility = settings_setup_visibility(db, user, active_context)
    workspace_count = setup_counts["workspaces"]
    project_count = setup_counts["projects"]
    profile_count = setup_counts["profiles"]
    environment_count = setup_counts["environments"]
    blocked_reasons: list[str] = []
    if project_count == 0:
        blocked_reasons.append("PROJECT")
    if profile_count == 0:
        blocked_reasons.append("PROFILE")
    if environment_count == 0:
        blocked_reasons.append("ENVIRONMENT")
    if not active_context or not active_context.project_id or not active_context.environment_id:
        blocked_reasons.append("ACTIVE_CONTEXT")
    if active_context and active_context.project_id and not active_context.domain_name:
        blocked_reasons.append("DOMAIN")
    can_set_active_context = project_count > 0 and environment_count > 0
    can_manage_users = bool(setup_visibility["can_manage_users"])
    can_manage_workspaces = bool(setup_visibility["can_manage_workspaces"])
    can_manage_projects = bool(setup_visibility["can_manage_projects"])
    can_manage_profiles = bool(setup_visibility["can_manage_profiles"])
    can_manage_environments = bool(setup_visibility["can_manage_environments"])
    can_manage_roles = bool(setup_visibility["can_manage_roles"])
    can_manage_grants = bool(setup_visibility["can_manage_grants"])
    can_manage_access_policies = bool(setup_visibility["can_manage_access_policies"])
    return {
        "module": "settings",
        "label": "Settings",
        "label_key": "module.settings.label",
        "status": "READY" if not blocked_reasons else "INCOMPLETE",
        "active_context": serialize_active_context(active_context, user),
        "setup_counts": setup_counts,
        "setup_visibility": setup_visibility,
        "blocked_reasons": blocked_reasons,
        "available_actions": [
            available_action(
                key="create_workspace",
                label="Create workspace",
                method="POST",
                href="/api/v1/platform/workspaces",
                icon_key="settings.workspace",
                variant="primary",
                disabled=not can_manage_workspaces,
                disabled_reason=disabled_reason_for_authority(can_manage_workspaces, None, "DBA_REQUIRED"),
            ),
            available_action(
                key="create_project",
                label="Create project",
                method="POST",
                href="/api/v1/platform/projects",
                icon_key="settings.project",
                disabled=not can_manage_projects or workspace_count == 0,
                disabled_reason=disabled_reason_for_authority(
                    can_manage_projects,
                    "WORKSPACE_REQUIRED" if workspace_count == 0 else None,
                    "DBA_REQUIRED",
                ),
            ),
            available_action(
                key="create_profile",
                label="Create profile",
                method="POST",
                href="/api/v1/platform/profiles",
                icon_key="settings.profile",
                disabled=not can_manage_profiles or project_count == 0,
                disabled_reason=disabled_reason_for_authority(
                    can_manage_profiles,
                    "PROJECT_REQUIRED" if project_count == 0 else None,
                    "PROJECT_ADMIN_REQUIRED",
                ),
            ),
            available_action(
                key="create_environment",
                label="Create environment",
                method="POST",
                href="/api/v1/platform/environments",
                icon_key="settings.environment",
                disabled=not can_manage_environments or project_count == 0,
                disabled_reason=disabled_reason_for_authority(
                    can_manage_environments,
                    "PROJECT_REQUIRED" if project_count == 0 else None,
                    "PROJECT_ADMIN_REQUIRED",
                ),
            ),
            available_action(
                key="set_active_context",
                label="Set active context",
                method="POST",
                href="/api/v1/platform/active-context",
                icon_key="settings.context",
                disabled=not can_set_active_context,
                disabled_reason="PROJECT_AND_ENVIRONMENT_REQUIRED" if not can_set_active_context else None,
            ),
            available_action(
                key="create_user",
                label="Create user",
                method="POST",
                href="/api/v1/platform/users",
                icon_key="settings.user",
                disabled=not can_manage_users,
                disabled_reason=disabled_reason_for_authority(can_manage_users, None, "PROJECT_ADMIN_REQUIRED"),
            ),
            available_action(
                key="create_role",
                label="Create role",
                method="POST",
                href="/api/v1/platform/roles",
                icon_key="settings.role",
                disabled=not can_manage_roles,
                disabled_reason=disabled_reason_for_authority(can_manage_roles, None, "PROJECT_ADMIN_REQUIRED"),
            ),
            available_action(
                key="assign_grant",
                label="Assign grant",
                method="POST",
                href="/api/v1/platform/grants",
                icon_key="settings.grant",
                disabled=not can_manage_grants,
                disabled_reason=disabled_reason_for_authority(can_manage_grants, None, "PROJECT_ADMIN_REQUIRED"),
            ),
            available_action(
                key="create_access_policy",
                label="Create access policy",
                method="POST",
                href="/api/v1/platform/access-policies",
                icon_key="settings.policy",
                disabled=not can_manage_access_policies,
                disabled_reason=disabled_reason_for_authority(
                    can_manage_access_policies,
                    None,
                    "PROJECT_ADMIN_REQUIRED",
                ),
            ),
        ],
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


def filter_cockpit_recent_records(query, model, db: Session, user: User, active_context: ActiveContext | None):
    if user.is_admin and not active_context:
        project_id = active_context.project_id if active_context else None
        return filter_by_active_project(query, model, project_id)
    return apply_operational_scope(query, model, operational_scope_from_context(active_context))


def cockpit_context_selector_payload(active_context_payload: dict[str, object]) -> dict[str, object]:
    mode = "PRIVATE" if active_context_payload["domain_name"] else "PUBLIC"
    return {
        "mode": mode,
        "active_context": active_context_payload,
        "public_view_available": True,
        "requires_private_context": False,
        "set_context_action_key": "set_active_context",
    }


def cockpit_project_info_payload(project_id: str | None) -> dict[str, object]:
    return {
        "title": "Project information",
        "status": "AVAILABLE" if project_id else "NEEDS_CONTEXT",
        "links": [],
        "documents": [],
        "contacts": [],
        "secure_vault": {
            "status": "NOT_CONFIGURED",
            "metadata_only": True,
            "secret_values_available": False,
        },
    }


def cockpit_user_scope_payload(user: User, active_context_payload: dict[str, object]) -> dict[str, object]:
    return {
        "role_mode": "DBA" if user.is_admin else "SCOPED",
        "is_dba": user.is_admin,
        "allowed_domains": active_context_payload["allowed_domains"],
        "can_view_all_domains": active_context_payload["can_view_all_domains"],
    }


def cockpit_route_recovery_payload() -> dict[str, object]:
    return {
        "default_path": "/home",
        "return_action_key": "return_to_cockpit",
        "blocked_route_message": "Return to Project Cockpit and select an available context or accelerator.",
    }


def cockpit_accelerators_payload(items: list[dict[str, object]], has_private_scope: bool) -> list[dict[str, object]]:
    accelerators = []
    for item in items:
        requires_private_context = item["id"] not in {"home", "settings"}
        disabled = requires_private_context and not has_private_scope
        disabled_reason = None
        if requires_private_context and not has_private_scope:
            disabled_reason = "ACTIVE_CONTEXT_REQUIRED"
        accelerators.append(
            {
                "key": item["id"],
                "label": item["label"],
                "description": item["description"],
                "href": item["path"],
                "status": item["status"],
                "icon_key": item["icon_key"],
                "requires_private_context": requires_private_context,
                "disabled": disabled,
                "disabled_reason": disabled_reason,
            }
        )
    return accelerators


def project_cockpit_summary_payload(db: Session, user: User) -> dict[str, object]:
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    if active_context and active_context.project_id and not can_use_active_context(db, user, active_context):
        active_context = None
    active_context_payload = serialize_active_context(active_context, user)
    project_id = active_context.project_id if active_context else None
    setup_status = project_setup_status_payload(db, project_id, user) if project_id else None
    recent_jobs = []
    recent_artifacts = []
    recent_evidence = []
    if project_id:
        recent_jobs = apply_job_visibility(db.query(Job), db, user).order_by(Job.created_at.desc()).limit(5).all()
        recent_artifacts = (
            filter_cockpit_recent_records(db.query(Artifact), Artifact, db, user, active_context)
            .order_by(Artifact.created_at.desc())
            .limit(5)
            .all()
        )
        recent_evidence = (
            filter_cockpit_recent_records(db.query(Evidence).filter(Evidence.client_safe.is_(True)), Evidence, db, user, active_context)
            .order_by(Evidence.created_at.desc())
            .limit(5)
            .all()
        )
    status = "ready" if setup_status and setup_status["status"] == "READY" else "needs_context"
    has_active_scope = bool(active_context and active_context.project_id and active_context.environment_id)
    has_private_scope = bool(has_active_scope and active_context and active_context.domain_name)
    module_summary = module_summary_payload(db, user)
    return {
        "module_id": "home",
        "title": "Project Cockpit",
        "status": status,
        "description": "Project context, project information, and module accelerators for the active OTM workbench scope.",
        "active_context": active_context_payload,
        "setup_status": setup_status,
        "counts": {
            "recent_jobs": len(recent_jobs),
            "recent_artifacts": len(recent_artifacts),
            "recent_evidence": len(recent_evidence),
        },
        "context_selector": cockpit_context_selector_payload(active_context_payload),
        "project_info": cockpit_project_info_payload(project_id),
        "accelerators": cockpit_accelerators_payload(module_summary["items"], has_private_scope),
        "user_scope": cockpit_user_scope_payload(user, active_context_payload),
        "route_recovery": cockpit_route_recovery_payload(),
        "module_summary": module_summary,
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
                disabled=not has_active_scope,
                disabled_reason="ACTIVE_CONTEXT_REQUIRED" if not has_active_scope else None,
            ),
            available_action(
                key="view_evidence",
                label="View evidence",
                method="GET",
                href="/api/v1/evidence-hub/evidence",
                icon_key="evidence",
                disabled=not has_active_scope,
                disabled_reason="ACTIVE_CONTEXT_REQUIRED" if not has_active_scope else None,
            ),
            available_action(
                key="return_to_cockpit",
                label="Return to Cockpit",
                method="GET",
                href="/home",
                icon_key="home",
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
    domain_name = normalize_domain_name(active_context.domain_name) if active_context and active_context.domain_name else None
    rows = (
        db.query(Role, Capability)
        .join(UserProjectRole, UserProjectRole.role_id == Role.id)
        .join(RoleCapability, RoleCapability.role_id == Role.id)
        .join(Capability, Capability.id == RoleCapability.capability_id)
        .filter(
            UserProjectRole.user_id == user.id,
            UserProjectRole.project_id == project_id,
            or_(UserProjectRole.environment_id.is_(None), UserProjectRole.environment_id == active_context.environment_id),
            or_(UserProjectRole.domain_name.is_(None), UserProjectRole.domain_name == domain_name),
        )
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
    project_id: str | None = None
    profile_id: str | None = None
    environment_id: str | None = None
    domain_name: str | None = None
    visibility: str = "PRIVATE"
    access_policy_id: str | None = None


class ManifestCreate(BaseModel):
    source_module: str
    manifest_json: str
    status: str = "CREATED"
    project_id: str | None = None
    profile_id: str | None = None
    environment_id: str | None = None
    domain_name: str | None = None
    visibility: str = "PRIVATE"
    access_policy_id: str | None = None


class EvidenceCreate(BaseModel):
    source_module: str
    evidence_type: str
    summary_json: str
    artifact_id: str | None = None
    manifest_id: str | None = None
    project_id: str | None = None
    profile_id: str | None = None
    environment_id: str | None = None
    domain_name: str | None = None
    visibility: str | None = None
    access_policy_id: str | None = None


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
    query = db.query(Workspace)
    if not user.is_admin:
        project_ids = granted_project_ids(db, user)
        if not project_ids:
            return []
        workspace_ids = {
            workspace_id
            for (workspace_id,) in db.query(Project.workspace_id).filter(Project.id.in_(project_ids)).distinct().all()
        }
        query = query.filter(Workspace.id.in_(workspace_ids))
    return [IdNameResponse(id=item.id, name=item.name) for item in query.order_by(Workspace.name).all()]


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
    if not user.is_admin:
        project_ids = granted_project_ids(db, user)
        if not project_ids:
            return PageResponse(items=[], total=0)
        query = query.filter(Project.id.in_(project_ids))
    projects = query.order_by(Project.name).all()
    items = [IdNameResponse(id=item.id, name=item.name) for item in projects]
    return PageResponse(items=items, total=len(items))


@router.get("/projects/{project_id}/setup-status")
def get_project_setup_status(
    project_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    if db.get(Project, project_id) is None:
        raise api_error(404, "PROJECT_NOT_FOUND", "Project not found.")
    if not can_read_project_setup(db, user, project_id):
        raise api_error(403, "PROJECT_SETUP_STATUS_FORBIDDEN", "Project is not visible to this user.")
    return project_setup_status_payload(db, project_id, user)


@router.get("/settings/scope-authority")
def get_settings_scope_authority(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    return settings_scope_authority_payload(db, user)


@router.get("/settings/access-model")
def get_settings_access_model(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    active_context = active_context_for_user(db, user)
    visibility = settings_setup_visibility(db, user, active_context)
    can_manage_users = bool(visibility["can_manage_users"])
    can_manage_roles = bool(visibility["can_manage_roles"])
    can_manage_grants = bool(visibility["can_manage_grants"])
    can_manage_access_policies = bool(visibility["can_manage_access_policies"])
    grants_query = db.query(UserProjectRole)
    if not user.is_admin:
        if not active_context or not active_context.project_id:
            grants_query = grants_query.filter(UserProjectRole.project_id == "__none__")
        else:
            grants_query = grants_query.filter(UserProjectRole.project_id == active_context.project_id)
        if not can_manage_grants:
            grants_query = grants_query.filter(UserProjectRole.user_id == user.id)
    grants = grants_query.order_by(UserProjectRole.project_id, UserProjectRole.user_id).all()
    if user.is_admin or can_manage_roles or can_manage_grants:
        roles = db.query(Role).order_by(Role.name).all()
    else:
        role_ids = {grant.role_id for grant in grants}
        roles_query = db.query(Role)
        if role_ids:
            roles_query = roles_query.filter(Role.id.in_(role_ids))
        else:
            roles_query = roles_query.filter(Role.id == "__none__")
        roles = roles_query.order_by(Role.name).all()
    policies_query = db.query(AccessPolicy)
    if not user.is_admin:
        if not active_context or not active_context.project_id:
            policies_query = policies_query.filter(AccessPolicy.project_id == "__none__")
        else:
            policies_query = policies_query.filter(AccessPolicy.project_id == active_context.project_id)
        if not can_manage_access_policies:
            policies_query = policies_query.filter(AccessPolicy.id == "__none__")
    policies = policies_query.order_by(AccessPolicy.name).all()
    if user.is_admin or can_manage_users or can_manage_grants:
        users = db.query(User).order_by(User.email).all()
    else:
        users = [user]
    capability_names = (
        [name for (name,) in db.query(Capability.name).order_by(Capability.name).all()]
        if user.is_admin or can_manage_roles
        else []
    )
    return {
        "setup_visibility": visibility,
        "active_project_id": active_context.project_id if active_context else None,
        "users": [serialize_settings_user(item) for item in users],
        "roles": [serialize_role(db, role) for role in roles],
        "capability_names": capability_names,
        "grants": [serialize_grant(db, grant, active_context) for grant in grants],
        "access_policies": [serialize_access_policy(db, policy, active_context) for policy in policies],
    }


@router.post("/roles")
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    require_settings_setup_authority(db, user, "can_manage_roles", "SETTINGS_ROLE_AUTHORITY_REQUIRED")
    name = payload.name.strip()
    if not name:
        raise api_error(400, "ROLE_NAME_REQUIRED", "Role name is required.")
    existing = db.query(Role).filter(Role.name == name).first()
    if existing:
        raise api_error(409, "ROLE_ALREADY_EXISTS", "Role already exists.")
    role = Role(name=name)
    db.add(role)
    db.flush()
    for capability_name in sorted({item.strip() for item in payload.capability_names if item.strip()}):
        capability = db.query(Capability).filter(Capability.name == capability_name).first()
        if capability is None:
            capability = Capability(name=capability_name)
            db.add(capability)
            db.flush()
        db.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    db.commit()
    db.refresh(role)
    write_audit(db, user, "role.create", "role", role.id)
    return serialize_role(db, role)


@router.post("/users")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    require_settings_setup_authority(db, user, "can_manage_users", "SETTINGS_USER_AUTHORITY_REQUIRED")
    email = payload.email.strip().lower()
    if not email:
        raise api_error(400, "USER_EMAIL_REQUIRED", "User email is required.")
    if not payload.password:
        raise api_error(400, "USER_PASSWORD_REQUIRED", "User password is required.")
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise api_error(409, "USER_ALREADY_EXISTS", "User already exists.")
    created = User(email=email, password_hash=hash_password(payload.password), is_active=payload.is_active, is_admin=False)
    db.add(created)
    db.commit()
    db.refresh(created)
    write_audit(db, user, "user.create", "user", created.id)
    return serialize_settings_user(created)


@router.post("/grants")
def create_grant(
    payload: GrantCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    require_settings_setup_authority(
        db,
        user,
        "can_manage_grants",
        "SETTINGS_GRANT_AUTHORITY_REQUIRED",
        project_id=payload.project_id,
    )
    if db.get(Project, payload.project_id) is None:
        raise api_error(400, "GRANT_INVALID_PROJECT", "Project not found.")
    if payload.environment_id:
        environment = db.get(Environment, payload.environment_id)
        if environment is None or environment.project_id != payload.project_id:
            raise api_error(400, "GRANT_INVALID_ENVIRONMENT", "Environment not found for project.")
    if db.get(User, payload.user_id) is None:
        raise api_error(400, "GRANT_INVALID_USER", "User not found.")
    if db.get(Role, payload.role_id) is None:
        raise api_error(400, "GRANT_INVALID_ROLE", "Role not found.")
    domain_name = normalize_domain_name(payload.domain_name) if payload.domain_name else None
    existing = (
        db.query(UserProjectRole)
        .filter(
            UserProjectRole.project_id == payload.project_id,
            UserProjectRole.environment_id == payload.environment_id,
            UserProjectRole.domain_name == domain_name,
            UserProjectRole.user_id == payload.user_id,
            UserProjectRole.role_id == payload.role_id,
        )
        .first()
    )
    if existing:
        return serialize_grant(db, existing)
    grant = UserProjectRole(
        project_id=payload.project_id,
        environment_id=payload.environment_id,
        domain_name=domain_name,
        user_id=payload.user_id,
        role_id=payload.role_id,
    )
    db.add(grant)
    db.commit()
    db.refresh(grant)
    write_audit(db, user, "grant.create", "user_project_role", grant.id)
    return serialize_grant(db, grant)


@router.post("/access-policies")
def create_access_policy(
    payload: AccessPolicyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    require_settings_setup_authority(
        db,
        user,
        "can_manage_access_policies",
        "SETTINGS_ACCESS_POLICY_AUTHORITY_REQUIRED",
        project_id=payload.project_id,
    )
    name = payload.name.strip()
    if not name:
        raise api_error(400, "ACCESS_POLICY_NAME_REQUIRED", "Access policy name is required.")
    visibility = normalize_visibility(payload.visibility)
    domain_name = normalize_domain_for_visibility(payload.domain_name, visibility)
    if payload.project_id and db.get(Project, payload.project_id) is None:
        raise api_error(400, "ACCESS_POLICY_INVALID_PROJECT", "Project not found.")
    existing = (
        db.query(AccessPolicy)
        .filter(AccessPolicy.project_id == payload.project_id, AccessPolicy.name == name)
        .first()
    )
    if existing:
        raise api_error(409, "ACCESS_POLICY_ALREADY_EXISTS", "Access policy already exists.")
    policy = AccessPolicy(
        project_id=payload.project_id,
        name=name,
        visibility=visibility,
        domain_name=domain_name,
        rule_json=payload.rule_json or "{}",
        created_by=user.id,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    write_audit(db, user, "access_policy.create", "access_policy", policy.id)
    return serialize_access_policy(db, policy)


@router.post("/profiles", response_model=IdNameResponse)
def create_profile(
    payload: ProfileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
) -> IdNameResponse:
    require_settings_setup_authority(
        db,
        user,
        "can_manage_profiles",
        "SETTINGS_PROJECT_AUTHORITY_REQUIRED",
        project_id=payload.project_id,
    )
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
        if not can_read_project_setup(db, user, project_id):
            return PageResponse(items=[], total=0)
        query = query.filter(Profile.project_id == project_id)
    elif not user.is_admin:
        project_ids = granted_project_ids(db, user)
        if not project_ids:
            return PageResponse(items=[], total=0)
        query = query.filter(Profile.project_id.in_(project_ids))
    profiles = query.order_by(Profile.name).all()
    items = [IdNameResponse(id=item.id, name=item.name) for item in profiles]
    return PageResponse(items=items, total=len(items))


@router.post("/environments", response_model=IdNameResponse)
def create_environment(
    payload: EnvironmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
) -> IdNameResponse:
    require_settings_setup_authority(
        db,
        user,
        "can_manage_environments",
        "SETTINGS_PROJECT_AUTHORITY_REQUIRED",
        project_id=payload.project_id,
    )
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
        if not can_read_project_setup(db, user, project_id):
            return PageResponse(items=[], total=0)
        query = query.filter(Environment.project_id == project_id)
    elif not user.is_admin:
        project_ids = granted_project_ids(db, user)
        if not project_ids:
            return PageResponse(items=[], total=0)
        query = query.filter(Environment.project_id.in_(project_ids))
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
    project = db.get(Project, payload.project_id) if payload.project_id else None
    if payload.project_id and project is None:
        raise api_error(400, "ACTIVE_CONTEXT_INVALID_PROJECT", "Project not found.")
    if payload.project_id and not can_read_project_setup(db, user, payload.project_id):
        raise api_error(403, "ACTIVE_CONTEXT_PROJECT_FORBIDDEN", "Project is not visible to this user.")
    profile = db.get(Profile, payload.profile_id) if payload.profile_id else None
    if payload.profile_id and profile is None:
        raise api_error(400, "ACTIVE_CONTEXT_INVALID_PROFILE", "Profile not found.")
    if profile and payload.project_id and profile.project_id != payload.project_id:
        raise api_error(400, "ACTIVE_CONTEXT_PROFILE_PROJECT_MISMATCH", "Profile does not belong to the project.")
    environment = db.get(Environment, payload.environment_id) if payload.environment_id else None
    if payload.environment_id and environment is None:
        raise api_error(400, "ACTIVE_CONTEXT_INVALID_ENVIRONMENT", "Environment not found.")
    if environment and payload.project_id and environment.project_id != payload.project_id:
        raise api_error(
            400,
            "ACTIVE_CONTEXT_ENVIRONMENT_PROJECT_MISMATCH",
            "Environment does not belong to the project.",
        )

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
        validate_operational_record_scope(
            db,
            project_id=payload.project_id,
            profile_id=payload.profile_id,
            environment_id=payload.environment_id,
        )
        require_job_creation_visible(payload, db, user)
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
    query = apply_job_visibility(query, db, user)
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
    require_job_visible(job, db, user)
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
    require_job_visible(job, db, user)
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
    require_job_visible(job, db, user)
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
    require_job_visible(job, db, user)
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
    visibility = normalize_visibility(payload.visibility)
    domain_name = normalize_domain_for_visibility(payload.domain_name, visibility)
    validate_operational_record_scope(
        db,
        project_id=payload.project_id,
        profile_id=payload.profile_id,
        environment_id=payload.environment_id,
    )
    access_policy_id = validate_access_policy_binding(
        db,
        payload.access_policy_id,
        project_id=payload.project_id,
        domain_name=domain_name,
        visibility=visibility,
    )
    artifact = Artifact(
        project_id=payload.project_id,
        profile_id=payload.profile_id,
        environment_id=payload.environment_id,
        domain_name=domain_name,
        visibility=visibility,
        access_policy_id=access_policy_id,
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
    return {
        "id": artifact.id,
        "project_id": artifact.project_id,
        "profile_id": artifact.profile_id,
        "environment_id": artifact.environment_id,
        "domain_name": artifact.domain_name,
        "visibility": artifact.visibility,
        "access_policy_id": artifact.access_policy_id,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
    }


@router.post("/manifests")
def create_manifest(
    payload: ManifestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    visibility = normalize_visibility(payload.visibility)
    domain_name = normalize_domain_for_visibility(payload.domain_name, visibility)
    validate_operational_record_scope(
        db,
        project_id=payload.project_id,
        profile_id=payload.profile_id,
        environment_id=payload.environment_id,
    )
    access_policy_id = validate_access_policy_binding(
        db,
        payload.access_policy_id,
        project_id=payload.project_id,
        domain_name=domain_name,
        visibility=visibility,
    )
    manifest = Manifest(
        project_id=payload.project_id,
        profile_id=payload.profile_id,
        environment_id=payload.environment_id,
        domain_name=domain_name,
        visibility=visibility,
        access_policy_id=access_policy_id,
        source_module=payload.source_module,
        manifest_json=payload.manifest_json,
        status=payload.status,
    )
    db.add(manifest)
    db.commit()
    db.refresh(manifest)
    return {
        "id": manifest.id,
        "project_id": manifest.project_id,
        "profile_id": manifest.profile_id,
        "environment_id": manifest.environment_id,
        "domain_name": manifest.domain_name,
        "visibility": manifest.visibility,
        "access_policy_id": manifest.access_policy_id,
        "status": manifest.status,
    }


@router.post("/evidence")
def create_evidence(
    payload: EvidenceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    artifact = db.query(Artifact).filter(Artifact.id == payload.artifact_id).first() if payload.artifact_id else None
    manifest = db.query(Manifest).filter(Manifest.id == payload.manifest_id).first() if payload.manifest_id else None
    scope_source = artifact or manifest
    effective_visibility = normalize_visibility(payload.visibility or (scope_source.visibility if scope_source else "PRIVATE"))
    effective_domain_name = payload.domain_name if payload.domain_name is not None else (scope_source.domain_name if scope_source else None)
    effective_project_id = payload.project_id if payload.project_id is not None else (scope_source.project_id if scope_source else None)
    effective_profile_id = payload.profile_id if payload.profile_id is not None else (scope_source.profile_id if scope_source else None)
    effective_environment_id = (
        payload.environment_id if payload.environment_id is not None else (scope_source.environment_id if scope_source else None)
    )
    effective_domain_name = normalize_domain_for_visibility(effective_domain_name, effective_visibility)
    validate_operational_record_scope(
        db,
        project_id=effective_project_id,
        profile_id=effective_profile_id,
        environment_id=effective_environment_id,
    )
    effective_access_policy_id = validate_access_policy_binding(
        db,
        payload.access_policy_id if payload.access_policy_id is not None else (scope_source.access_policy_id if scope_source else None),
        project_id=effective_project_id,
        domain_name=effective_domain_name,
        visibility=effective_visibility,
    )
    evidence = Evidence(
        project_id=effective_project_id,
        profile_id=effective_profile_id,
        environment_id=effective_environment_id,
        domain_name=effective_domain_name,
        visibility=effective_visibility,
        access_policy_id=effective_access_policy_id,
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
    return {
        "id": evidence.id,
        "project_id": evidence.project_id,
        "profile_id": evidence.profile_id,
        "environment_id": evidence.environment_id,
        "domain_name": evidence.domain_name,
        "visibility": evidence.visibility,
        "access_policy_id": evidence.access_policy_id,
        "client_safe": evidence.client_safe,
        "status": evidence.status,
    }


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
