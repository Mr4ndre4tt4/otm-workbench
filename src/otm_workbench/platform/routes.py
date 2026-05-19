from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_admin, require_user
from otm_workbench.models import (
    Artifact,
    AuditLog,
    Environment,
    Evidence,
    FeatureFlag,
    Job,
    JobEvent,
    Manifest,
    Profile,
    Project,
    User,
    Workspace,
)
from otm_workbench.platform.audit import write_audit
from otm_workbench.platform.jobs import (
    cancel_pending_job,
    create_job as create_platform_job,
    parse_json_object,
    serialize_job,
    serialize_job_event,
)
from otm_workbench.platform.navigation import navigation_items, registered_modules
from otm_workbench.platform.services import authenticate, create_session, file_sha256

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


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


class IdNameResponse(BaseModel):
    id: str
    name: str


class ModuleResponse(BaseModel):
    id: str
    display_name: str
    route_base: str
    status: str


class NavigationItem(BaseModel):
    id: str
    label: str
    path: str
    status: str


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
    user: User = Depends(require_user),
):
    digest, size = file_sha256(payload.file_path)
    artifact = Artifact(
        source_module=payload.source_module,
        artifact_type=payload.artifact_type,
        file_path=payload.file_path,
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
    user: User = Depends(require_user),
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
    user: User = Depends(require_user),
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
