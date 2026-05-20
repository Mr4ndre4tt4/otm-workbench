from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import Asset, User
from otm_workbench.modules.assets.assets import create_draft_asset, serialize_asset
from otm_workbench.modules.assets.classifications import grouped_asset_classifications


router = APIRouter(prefix="/api/v1/modules/assets", tags=["assets"])


class AssetCreateRequest(BaseModel):
    name: str
    description: str = ""
    asset_type: str
    category: str
    visibility: str
    scope_type: str
    sensitivity: str
    module_id: str | None = None
    macro_object_code: str | None = None
    otm_table_name: str | None = None
    tags: list[str] = []


@router.get("/health")
def assets_health(user: User = Depends(require_user)):
    return {"status": "ok", "module": "assets"}


@router.get("/classifications")
def list_asset_classifications(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    items = grouped_asset_classifications(db)
    return PageResponse(items=items, total=len(items))


@router.post("/assets")
def create_asset(
    payload: AssetCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    try:
        asset = create_draft_asset(db, payload=payload.model_dump(), user=user)
    except ValueError as exc:
        raise api_error(400, "ASSET_CLASSIFICATION_INVALID", str(exc)) from exc
    return serialize_asset(asset)


@router.get("/assets")
def list_assets(
    asset_type: str | None = None,
    category: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(Asset)
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type.strip().upper())
    if category:
        query = query.filter(Asset.category == category.strip().upper())
    if status:
        query = query.filter(Asset.status == status.strip().upper())
    assets = query.order_by(Asset.created_at.desc()).all()
    items = [serialize_asset(asset) for asset in assets]
    return PageResponse(items=items, total=len(items))


@router.get("/assets/{asset_id}")
def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise api_error(404, "ASSET_NOT_FOUND", "Asset not found.")
    return serialize_asset(asset)
