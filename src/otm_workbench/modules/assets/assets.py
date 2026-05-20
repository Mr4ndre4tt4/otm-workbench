import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import Asset, AssetClassification, AssetLink, AssetVersion, AuditLog, DomainEvent, User
from otm_workbench.modules.assets.classifications import seed_asset_classifications
from otm_workbench.modules.assets.secret_risk import (
    assert_global_asset_without_secret_risk,
    assert_global_content_without_secret_risk,
)
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


def serialize_asset_link(link: AssetLink) -> dict[str, object]:
    return {
        "id": link.id,
        "asset_id": link.asset_id,
        "link_type": link.link_type,
        "target_id": link.target_id,
        "target_label": link.target_label,
        "created_by": link.created_by,
        "created_at": link.created_at.isoformat() if link.created_at else None,
        "updated_at": link.updated_at.isoformat() if link.updated_at else None,
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


def ensure_link_type(db: Session, link_type: str) -> None:
    ensure_classification(db, "asset_link_type", link_type)


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
    assert_global_asset_without_secret_risk(normalized["scope_type"], payload)

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


def normalize_tags(raw_tags: object) -> list[str]:
    if not raw_tags:
        return []
    if not isinstance(raw_tags, list):
        raise ValueError("Asset tags must be a list.")
    return [str(tag).strip().upper() for tag in raw_tags if str(tag).strip()]


def record_asset_change(
    db: Session,
    *,
    asset: Asset,
    action: str,
    event_type: str,
    actor: str,
    extra: dict[str, object] | None = None,
) -> None:
    payload = {
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
        **(extra or {}),
    }
    db.add(
        AuditLog(
            actor_user_id=actor,
            action=action,
            target_type="asset",
            target_id=asset.id,
            metadata_json=json.dumps(payload, sort_keys=True),
        )
    )
    db.add(
        DomainEvent(
            event_type=event_type,
            source_module="assets",
            project_id=asset.project_id,
            aggregate_type="asset",
            aggregate_id=asset.id,
            payload_json=json.dumps(payload, sort_keys=True),
            status="PENDING",
        )
    )


def update_asset_metadata(
    db: Session,
    *,
    asset: Asset,
    payload: dict[str, object],
    updated_by: str,
) -> Asset:
    allowed_fields = {
        "name",
        "description",
        "category",
        "visibility",
        "scope_type",
        "sensitivity",
        "module_id",
        "macro_object_code",
        "otm_table_name",
        "tags",
    }
    candidate_payload = {
        "name": asset.name,
        "description": asset.description,
        "scope_type": asset.scope_type,
        "module_id": asset.module_id,
        "macro_object_code": asset.macro_object_code,
        "otm_table_name": asset.otm_table_name,
        "tags": parse_tags(asset.tags_json),
        **payload,
    }
    assert_global_asset_without_secret_risk(str(candidate_payload.get("scope_type") or ""), candidate_payload)

    changed_fields: list[str] = []
    for field_name, value in payload.items():
        if field_name not in allowed_fields or value is None:
            continue
        if field_name in {"category", "visibility", "scope_type", "sensitivity"}:
            classification_field = "category" if field_name == "category" else field_name
            classification_type = CLASSIFICATION_FIELDS[classification_field]
            normalized_value = str(value).strip().upper()
            ensure_classification(db, classification_type, normalized_value)
            if getattr(asset, field_name) != normalized_value:
                setattr(asset, field_name, normalized_value)
                changed_fields.append(field_name)
        elif field_name == "tags":
            tags = normalize_tags(value)
            tags_json = json.dumps(tags, sort_keys=True)
            if asset.tags_json != tags_json:
                asset.tags_json = tags_json
                changed_fields.append(field_name)
        elif field_name in {"macro_object_code", "otm_table_name"}:
            normalized_value = str(value).strip().upper() or None
            if getattr(asset, field_name) != normalized_value:
                setattr(asset, field_name, normalized_value)
                changed_fields.append(field_name)
        else:
            normalized_value = str(value).strip() or None
            if getattr(asset, field_name) != normalized_value:
                setattr(asset, field_name, normalized_value)
                changed_fields.append(field_name)

    record_asset_change(
        db,
        asset=asset,
        action="assets.asset.update",
        event_type="assets.asset.updated",
        actor=updated_by,
        extra={"changed_fields": sorted(changed_fields)},
    )
    db.commit()
    db.refresh(asset)
    return asset


def archive_asset(db: Session, *, asset: Asset, archived_by: str) -> Asset:
    asset.status = "ARCHIVED"
    record_asset_change(
        db,
        asset=asset,
        action="assets.asset.archive",
        event_type="assets.asset.archived",
        actor=archived_by,
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
    assert_global_content_without_secret_risk(asset.scope_type, content)
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


def record_asset_download(
    db: Session,
    *,
    asset: Asset,
    version: AssetVersion,
    downloaded_by: str,
) -> None:
    audit_payload = {
        "asset_id": asset.id,
        "asset_version_id": version.id,
        "version_number": version.version_number,
        "file_name": version.file_name,
        "content_type": version.content_type,
        "sha256": version.sha256,
        "size_bytes": version.size_bytes,
        "sensitivity": asset.sensitivity,
    }
    db.add(
        AuditLog(
            actor_user_id=downloaded_by,
            action="assets.asset.download",
            target_type="asset",
            target_id=asset.id,
            metadata_json=json.dumps(audit_payload, sort_keys=True),
        )
    )
    db.add(
        DomainEvent(
            event_type="assets.asset.downloaded",
            source_module="assets",
            project_id=asset.project_id,
            aggregate_type="asset",
            aggregate_id=asset.id,
            payload_json=json.dumps(audit_payload, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()


def create_asset_link(
    db: Session,
    *,
    asset: Asset,
    link_type: str,
    target_id: str,
    target_label: str,
    created_by: str,
) -> AssetLink:
    normalized_link_type = link_type.strip().upper()
    normalized_target_id = target_id.strip().upper() if normalized_link_type in {"OTM_TABLE", "MACRO_OBJECT"} else target_id.strip()
    ensure_link_type(db, normalized_link_type)
    link = AssetLink(
        asset_id=asset.id,
        link_type=normalized_link_type,
        target_id=normalized_target_id,
        target_label=target_label.strip(),
        created_by=created_by,
    )
    db.add(link)
    db.flush()
    audit_payload = {
        "asset_id": asset.id,
        "asset_link_id": link.id,
        "link_type": link.link_type,
        "target_id": link.target_id,
        "target_label": link.target_label,
    }
    db.add(
        AuditLog(
            actor_user_id=created_by,
            action="assets.asset_link.create",
            target_type="asset_link",
            target_id=link.id,
            metadata_json=json.dumps(audit_payload, sort_keys=True),
        )
    )
    db.add(
        DomainEvent(
            event_type="assets.asset_link.created",
            source_module="assets",
            project_id=asset.project_id,
            aggregate_type="asset_link",
            aggregate_id=link.id,
            payload_json=json.dumps(audit_payload, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(link)
    return link
