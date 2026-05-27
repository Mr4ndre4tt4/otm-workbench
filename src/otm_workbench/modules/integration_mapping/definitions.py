from otm_workbench.models import IntegrationDefinition, SchemaRoot, User


class UnknownIntegrationSchemaRoot(ValueError):
    def __init__(self, *, field: str, schema_root_id: str) -> None:
        self.field = field
        self.schema_root_id = schema_root_id
        super().__init__(f"{field} references an unknown schema root.")


def normalize_code(value: str) -> str:
    return value.strip().upper()


def normalize_format(value: str) -> str:
    return value.strip().upper()


def schema_root_id_from_payload(payload: dict[str, object], field: str) -> str | None:
    value = payload.get(field)
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def require_schema_root(db, *, schema_root_id: str | None, field: str) -> None:
    if schema_root_id is None:
        return
    if db.get(SchemaRoot, schema_root_id) is None:
        raise UnknownIntegrationSchemaRoot(field=field, schema_root_id=schema_root_id)


def create_integration_definition(
    db,
    *,
    payload: dict[str, object],
    user: User,
    scope: dict[str, object] | None = None,
) -> IntegrationDefinition:
    source_schema_root_id = schema_root_id_from_payload(payload, "source_schema_root_id")
    target_schema_root_id = schema_root_id_from_payload(payload, "target_schema_root_id")
    require_schema_root(db, schema_root_id=source_schema_root_id, field="source_schema_root_id")
    require_schema_root(db, schema_root_id=target_schema_root_id, field="target_schema_root_id")
    definition = IntegrationDefinition(
        project_id=str(scope.get("project_id") or "").strip() or None if scope else None,
        environment_id=str(scope.get("environment_id") or "").strip() or None if scope else None,
        profile_id=str(scope.get("profile_id") or "").strip() or None if scope else None,
        domain_name=str(scope.get("domain_name") or "").strip().upper() or None if scope else None,
        code=normalize_code(str(payload["code"])),
        name=str(payload["name"]).strip(),
        description=str(payload.get("description") or "").strip(),
        source_system=str(payload["source_system"]).strip().upper(),
        target_system=str(payload["target_system"]).strip().upper(),
        source_format=normalize_format(str(payload["source_format"])),
        target_format=normalize_format(str(payload["target_format"])),
        source_schema_root_id=source_schema_root_id,
        target_schema_root_id=target_schema_root_id,
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
        "project_id": definition.project_id,
        "environment_id": definition.environment_id,
        "profile_id": definition.profile_id,
        "domain_name": definition.domain_name,
        "code": definition.code,
        "name": definition.name,
        "description": definition.description,
        "source_system": definition.source_system,
        "target_system": definition.target_system,
        "source_format": definition.source_format,
        "target_format": definition.target_format,
        "source_schema_root_id": definition.source_schema_root_id,
        "target_schema_root_id": definition.target_schema_root_id,
        "status": definition.status,
        "created_by": definition.created_by,
        "created_at": definition.created_at.isoformat() if definition.created_at else None,
        "updated_at": definition.updated_at.isoformat() if definition.updated_at else None,
    }
