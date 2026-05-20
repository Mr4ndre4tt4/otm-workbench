from sqlalchemy.orm import Session

from otm_workbench.models import (
    IntegrationDefinition,
    IntegrationLoopDefinition,
    IntegrationSchemaDocument,
    User,
)
from otm_workbench.modules.integration_mapping.mappings import (
    schema_document_belongs_to_definition,
    schema_path_exists,
)


def create_integration_loop_definition(
    db: Session,
    *,
    definition: IntegrationDefinition,
    payload: dict[str, object],
    user: User,
) -> IntegrationLoopDefinition:
    source_schema_document_id = str(payload["source_schema_document_id"])
    target_schema_document_id = str(payload["target_schema_document_id"])
    source_document = db.get(IntegrationSchemaDocument, source_schema_document_id)
    target_document = db.get(IntegrationSchemaDocument, target_schema_document_id)
    if not schema_document_belongs_to_definition(source_document, definition.id):
        raise ValueError("source_schema_document_invalid")
    if not schema_document_belongs_to_definition(target_document, definition.id):
        raise ValueError("target_schema_document_invalid")

    source_collection_path = str(payload["source_collection_path"]).strip()
    target_collection_path = str(payload["target_collection_path"]).strip()
    if not schema_path_exists(db, schema_document_id=source_schema_document_id, path=source_collection_path):
        raise ValueError("source_collection_path_invalid")
    if not schema_path_exists(db, schema_document_id=target_schema_document_id, path=target_collection_path):
        raise ValueError("target_collection_path_invalid")

    loop = IntegrationLoopDefinition(
        definition_id=definition.id,
        source_schema_document_id=source_schema_document_id,
        target_schema_document_id=target_schema_document_id,
        source_collection_path=source_collection_path,
        target_collection_path=target_collection_path,
        name=str(payload["name"]).strip(),
        description=str(payload.get("description") or "").strip(),
        sequence_index=int(payload.get("sequence_index") or 0),
        status="ACTIVE",
        created_by=user.email,
    )
    db.add(loop)
    db.commit()
    db.refresh(loop)
    return loop


def serialize_integration_loop_definition(loop: IntegrationLoopDefinition) -> dict[str, object]:
    return {
        "id": loop.id,
        "definition_id": loop.definition_id,
        "source_schema_document_id": loop.source_schema_document_id,
        "target_schema_document_id": loop.target_schema_document_id,
        "source_collection_path": loop.source_collection_path,
        "target_collection_path": loop.target_collection_path,
        "name": loop.name,
        "description": loop.description,
        "sequence_index": loop.sequence_index,
        "status": loop.status,
        "created_by": loop.created_by,
        "created_at": loop.created_at.isoformat() if loop.created_at else None,
        "updated_at": loop.updated_at.isoformat() if loop.updated_at else None,
    }
