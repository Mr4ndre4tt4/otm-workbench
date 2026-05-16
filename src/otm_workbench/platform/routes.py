from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.dependencies import api_error, get_db, require_admin, require_user
from otm_workbench.models import FeatureFlag, User
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
