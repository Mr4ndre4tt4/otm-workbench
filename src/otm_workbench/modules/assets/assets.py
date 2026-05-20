import json

from sqlalchemy.orm import Session

from otm_workbench.models import Asset, AssetClassification, AuditLog, DomainEvent, User
from otm_workbench.modules.assets.classifications import seed_asset_classifications


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
        "created_by": asset.created_by,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
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
