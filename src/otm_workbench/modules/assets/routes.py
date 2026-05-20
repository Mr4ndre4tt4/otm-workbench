from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import Asset, AssetVersion, User
from otm_workbench.modules.assets.assets import (
    create_draft_asset,
    record_asset_download,
    serialize_asset,
    serialize_asset_version,
    upload_asset_version,
)
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


@router.get("/assets/{asset_id}/download")
def download_current_asset_version(
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise api_error(404, "ASSET_NOT_FOUND", "Asset not found.")
    if not asset.current_version_id:
        raise api_error(409, "ASSET_VERSION_MISSING", "Asset has no current version to download.")
    version = db.query(AssetVersion).filter(AssetVersion.id == asset.current_version_id).first()
    if version is None:
        raise api_error(409, "ASSET_VERSION_MISSING", "Asset current version was not found.")
    storage_path = Path(version.storage_path)
    if not storage_path.exists():
        raise api_error(409, "ASSET_FILE_MISSING", "Asset current version file was not found.")
    record_asset_download(db, asset=asset, version=version, downloaded_by=user.email)
    return FileResponse(
        path=storage_path,
        media_type=version.content_type,
        filename=version.file_name,
    )


@router.post("/assets/{asset_id}/versions")
def upload_asset_file_version(
    asset_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise api_error(404, "ASSET_NOT_FOUND", "Asset not found.")
    content = file.file.read()
    version = upload_asset_version(
        db,
        asset=asset,
        artifact_root=Path(get_settings().artifact_root),
        file_name=file.filename or "asset.bin",
        content_type=file.content_type or "application/octet-stream",
        content=content,
        uploaded_by=user.email,
    )
    return serialize_asset_version(version)


@router.get("/assets/{asset_id}/versions")
def list_asset_versions(
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise api_error(404, "ASSET_NOT_FOUND", "Asset not found.")
    versions = (
        db.query(AssetVersion)
        .filter(AssetVersion.asset_id == asset_id)
        .order_by(AssetVersion.version_number.desc())
        .all()
    )
    items = [serialize_asset_version(version) for version in versions]
    return PageResponse(items=items, total=len(items))
