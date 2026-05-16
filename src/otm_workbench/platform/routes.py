from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_admin, require_user
from otm_workbench.models import Environment, FeatureFlag, Profile, Project, User, Workspace
from otm_workbench.platform.navigation import navigation_items, registered_modules
from otm_workbench.platform.services import authenticate, create_session

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
