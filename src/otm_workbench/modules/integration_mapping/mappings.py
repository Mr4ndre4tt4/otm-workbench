from sqlalchemy.orm import Session

from otm_workbench.models import (
    IntegrationDefinition,
    IntegrationMapping,
    IntegrationSchemaDocument,
    IntegrationSchemaNode,
    User,
)
from otm_workbench.modules.integration_mapping.transform_types import (
    normalize_transform_type_code,
    transform_type_is_active,
)


def schema_document_belongs_to_definition(document: IntegrationSchemaDocument | None, definition_id: str) -> bool:
    return bool(document and document.definition_id == definition_id)


def schema_path_exists(db: Session, *, schema_document_id: str, path: str) -> bool:
    return (
        db.query(IntegrationSchemaNode)
        .filter(
            IntegrationSchemaNode.schema_document_id == schema_document_id,
            IntegrationSchemaNode.path == path,
        )
        .first()
        is not None
    )


def create_integration_mapping(
    db: Session,
    *,
    definition: IntegrationDefinition,
    payload: dict[str, object],
    user: User,
) -> IntegrationMapping:
    source_schema_document_id = str(payload["source_schema_document_id"])
    target_schema_document_id = str(payload["target_schema_document_id"])
    source_document = db.get(IntegrationSchemaDocument, source_schema_document_id)
    target_document = db.get(IntegrationSchemaDocument, target_schema_document_id)
    if not schema_document_belongs_to_definition(source_document, definition.id):
        raise ValueError("source_schema_document_invalid")
    if not schema_document_belongs_to_definition(target_document, definition.id):
        raise ValueError("target_schema_document_invalid")

    source_path = str(payload["source_path"]).strip()
    target_path = str(payload["target_path"]).strip()
    if not schema_path_exists(db, schema_document_id=source_schema_document_id, path=source_path):
        raise ValueError("source_path_invalid")
    if not schema_path_exists(db, schema_document_id=target_schema_document_id, path=target_path):
        raise ValueError("target_path_invalid")
    transform_type = normalize_transform_type_code(payload.get("transform_type"))
    if not transform_type_is_active(db, transform_type):
        raise ValueError("transform_type_invalid")

    mapping = IntegrationMapping(
        definition_id=definition.id,
        source_schema_document_id=source_schema_document_id,
        target_schema_document_id=target_schema_document_id,
        source_path=source_path,
        target_path=target_path,
        transform_type=transform_type,
        description=str(payload.get("description") or "").strip(),
        sequence_index=int(payload.get("sequence_index") or 0),
        status="ACTIVE",
        created_by=user.email,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping


def serialize_integration_mapping(mapping: IntegrationMapping) -> dict[str, object]:
    return {
        "id": mapping.id,
        "definition_id": mapping.definition_id,
        "source_schema_document_id": mapping.source_schema_document_id,
        "target_schema_document_id": mapping.target_schema_document_id,
        "source_path": mapping.source_path,
        "target_path": mapping.target_path,
        "transform_type": mapping.transform_type,
        "description": mapping.description,
        "sequence_index": mapping.sequence_index,
        "status": mapping.status,
        "created_by": mapping.created_by,
        "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
        "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None,
    }
