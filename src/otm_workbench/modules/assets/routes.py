from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_admin, require_user
from otm_workbench.catalog.services import get_macro_object
from otm_workbench.models import Artifact, Asset, AssetLink, AssetVersion, Evidence, User
from otm_workbench.modules.assets.assets import (
    AssetValidationError,
    archive_asset,
    create_asset_link,
    create_draft_asset,
    record_asset_download,
    serialize_asset,
    serialize_asset_link,
    serialize_asset_version,
    update_asset_metadata,
    upload_asset_version,
)
from otm_workbench.modules.assets.classifications import grouped_asset_classifications
from otm_workbench.modules.rates.dictionary import load_table_definition


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


class AssetUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    visibility: str | None = None
    scope_type: str | None = None
    sensitivity: str | None = None
    module_id: str | None = None
    macro_object_code: str | None = None
    otm_table_name: str | None = None
    tags: list[str] | None = None


class AssetLinkCreateRequest(BaseModel):
    link_type: str
    target_id: str
    target_label: str = ""


def reject_archived_asset(asset: Asset) -> None:
    if asset.status == "ARCHIVED":
        raise api_error(409, "ASSET_ARCHIVED", "Archived assets cannot be changed.")


def artifact_has_client_safe_evidence(db: Session, artifact_id: str) -> bool:
    return (
        db.query(Evidence)
        .filter(Evidence.artifact_id == artifact_id)
        .filter(Evidence.client_safe.is_(True))
        .first()
        is not None
    )


def client_safe_evidence_exists(db: Session, evidence_id: str) -> bool:
    return (
        db.query(Evidence)
        .filter(Evidence.id == evidence_id)
        .filter(Evidence.client_safe.is_(True))
        .first()
        is not None
    )


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
    user: User = Depends(require_admin),
):
    try:
        asset = create_draft_asset(db, payload=payload.model_dump(), user=user)
    except AssetValidationError as exc:
        raise api_error(400, "ASSET_CLASSIFICATION_INVALID", str(exc), details=exc.details) from exc
    except ValueError as exc:
        if "secret-like" in str(exc):
            raise api_error(400, "ASSET_SECRET_RISK", str(exc)) from exc
        raise api_error(400, "ASSET_CLASSIFICATION_INVALID", str(exc)) from exc
    return serialize_asset(asset)


@router.get("/assets")
def list_assets(
    asset_type: str | None = None,
    category: str | None = None,
    status: str | None = None,
    scope_type: str | None = None,
    tag: str | None = None,
    module_id: str | None = None,
    macro_object_code: str | None = None,
    otm_table_name: str | None = None,
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
    if scope_type:
        query = query.filter(Asset.scope_type == scope_type.strip().upper())
    if tag:
        query = query.filter(Asset.tags_json.contains(f'"{tag.strip().upper()}"'))
    if module_id:
        query = query.filter(Asset.module_id == module_id.strip())
    if macro_object_code:
        query = query.filter(Asset.macro_object_code == macro_object_code.strip().upper())
    if otm_table_name:
        query = query.filter(Asset.otm_table_name == otm_table_name.strip().upper())
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


@router.patch("/assets/{asset_id}")
def patch_asset(
    asset_id: str,
    payload: AssetUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise api_error(404, "ASSET_NOT_FOUND", "Asset not found.")
    reject_archived_asset(asset)
    try:
        updated = update_asset_metadata(
            db,
            asset=asset,
            payload=payload.model_dump(exclude_unset=True),
            updated_by=user.email,
        )
    except AssetValidationError as exc:
        raise api_error(400, "ASSET_METADATA_INVALID", str(exc), details=exc.details) from exc
    except ValueError as exc:
        if "secret-like" in str(exc):
            raise api_error(400, "ASSET_SECRET_RISK", str(exc)) from exc
        raise api_error(400, "ASSET_METADATA_INVALID", str(exc)) from exc
    return serialize_asset(updated)


@router.post("/assets/{asset_id}/archive")
def archive_asset_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise api_error(404, "ASSET_NOT_FOUND", "Asset not found.")
    return serialize_asset(archive_asset(db, asset=asset, archived_by=user.email))


@router.post("/assets/{asset_id}/links")
def create_asset_link_endpoint(
    asset_id: str,
    payload: AssetLinkCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise api_error(404, "ASSET_NOT_FOUND", "Asset not found.")
    reject_archived_asset(asset)
    link_type = payload.link_type.strip().upper()
    target_id = payload.target_id.strip()
    if link_type == "OTM_TABLE":
        try:
            load_table_definition(Path(get_settings().otm_data_dictionary_root), target_id)
        except FileNotFoundError as exc:
            raise api_error(400, "ASSET_LINK_INVALID_TABLE", "OTM table not found in Data Dictionary.") from exc
    if link_type == "MACRO_OBJECT" and get_macro_object(db, Path(get_settings().otm_data_dictionary_root), target_id) is None:
        raise api_error(400, "ASSET_LINK_INVALID_MACRO_OBJECT", "OTM macro object not found in Catalog Core.")
    if link_type == "ARTIFACT":
        artifact = db.query(Artifact).filter(Artifact.id == target_id).first()
        if artifact is None or not artifact_has_client_safe_evidence(db, target_id):
            raise api_error(
                400,
                "ASSET_LINK_INVALID_ARTIFACT",
                "Evidence Hub artifact not found or not backed by client-safe evidence.",
            )
    if link_type == "EVIDENCE" and not client_safe_evidence_exists(db, target_id):
        raise api_error(
            400,
            "ASSET_LINK_INVALID_EVIDENCE",
            "Evidence Hub evidence not found or not client-safe.",
        )
    try:
        link = create_asset_link(
            db,
            asset=asset,
            link_type=payload.link_type,
            target_id=target_id,
            target_label=payload.target_label,
            created_by=user.email,
        )
    except ValueError as exc:
        raise api_error(400, "ASSET_LINK_INVALID", str(exc)) from exc
    return serialize_asset_link(link)


@router.get("/assets/{asset_id}/links")
def list_asset_links(
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise api_error(404, "ASSET_NOT_FOUND", "Asset not found.")
    links = (
        db.query(AssetLink)
        .filter(AssetLink.asset_id == asset_id)
        .order_by(AssetLink.created_at.desc())
        .all()
    )
    items = [serialize_asset_link(link) for link in links]
    return PageResponse(items=items, total=len(items))


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
    user: User = Depends(require_admin),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise api_error(404, "ASSET_NOT_FOUND", "Asset not found.")
    reject_archived_asset(asset)
    content = file.file.read()
    try:
        version = upload_asset_version(
            db,
            asset=asset,
            artifact_root=Path(get_settings().artifact_root),
            file_name=file.filename or "asset.bin",
            content_type=file.content_type or "application/octet-stream",
            content=content,
            uploaded_by=user.email,
        )
    except ValueError as exc:
        if "secret-like" in str(exc):
            raise api_error(400, "ASSET_SECRET_RISK", str(exc)) from exc
        raise
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
