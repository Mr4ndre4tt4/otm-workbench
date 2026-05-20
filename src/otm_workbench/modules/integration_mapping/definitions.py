from otm_workbench.models import IntegrationDefinition, User


def normalize_code(value: str) -> str:
    return value.strip().upper()


def normalize_format(value: str) -> str:
    return value.strip().upper()


def create_integration_definition(
    db,
    *,
    payload: dict[str, object],
    user: User,
) -> IntegrationDefinition:
    definition = IntegrationDefinition(
        code=normalize_code(str(payload["code"])),
        name=str(payload["name"]).strip(),
        description=str(payload.get("description") or "").strip(),
        source_system=str(payload["source_system"]).strip().upper(),
        target_system=str(payload["target_system"]).strip().upper(),
        source_format=normalize_format(str(payload["source_format"])),
        target_format=normalize_format(str(payload["target_format"])),
        status="DRAFT",
        created_by=user.email,
    )
    db.add(definition)
    db.commit()
    db.refresh(definition)
    return definition


def serialize_integration_definition(definition: IntegrationDefinition) -> dict[str, object]:
    return {
        "id": definition.id,
        "code": definition.code,
        "name": definition.name,
        "description": definition.description,
        "source_system": definition.source_system,
        "target_system": definition.target_system,
        "source_format": definition.source_format,
        "target_format": definition.target_format,
        "status": definition.status,
        "created_by": definition.created_by,
        "created_at": definition.created_at.isoformat() if definition.created_at else None,
        "updated_at": definition.updated_at.isoformat() if definition.updated_at else None,
    }
