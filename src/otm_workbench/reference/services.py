from dataclasses import dataclass
from datetime import UTC, datetime
import json

from sqlalchemy.orm import Session

from otm_workbench.models import (
    ReferenceFieldPolicy,
    ReferenceImportBatch,
    ReferenceObject,
    ReferenceObjectType,
)
from otm_workbench.reference.policies import (
    ERROR,
    FREE_TEXT,
    INFO,
    MUST_EXIST,
    SHOULD_EXIST_ALLOW_NEW,
    SUGGEST_ONLY,
    WARNING,
    ReferenceValidationResult,
)


@dataclass(frozen=True)
class ReferenceContext:
    project_id: str | None
    environment_id: str | None
    profile_id: str | None
    domain_name: str
    can_view_all_domains: bool = False


def allowed_domains(context: ReferenceContext) -> list[str]:
    if context.can_view_all_domains:
        return ["*"]
    return ["PUBLIC", context.domain_name.upper()]


def seed_reference_object_types(db: Session) -> None:
    object_types = [
        ("EXCHANGE_RATE", "Exchange Rate"),
        ("RATE_SERVICE", "Rate Service"),
        ("RATE_DISTANCE", "Rate Distance"),
        ("RATE_VERSION", "Rate Version"),
        ("ACCESSORIAL_CODE", "Accessorial Code"),
        ("EQUIPMENT_GROUP", "Equipment Group"),
        ("EQUIPMENT_GROUP_PROFILE", "Equipment Group Profile"),
        ("TRANSPORT_MODE", "Transport Mode"),
        ("CURRENCY", "Currency"),
        ("RATE_OFFERING", "Rate Offering"),
        ("RATE_GEO", "Rate Geo"),
    ]
    for code, name in object_types:
        exists = db.query(ReferenceObjectType).filter(ReferenceObjectType.code == code).first()
        if not exists:
            db.add(ReferenceObjectType(code=code, name=name))
    db.commit()


def seed_rates_field_policies(db: Session) -> None:
    policies = [
        ("transport_mode_gid", "TRANSPORT_MODE", MUST_EXIST, ERROR, False),
        ("currency_gid", "CURRENCY", MUST_EXIST, ERROR, False),
        ("accessorial_code_gid", "ACCESSORIAL_CODE", MUST_EXIST, ERROR, False),
        ("rate_service_gid", "RATE_SERVICE", SHOULD_EXIST_ALLOW_NEW, WARNING, True),
        ("rate_distance_gid", "RATE_DISTANCE", SHOULD_EXIST_ALLOW_NEW, WARNING, True),
        ("rate_version_gid", "RATE_VERSION", SHOULD_EXIST_ALLOW_NEW, WARNING, True),
        ("equipment_group_gid", "EQUIPMENT_GROUP", SHOULD_EXIST_ALLOW_NEW, WARNING, True),
        (
            "equipment_group_profile_gid",
            "EQUIPMENT_GROUP_PROFILE",
            SHOULD_EXIST_ALLOW_NEW,
            WARNING,
            True,
        ),
        ("rate_offering_gid", "RATE_OFFERING", SUGGEST_ONLY, WARNING, True),
        ("rate_geo_gid", "RATE_GEO", FREE_TEXT, INFO, True),
        ("rate_geo_xid", "RATE_GEO", FREE_TEXT, INFO, True),
    ]
    for field_name, object_type, policy, severity, allow_manual in policies:
        exists = (
            db.query(ReferenceFieldPolicy)
            .filter(
                ReferenceFieldPolicy.module_id == "rates",
                ReferenceFieldPolicy.field_name == field_name,
            )
            .first()
        )
        if not exists:
            db.add(
                ReferenceFieldPolicy(
                    module_id="rates",
                    field_name=field_name,
                    object_type=object_type,
                    policy=policy,
                    severity_when_missing=severity,
                    allow_manual_value=allow_manual,
                )
            )
    db.commit()


def list_reference_options(
    db: Session,
    context: ReferenceContext,
    object_type: str,
) -> list[ReferenceObject]:
    query = (
        db.query(ReferenceObject)
        .filter(ReferenceObject.object_type == object_type.upper())
        .filter(ReferenceObject.is_active.is_(True))
    )
    if not context.can_view_all_domains:
        query = query.filter(ReferenceObject.domain_name.in_(allowed_domains(context)))
    options = query.order_by(ReferenceObject.gid).all()
    if context.can_view_all_domains:
        return sorted(options, key=lambda item: (item.domain_name, item.gid))
    domain_order = {domain: index for index, domain in enumerate(allowed_domains(context))}
    return sorted(options, key=lambda item: (domain_order.get(item.domain_name, 99), item.gid))


def find_reference(
    db: Session,
    context: ReferenceContext,
    object_type: str,
    gid: str,
) -> ReferenceObject | None:
    query = (
        db.query(ReferenceObject)
        .filter(ReferenceObject.object_type == object_type.upper())
        .filter(ReferenceObject.gid == gid)
        .filter(ReferenceObject.is_active.is_(True))
    )
    if not context.can_view_all_domains:
        query = query.filter(ReferenceObject.domain_name.in_(allowed_domains(context)))
    return query.first()


def get_field_policy(db: Session, module_id: str, field_name: str) -> ReferenceFieldPolicy | None:
    return (
        db.query(ReferenceFieldPolicy)
        .filter(
            ReferenceFieldPolicy.module_id == module_id,
            ReferenceFieldPolicy.field_name == field_name,
            ReferenceFieldPolicy.is_active.is_(True),
        )
        .first()
    )


def validate_reference_value(
    db: Session,
    context: ReferenceContext,
    module_id: str,
    field_name: str,
    value: str,
) -> ReferenceValidationResult:
    seed_rates_field_policies(db)
    policy = get_field_policy(db, module_id, field_name)
    if not policy:
        return ReferenceValidationResult(
            valid=True,
            severity=INFO,
            policy=FREE_TEXT,
            message="No active policy exists for this field; value is treated as free text.",
            object_type="FREE_TEXT",
            gid=value,
        )
    if policy.policy == FREE_TEXT:
        return ReferenceValidationResult(
            valid=True,
            severity=INFO,
            policy=policy.policy,
            message="Free text value accepted.",
            object_type=policy.object_type,
            gid=value,
        )
    reference = find_reference(db, context, policy.object_type, value)
    if reference:
        return ReferenceValidationResult(
            valid=True,
            severity=INFO,
            policy=policy.policy,
            message="Reference found and allowed for current profile.",
            object_type=policy.object_type,
            gid=value,
            domain_name=reference.domain_name,
        )
    if policy.policy == MUST_EXIST:
        return ReferenceValidationResult(
            valid=False,
            severity=policy.severity_when_missing,
            policy=policy.policy,
            message="Reference is required but was not found in the allowed catalog scope.",
            object_type=policy.object_type,
            gid=value,
        )
    return ReferenceValidationResult(
        valid=True,
        severity=policy.severity_when_missing,
        policy=policy.policy,
        message=(
            "Reference was not found; value may represent a new object if the "
            "business process allows it."
        ),
        object_type=policy.object_type,
        gid=value,
    )


def import_reference_records(
    db: Session,
    records: list[dict[str, object]],
    source_type: str,
    source_description: str,
    actor_user_id: str | None,
) -> ReferenceImportBatch:
    batch = ReferenceImportBatch(
        source_type=source_type,
        source_description=source_description,
        status="RUNNING",
        records_received=len(records),
        started_at=datetime.now(UTC).replace(tzinfo=None),
        created_by=actor_user_id,
    )
    db.add(batch)
    db.commit()
    inserted = 0
    updated = 0
    rejected = 0
    for record in records:
        object_type = str(record.get("object_type", "")).upper()
        gid = str(record.get("gid", ""))
        domain_name = str(record.get("domain_name", "")).upper()
        if not object_type or not gid or not domain_name:
            rejected += 1
            continue
        existing = (
            db.query(ReferenceObject)
            .filter(ReferenceObject.object_type == object_type, ReferenceObject.gid == gid)
            .first()
        )
        metadata = record.get("metadata_json", "{}")
        metadata_json = metadata if isinstance(metadata, str) else json.dumps(metadata)
        if existing:
            existing.xid = str(record.get("xid", existing.xid))
            existing.domain_name = domain_name
            existing.display_name = str(record.get("display_name", existing.display_name))
            existing.metadata_json = metadata_json
            existing.sync_batch_id = batch.id
            updated += 1
        else:
            db.add(
                ReferenceObject(
                    object_type=object_type,
                    gid=gid,
                    xid=str(record.get("xid", "")),
                    domain_name=domain_name,
                    display_name=str(record.get("display_name", "")),
                    metadata_json=metadata_json,
                    source=source_type,
                    sync_batch_id=batch.id,
                    last_synced_at=datetime.now(UTC).replace(tzinfo=None),
                )
            )
            inserted += 1
    batch.status = "COMPLETED"
    batch.records_inserted = inserted
    batch.records_updated = updated
    batch.records_rejected = rejected
    batch.finished_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(batch)
    return batch
