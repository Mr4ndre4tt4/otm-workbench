from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_admin, require_user
from otm_workbench.catalog.services import get_macro_object
from otm_workbench.models import ActiveContext, Artifact, Asset, AssetClassification, AssetLink, AssetVersion, Evidence, User
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
from otm_workbench.modules.assets.classifications import (
    create_asset_classification,
    grouped_asset_classifications,
    serialize_asset_classification,
    update_asset_classification,
)
from otm_workbench.modules.rates.dictionary import load_table_definition
from otm_workbench.platform.scoping import apply_operational_scope, operational_scope_from_context


router = APIRouter(prefix="/api/v1/modules/assets", tags=["assets"])


class AssetCreateRequest(BaseModel):
    name: str
    description: str = ""
    asset_type: str
    category: str
    visibility: str
    scope_type: str
    sensitivity: str
    project_id: str | None = None
    profile_id: str | None = None
    environment_id: str | None = None
    domain_name: str | None = None
    access_policy_id: str | None = None
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


class AssetClassificationCreateRequest(BaseModel):
    classification_type: str
    code: str
    name: str
    description: str = ""
    sort_order: int = 0


class AssetClassificationUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


def reject_archived_asset(asset: Asset) -> None:
    if asset.status == "ARCHIVED":
        raise api_error(409, "ASSET_ARCHIVED", "Archived assets cannot be changed.")


def scoped_asset_query(db: Session, user: User):
    query = db.query(Asset)
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    if active_context is None:
        if not user.is_admin:
            return query.filter(Asset.id.is_(None))
        return query
    return apply_operational_scope(query, Asset, operational_scope_from_context(active_context))


def active_context_scope_payload(db: Session, user: User) -> dict[str, object] | None:
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    if active_context is None:
        return None
    return {
        "project_id": active_context.project_id,
        "profile_id": active_context.profile_id,
        "environment_id": active_context.environment_id,
        "domain_name": active_context.domain_name,
    }


def merge_asset_create_scope(db: Session, user: User, payload: dict[str, object]) -> dict[str, object]:
    scope = active_context_scope_payload(db, user)
    if scope is None:
        return payload
    return {
        **payload,
        **{key: payload.get(key) or value for key, value in scope.items()},
    }


def get_scoped_asset_or_404(db: Session, user: User, asset_id: str) -> Asset:
    asset = scoped_asset_query(db, user).filter(Asset.id == asset_id).first()
    if asset is None:
        raise api_error(404, "ASSET_NOT_FOUND", "Asset not found.")
    return asset


def validate_asset_otm_references(db: Session, payload: dict[str, object]) -> None:
    dictionary_root = Path(get_settings().otm_data_dictionary_root)
    macro_object_code = str(payload.get("macro_object_code") or "").strip().upper()
    otm_table_name = str(payload.get("otm_table_name") or "").strip().upper()
    if macro_object_code and get_macro_object(db, dictionary_root, macro_object_code) is None:
        raise api_error(
            400,
            "ASSET_METADATA_INVALID",
            "Asset macro object was not found in Catalog Core.",
            details={"field_name": "macro_object_code", "reference_type": "catalog_macro_object"},
        )
    if otm_table_name:
        try:
            load_table_definition(dictionary_root, otm_table_name)
        except FileNotFoundError as exc:
            raise api_error(
                400,
                "ASSET_METADATA_INVALID",
                "Asset OTM table was not found in the Data Dictionary.",
                details={"field_name": "otm_table_name", "reference_type": "otm_data_dictionary_table"},
            ) from exc


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


@router.post("/classifications")
def create_classification(
    payload: AssetClassificationCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    try:
        classification = create_asset_classification(db, payload.model_dump())
    except ValueError as exc:
        raise api_error(400, "ASSET_CLASSIFICATION_INVALID", str(exc)) from exc
    return serialize_asset_classification(classification)


@router.patch("/classifications/{classification_id}")
def patch_classification(
    classification_id: str,
    payload: AssetClassificationUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    classification = db.query(AssetClassification).filter(AssetClassification.id == classification_id).first()
    if classification is None:
        raise api_error(404, "ASSET_CLASSIFICATION_NOT_FOUND", "Asset classification not found.")
    try:
        updated = update_asset_classification(
            db,
            classification=classification,
            payload=payload.model_dump(exclude_unset=True),
        )
    except PermissionError as exc:
        raise api_error(409, "ASSET_CLASSIFICATION_PROTECTED", str(exc)) from exc
    return serialize_asset_classification(updated)


@router.post("/assets")
def create_asset(
    payload: AssetCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    request_payload = merge_asset_create_scope(db, user, payload.model_dump())
    validate_asset_otm_references(db, request_payload)
    try:
        asset = create_draft_asset(db, payload=request_payload, user=user)
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
    query = scoped_asset_query(db, user)
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
    asset = get_scoped_asset_or_404(db, user, asset_id)
    return serialize_asset(asset)


@router.patch("/assets/{asset_id}")
def patch_asset(
    asset_id: str,
    payload: AssetUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    asset = get_scoped_asset_or_404(db, user, asset_id)
    reject_archived_asset(asset)
    request_payload = payload.model_dump(exclude_unset=True)
    validate_asset_otm_references(db, request_payload)
    try:
        updated = update_asset_metadata(
            db,
            asset=asset,
            payload=request_payload,
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
    asset = get_scoped_asset_or_404(db, user, asset_id)
    return serialize_asset(archive_asset(db, asset=asset, archived_by=user.email))


@router.post("/assets/{asset_id}/links")
def create_asset_link_endpoint(
    asset_id: str,
    payload: AssetLinkCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    asset = get_scoped_asset_or_404(db, user, asset_id)
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
    asset = get_scoped_asset_or_404(db, user, asset_id)
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
    asset = get_scoped_asset_or_404(db, user, asset_id)
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
    asset = get_scoped_asset_or_404(db, user, asset_id)
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
    asset = get_scoped_asset_or_404(db, user, asset_id)
    versions = (
        db.query(AssetVersion)
        .filter(AssetVersion.asset_id == asset_id)
        .order_by(AssetVersion.version_number.desc())
        .all()
    )
    items = [serialize_asset_version(version) for version in versions]
    return PageResponse(items=items, total=len(items))
