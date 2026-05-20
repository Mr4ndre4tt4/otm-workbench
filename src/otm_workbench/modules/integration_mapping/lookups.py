from sqlalchemy.orm import Session

from otm_workbench.models import (
    IntegrationDefinition,
    IntegrationLookupDefinition,
    IntegrationSchemaDocument,
    User,
)
from otm_workbench.modules.integration_mapping.mappings import (
    schema_document_belongs_to_definition,
    schema_path_exists,
)
from otm_workbench.modules.integration_mapping.systems import reject_secret_like_payload


ALLOWED_LOOKUP_TYPES = {"MOCK"}


def normalize_lookup_type(value: object) -> str:
    return str(value or "MOCK").strip().upper()


def create_integration_lookup_definition(
    db: Session,
    *,
    definition: IntegrationDefinition,
    payload: dict[str, object],
    user: User,
) -> IntegrationLookupDefinition:
    lookup_type = normalize_lookup_type(payload.get("lookup_type"))
    if lookup_type not in ALLOWED_LOOKUP_TYPES:
        raise ValueError("lookup_type_invalid")

    source_schema_document_id = str(payload["source_schema_document_id"])
    target_schema_document_id = str(payload["target_schema_document_id"])
    source_document = db.get(IntegrationSchemaDocument, source_schema_document_id)
    target_document = db.get(IntegrationSchemaDocument, target_schema_document_id)
    if not schema_document_belongs_to_definition(source_document, definition.id):
        raise ValueError("source_schema_document_invalid")
    if not schema_document_belongs_to_definition(target_document, definition.id):
        raise ValueError("target_schema_document_invalid")

    input_path = str(payload["input_path"]).strip()
    output_path = str(payload["output_path"]).strip()
    if not schema_path_exists(db, schema_document_id=source_schema_document_id, path=input_path):
        raise ValueError("input_path_invalid")
    if not schema_path_exists(db, schema_document_id=target_schema_document_id, path=output_path):
        raise ValueError("output_path_invalid")

    mock_response_json = str(payload.get("mock_response_json") or "").strip()
    reject_secret_like_payload(
        {
            "name": payload["name"],
            "description": payload.get("description") or "",
            "mock_response_json": mock_response_json,
        }
    )

    lookup = IntegrationLookupDefinition(
        definition_id=definition.id,
        source_schema_document_id=source_schema_document_id,
        target_schema_document_id=target_schema_document_id,
        input_path=input_path,
        output_path=output_path,
        lookup_type=lookup_type,
        name=str(payload["name"]).strip(),
        description=str(payload.get("description") or "").strip(),
        mock_response_json=mock_response_json,
        sequence_index=int(payload.get("sequence_index") or 0),
        status="ACTIVE",
        created_by=user.email,
    )
    db.add(lookup)
    db.commit()
    db.refresh(lookup)
    return lookup


def serialize_integration_lookup_definition(lookup: IntegrationLookupDefinition) -> dict[str, object]:
    return {
        "id": lookup.id,
        "definition_id": lookup.definition_id,
        "source_schema_document_id": lookup.source_schema_document_id,
        "target_schema_document_id": lookup.target_schema_document_id,
        "input_path": lookup.input_path,
        "output_path": lookup.output_path,
        "lookup_type": lookup.lookup_type,
        "name": lookup.name,
        "description": lookup.description,
        "mock_response_json": lookup.mock_response_json,
        "sequence_index": lookup.sequence_index,
        "status": lookup.status,
        "created_by": lookup.created_by,
        "created_at": lookup.created_at.isoformat() if lookup.created_at else None,
        "updated_at": lookup.updated_at.isoformat() if lookup.updated_at else None,
    }
