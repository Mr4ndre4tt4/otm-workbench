import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import Asset, AssetClassification, AssetLink, AssetVersion, AuditLog, DomainEvent, User
from otm_workbench.modules.assets.classifications import seed_asset_classifications
from otm_workbench.modules.assets.secret_risk import (
    assert_global_asset_without_secret_risk,
    assert_global_content_without_secret_risk,
)
from otm_workbench.platform.scoping import normalize_domain_name
from otm_workbench.modules.rates.exports import file_sha256, utc_timestamp


CLASSIFICATION_FIELDS = {
    "asset_type": "asset_type",
    "category": "asset_category",
    "visibility": "asset_visibility",
    "scope_type": "asset_scope",
    "sensitivity": "asset_sensitivity",
}


class AssetValidationError(ValueError):
    def __init__(self, message: str, *, details: dict[str, object] | None = None):
        super().__init__(message)
        self.details = details or {}


def parse_tags(tags_json: str) -> list[str]:
    try:
        value = json.loads(tags_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def asset_action(
    *,
    asset_id: str,
    key: str,
    label: str,
    method: str,
    path_suffix: str,
    variant: str,
    icon_key: str,
    requires_confirmation: bool,
    disabled: bool,
    disabled_reason: str | None,
    permission: str,
    result_hint: str,
) -> dict[str, object]:
    return {
        "key": key,
        "label": label,
        "method": method,
        "href": f"/api/v1/modules/assets/assets/{asset_id}{path_suffix}",
        "variant": variant,
        "icon_key": icon_key,
        "requires_confirmation": requires_confirmation,
        "disabled": disabled,
        "disabled_reason": disabled_reason,
        "permission": permission,
        "result_hint": result_hint,
    }


def build_asset_available_actions(asset: Asset) -> list[dict[str, object]]:
    archived = asset.status == "ARCHIVED"
    no_version = not bool(asset.current_version_id)
    return [
        asset_action(
            asset_id=asset.id,
            key="asset.update",
            label="Update metadata",
            method="PATCH",
            path_suffix="",
            variant="secondary",
            icon_key="edit",
            requires_confirmation=False,
            disabled=archived,
            disabled_reason="ASSET_ARCHIVED" if archived else None,
            permission="assets.asset.update",
            result_hint="refresh_object",
        ),
        asset_action(
            asset_id=asset.id,
            key="asset.upload_version",
            label="Upload version",
            method="POST",
            path_suffix="/versions",
            variant="primary",
            icon_key="upload",
            requires_confirmation=False,
            disabled=archived,
            disabled_reason="ASSET_ARCHIVED" if archived else None,
            permission="assets.asset.upload_version",
            result_hint="refresh_object",
        ),
        asset_action(
            asset_id=asset.id,
            key="asset.create_link",
            label="Create link",
            method="POST",
            path_suffix="/links",
            variant="primary",
            icon_key="link",
            requires_confirmation=False,
            disabled=archived,
            disabled_reason="ASSET_ARCHIVED" if archived else None,
            permission="assets.asset.create_link",
            result_hint="refresh_object",
        ),
        asset_action(
            asset_id=asset.id,
            key="asset.download_current",
            label="Download current version",
            method="GET",
            path_suffix="/download",
            variant="secondary",
            icon_key="download",
            requires_confirmation=False,
            disabled=no_version,
            disabled_reason="NO_CURRENT_VERSION" if no_version else None,
            permission="assets.asset.download",
            result_hint="download",
        ),
        asset_action(
            asset_id=asset.id,
            key="asset.archive",
            label="Archive asset",
            method="POST",
            path_suffix="/archive",
            variant="danger",
            icon_key="archive",
            requires_confirmation=True,
            disabled=archived,
            disabled_reason="ASSET_ARCHIVED" if archived else None,
            permission="assets.asset.archive",
            result_hint="refresh_object",
        ),
    ]


def serialize_asset(asset: Asset) -> dict[str, object]:
    return {
        "id": asset.id,
        "project_id": asset.project_id,
        "profile_id": asset.profile_id,
        "environment_id": asset.environment_id,
        "domain_name": asset.domain_name,
        "access_policy_id": asset.access_policy_id,
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
        "target_otm_version": asset.target_otm_version,
        "tags": parse_tags(asset.tags_json),
        "current_version_id": asset.current_version_id,
        "available_actions": build_asset_available_actions(asset),
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


def serialize_asset_version_public(version: AssetVersion) -> dict[str, object]:
    payload = serialize_asset_version(version)
    payload.pop("storage_path", None)
    return payload


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


def asset_versions(db: Session, asset_id: str) -> list[AssetVersion]:
    return (
        db.query(AssetVersion)
        .filter(AssetVersion.asset_id == asset_id)
        .order_by(AssetVersion.version_number.desc())
        .all()
    )


def asset_links(db: Session, asset_id: str) -> list[AssetLink]:
    return (
        db.query(AssetLink)
        .filter(AssetLink.asset_id == asset_id)
        .order_by(AssetLink.created_at.desc())
        .all()
    )


def build_asset_archive_impact(db: Session, asset: Asset) -> dict[str, object]:
    versions = asset_versions(db, asset.id)
    links = asset_links(db, asset.id)
    archive_action = next(
        (action for action in build_asset_available_actions(asset) if action["key"] == "asset.archive"),
        None,
    )
    disabled = bool(archive_action and archive_action["disabled"])
    disabled_reason = str(archive_action["disabled_reason"]) if archive_action and archive_action["disabled_reason"] else None
    linked_target_types = sorted({link.link_type for link in links})
    return {
        "asset_id": asset.id,
        "status": asset.status,
        "eligible": not disabled,
        "disabled_reason": disabled_reason,
        "blocked_reasons": [disabled_reason] if disabled_reason else [],
        "impacted_versions": len(versions),
        "current_version_id": asset.current_version_id,
        "impacted_links": len(links),
        "linked_target_types": linked_target_types,
        "will_disable_actions": [
            "asset.update",
            "asset.upload_version",
            "asset.create_link",
            "asset.archive",
        ],
        "archive_action": archive_action,
    }


def serialize_asset_route_detail(db: Session, asset: Asset) -> dict[str, object]:
    versions = asset_versions(db, asset.id)
    links = asset_links(db, asset.id)
    current_version = next((version for version in versions if version.id == asset.current_version_id), None)
    return {
        "asset": serialize_asset(asset),
        "current_version": serialize_asset_version_public(current_version) if current_version else None,
        "versions": [serialize_asset_version_public(version) for version in versions],
        "links": [serialize_asset_link(link) for link in links],
        "available_actions": build_asset_available_actions(asset),
        "archive_impact": build_asset_archive_impact(db, asset),
    }


def allowed_classification_codes(db: Session, classification_type: str) -> list[str]:
    seed_asset_classifications(db)
    return [
        item.code
        for item in (
            db.query(AssetClassification)
            .filter(AssetClassification.classification_type == classification_type)
            .filter(AssetClassification.is_active.is_(True))
            .order_by(AssetClassification.sort_order.asc(), AssetClassification.code.asc())
            .all()
        )
    ]


def ensure_classification(db: Session, classification_type: str, code: str, field_name: str | None = None) -> None:
    allowed_codes = allowed_classification_codes(db, classification_type)
    classification = (
        db.query(AssetClassification)
        .filter(AssetClassification.classification_type == classification_type)
        .filter(AssetClassification.code == code)
        .filter(AssetClassification.is_active.is_(True))
        .first()
    )
    if classification is None:
        safe_field_name = field_name or classification_type
        raise AssetValidationError(
            f"Invalid asset metadata classification for {safe_field_name}.",
            details={
                "allowed_codes": allowed_codes,
                "classification_type": classification_type,
                "field_name": safe_field_name,
            },
        )


def ensure_link_type(db: Session, link_type: str) -> None:
    ensure_classification(db, "asset_link_type", link_type)


def normalize_target_otm_version(db: Session, value: object) -> str | None:
    normalized_value = str(value or "").strip().upper() or None
    if normalized_value is not None:
        ensure_classification(db, "asset_target_otm_version", normalized_value, "target_otm_version")
    return normalized_value


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
        ensure_classification(db, classification_type, normalized[field_name], field_name)
    target_otm_version = normalize_target_otm_version(db, payload.get("target_otm_version"))
    assert_global_asset_without_secret_risk(normalized["scope_type"], payload)

    raw_tags = payload.get("tags") or []
    tags = [str(tag).strip().upper() for tag in raw_tags if str(tag).strip()]
    asset = Asset(
        project_id=str(payload.get("project_id") or "").strip() or None,
        profile_id=str(payload.get("profile_id") or "").strip() or None,
        environment_id=str(payload.get("environment_id") or "").strip() or None,
        domain_name=normalize_domain_name(str(payload.get("domain_name") or "")) if payload.get("domain_name") else None,
        access_policy_id=str(payload.get("access_policy_id") or "").strip() or None,
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
        target_otm_version=target_otm_version,
        tags_json=json.dumps(tags, sort_keys=True),
        created_by=user.email,
    )
    db.add(asset)
    db.flush()

    audit_payload = {
        "asset_id": asset.id,
        "project_id": asset.project_id,
        "profile_id": asset.profile_id,
        "environment_id": asset.environment_id,
        "domain_name": asset.domain_name,
        "access_policy_id": asset.access_policy_id,
        "status": asset.status,
        "asset_type": asset.asset_type,
        "category": asset.category,
        "visibility": asset.visibility,
        "domain_name": asset.domain_name,
        "access_policy_id": asset.access_policy_id,
        "scope_type": asset.scope_type,
        "sensitivity": asset.sensitivity,
        "module_id": asset.module_id,
        "macro_object_code": asset.macro_object_code,
        "otm_table_name": asset.otm_table_name,
        "target_otm_version": asset.target_otm_version,
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
        "project_id": asset.project_id,
        "profile_id": asset.profile_id,
        "environment_id": asset.environment_id,
        "domain_name": asset.domain_name,
        "access_policy_id": asset.access_policy_id,
        "status": asset.status,
        "asset_type": asset.asset_type,
        "category": asset.category,
        "visibility": asset.visibility,
        "scope_type": asset.scope_type,
        "sensitivity": asset.sensitivity,
        "module_id": asset.module_id,
        "macro_object_code": asset.macro_object_code,
        "otm_table_name": asset.otm_table_name,
        "target_otm_version": asset.target_otm_version,
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
        "target_otm_version",
        "tags",
    }
    candidate_payload = {
        "name": asset.name,
        "description": asset.description,
        "scope_type": asset.scope_type,
        "module_id": asset.module_id,
        "macro_object_code": asset.macro_object_code,
        "otm_table_name": asset.otm_table_name,
        "target_otm_version": asset.target_otm_version,
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
            ensure_classification(db, classification_type, normalized_value, field_name)
            if getattr(asset, field_name) != normalized_value:
                setattr(asset, field_name, normalized_value)
                changed_fields.append(field_name)
        elif field_name == "tags":
            tags = normalize_tags(value)
            tags_json = json.dumps(tags, sort_keys=True)
            if asset.tags_json != tags_json:
                asset.tags_json = tags_json
                changed_fields.append(field_name)
        elif field_name == "target_otm_version":
            normalized_value = normalize_target_otm_version(db, value)
            if asset.target_otm_version != normalized_value:
                asset.target_otm_version = normalized_value
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
