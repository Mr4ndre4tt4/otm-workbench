import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import Asset, AssetClassification, AssetVersion, AuditLog, DomainEvent, User
from otm_workbench.modules.assets.classifications import seed_asset_classifications
from otm_workbench.modules.rates.exports import file_sha256, utc_timestamp


CLASSIFICATION_FIELDS = {
    "asset_type": "asset_type",
    "category": "asset_category",
    "visibility": "asset_visibility",
    "scope_type": "asset_scope",
    "sensitivity": "asset_sensitivity",
}


def parse_tags(tags_json: str) -> list[str]:
    try:
        value = json.loads(tags_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def serialize_asset(asset: Asset) -> dict[str, object]:
    return {
        "id": asset.id,
        "project_id": asset.project_id,
        "profile_id": asset.profile_id,
        "environment_id": asset.environment_id,
        "name": asset.name,
        "description": asset.description,
        "asset_type": asset.asset_type,
        "category": asset.category,
        "visibility": asset.visibility,
        "scope_type": asset.scope_type,
        "sensitivity": asset.sensitivity,
        "status": asset.status,
        "module_id": asset.module_id,
        "macro_object_code": asset.macro_object_code,
        "otm_table_name": asset.otm_table_name,
        "tags": parse_tags(asset.tags_json),
        "current_version_id": asset.current_version_id,
        "created_by": asset.created_by,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
    }


def serialize_asset_version(version: AssetVersion) -> dict[str, object]:
    return {
        "id": version.id,
        "asset_id": version.asset_id,
        "version_number": version.version_number,
        "status": version.status,
        "file_name": version.file_name,
        "content_type": version.content_type,
        "storage_path": version.storage_path,
        "sha256": version.sha256,
        "size_bytes": version.size_bytes,
        "uploaded_by": version.uploaded_by,
        "created_at": version.created_at.isoformat() if version.created_at else None,
        "updated_at": version.updated_at.isoformat() if version.updated_at else None,
    }


def ensure_classification(db: Session, classification_type: str, code: str) -> None:
    seed_asset_classifications(db)
    classification = (
        db.query(AssetClassification)
        .filter(AssetClassification.classification_type == classification_type)
        .filter(AssetClassification.code == code)
        .filter(AssetClassification.is_active.is_(True))
        .first()
    )
    if classification is None:
        raise ValueError(f"Unknown asset classification: {classification_type}/{code}.")


def create_draft_asset(
    db: Session,
    *,
    payload: dict[str, object],
    user: User,
) -> Asset:
    normalized = {
        "asset_type": str(payload["asset_type"]).strip().upper(),
        "category": str(payload["category"]).strip().upper(),
        "visibility": str(payload["visibility"]).strip().upper(),
        "scope_type": str(payload["scope_type"]).strip().upper(),
        "sensitivity": str(payload["sensitivity"]).strip().upper(),
    }
    for field_name, classification_type in CLASSIFICATION_FIELDS.items():
        ensure_classification(db, classification_type, normalized[field_name])

    raw_tags = payload.get("tags") or []
    tags = [str(tag).strip().upper() for tag in raw_tags if str(tag).strip()]
    asset = Asset(
        name=str(payload["name"]).strip(),
        description=str(payload.get("description") or "").strip(),
        asset_type=normalized["asset_type"],
        category=normalized["category"],
        visibility=normalized["visibility"],
        scope_type=normalized["scope_type"],
        sensitivity=normalized["sensitivity"],
        status="DRAFT",
        module_id=str(payload.get("module_id") or "").strip() or None,
        macro_object_code=str(payload.get("macro_object_code") or "").strip().upper() or None,
        otm_table_name=str(payload.get("otm_table_name") or "").strip().upper() or None,
        tags_json=json.dumps(tags, sort_keys=True),
        created_by=user.email,
    )
    db.add(asset)
    db.flush()

    audit_payload = {
        "asset_id": asset.id,
        "status": asset.status,
        "asset_type": asset.asset_type,
        "category": asset.category,
        "visibility": asset.visibility,
        "scope_type": asset.scope_type,
        "sensitivity": asset.sensitivity,
        "module_id": asset.module_id,
        "macro_object_code": asset.macro_object_code,
        "otm_table_name": asset.otm_table_name,
    }
    db.add(
        AuditLog(
            actor_user_id=user.email,
            action="assets.asset.create",
            target_type="asset",
            target_id=asset.id,
            metadata_json=json.dumps(audit_payload, sort_keys=True),
        )
    )
    db.add(
        DomainEvent(
            event_type="assets.asset.created",
            source_module="assets",
            project_id=asset.project_id,
            aggregate_type="asset",
            aggregate_id=asset.id,
            payload_json=json.dumps(audit_payload, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(asset)
    return asset


def next_version_number(db: Session, asset_id: str) -> int:
    latest = (
        db.query(AssetVersion)
        .filter(AssetVersion.asset_id == asset_id)
        .order_by(AssetVersion.version_number.desc())
        .first()
    )
    return 1 if latest is None else latest.version_number + 1


def upload_asset_version(
    db: Session,
    *,
    asset: Asset,
    artifact_root: Path,
    file_name: str,
    content_type: str,
    content: bytes,
    uploaded_by: str,
) -> AssetVersion:
    version_number = next_version_number(db, asset.id)
    storage_dir = artifact_root / "assets" / asset.id / "versions" / f"{version_number:04d}_{utc_timestamp()}"
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / file_name
    storage_path.write_bytes(content)
    digest, size = file_sha256(storage_path)

    db.query(AssetVersion).filter(AssetVersion.asset_id == asset.id).update({"status": "SUPERSEDED"})
    version = AssetVersion(
        asset_id=asset.id,
        version_number=version_number,
        status="CURRENT",
        file_name=file_name,
        content_type=content_type,
        storage_path=str(storage_path),
        sha256=digest,
        size_bytes=size,
        uploaded_by=uploaded_by,
    )
    db.add(version)
    db.flush()
    asset.current_version_id = version.id

    audit_payload = {
        "asset_id": asset.id,
        "asset_version_id": version.id,
        "version_number": version.version_number,
        "file_name": version.file_name,
        "content_type": version.content_type,
        "sha256": version.sha256,
        "size_bytes": version.size_bytes,
    }
    db.add(
        AuditLog(
            actor_user_id=uploaded_by,
            action="assets.asset_version.upload",
            target_type="asset_version",
            target_id=version.id,
            metadata_json=json.dumps(audit_payload, sort_keys=True),
        )
    )
    db.add(
        DomainEvent(
            event_type="assets.asset_version.uploaded",
            source_module="assets",
            project_id=asset.project_id,
            aggregate_type="asset_version",
            aggregate_id=version.id,
            payload_json=json.dumps(audit_payload, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(version)
    return version
