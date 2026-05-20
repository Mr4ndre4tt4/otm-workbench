import json

from sqlalchemy.orm import Session

from otm_workbench.models import AuditLog, DomainEvent, IntegrationDefinition, User


SOURCE_MODULE = "integration_mapping"
TARGET_TYPE = "integration_definition"


def definition_metadata(definition: IntegrationDefinition, extra: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "definition_id": definition.id,
        "code": definition.code,
        "status": definition.status,
        "source_system": definition.source_system,
        "target_system": definition.target_system,
        "source_format": definition.source_format,
        "target_format": definition.target_format,
        **(extra or {}),
    }


def record_definition_audit_event(
    db: Session,
    *,
    definition: IntegrationDefinition,
    user: User,
    action: str,
    event_type: str,
    metadata: dict[str, object],
) -> None:
    payload_json = json.dumps(metadata, sort_keys=True)
    db.add(
        AuditLog(
            actor_user_id=user.email,
            action=action,
            target_type=TARGET_TYPE,
            target_id=definition.id,
            metadata_json=payload_json,
        )
    )
    db.add(
        DomainEvent(
            event_type=event_type,
            source_module=SOURCE_MODULE,
            aggregate_type=TARGET_TYPE,
            aggregate_id=definition.id,
            payload_json=payload_json,
            status="PENDING",
        )
    )
