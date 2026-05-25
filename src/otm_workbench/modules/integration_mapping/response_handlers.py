from sqlalchemy.orm import Session

from otm_workbench.models import (
    IntegrationDefinition,
    IntegrationResponseHandler,
    IntegrationSchemaDocument,
    User,
)
from otm_workbench.modules.integration_mapping.mappings import (
    schema_document_belongs_to_definition,
    schema_path_exists,
)


ALLOWED_RESPONSE_CONDITIONS = {"EXISTS", "EQUALS"}
ALLOWED_RESPONSE_OUTCOMES = {"SUCCESS", "ERROR", "WARNING"}


def normalize_response_condition(value: object) -> str:
    condition = str(value or "EXISTS").strip().upper()
    if condition not in ALLOWED_RESPONSE_CONDITIONS:
        raise ValueError("success_condition_invalid")
    return condition


def normalize_response_outcome(value: object) -> str:
    outcome = str(value or "SUCCESS").strip().upper()
    if outcome not in ALLOWED_RESPONSE_OUTCOMES:
        raise ValueError("outcome_invalid")
    return outcome


def create_integration_response_handler(
    db: Session,
    *,
    definition: IntegrationDefinition,
    payload: dict[str, object],
    user: User,
) -> IntegrationResponseHandler:
    target_schema_document_id = str(payload["target_schema_document_id"])
    target_document = db.get(IntegrationSchemaDocument, target_schema_document_id)
    if not schema_document_belongs_to_definition(target_document, definition.id):
        raise ValueError("target_schema_document_invalid")

    response_path = str(payload["response_path"]).strip()
    if not schema_path_exists(db, schema_document_id=target_schema_document_id, path=response_path):
        raise ValueError("response_path_invalid")
    success_condition = normalize_response_condition(payload.get("success_condition"))
    expected_value = str(payload.get("expected_value") or "").strip()
    if success_condition == "EQUALS" and not expected_value:
        raise ValueError("expected_value_required")

    handler = IntegrationResponseHandler(
        definition_id=definition.id,
        target_schema_document_id=target_schema_document_id,
        response_path=response_path,
        success_condition=success_condition,
        expected_value=expected_value,
        outcome=normalize_response_outcome(payload.get("outcome")),
        name=str(payload["name"]).strip(),
        description=str(payload.get("description") or "").strip(),
        sequence_index=int(payload.get("sequence_index") or 0),
        status="ACTIVE",
        created_by=user.email,
    )
    db.add(handler)
    db.commit()
    db.refresh(handler)
    return handler


def serialize_integration_response_handler(handler: IntegrationResponseHandler) -> dict[str, object]:
    return {
        "id": handler.id,
        "definition_id": handler.definition_id,
        "target_schema_document_id": handler.target_schema_document_id,
        "response_path": handler.response_path,
        "success_condition": handler.success_condition,
        "expected_value": handler.expected_value,
        "outcome": handler.outcome,
        "name": handler.name,
        "description": handler.description,
        "sequence_index": handler.sequence_index,
        "status": handler.status,
        "created_by": handler.created_by,
        "created_at": handler.created_at.isoformat() if handler.created_at else None,
        "updated_at": handler.updated_at.isoformat() if handler.updated_at else None,
    }
