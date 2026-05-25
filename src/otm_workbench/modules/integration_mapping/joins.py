from sqlalchemy.orm import Session

from otm_workbench.models import (
    IntegrationDefinition,
    IntegrationJoinRule,
    IntegrationSchemaDocument,
    User,
)
from otm_workbench.modules.integration_mapping.mappings import (
    schema_document_belongs_to_definition,
    schema_path_exists,
)


ALLOWED_JOIN_OPERATORS = {"EQ", "NE"}


def normalize_join_operator(value: object) -> str:
    return str(value or "EQ").strip().upper()


def create_integration_join_rule(
    db: Session,
    *,
    definition: IntegrationDefinition,
    payload: dict[str, object],
    user: User,
) -> IntegrationJoinRule:
    source_schema_document_id = str(payload["source_schema_document_id"])
    source_document = db.get(IntegrationSchemaDocument, source_schema_document_id)
    if not schema_document_belongs_to_definition(source_document, definition.id):
        raise ValueError("source_schema_document_invalid")

    operator = normalize_join_operator(payload.get("operator"))
    if operator not in ALLOWED_JOIN_OPERATORS:
        raise ValueError("operator_invalid")

    left_path = str(payload["left_path"]).strip()
    right_path = str(payload["right_path"]).strip()
    if not schema_path_exists(db, schema_document_id=source_schema_document_id, path=left_path):
        raise ValueError("left_path_invalid")
    if not schema_path_exists(db, schema_document_id=source_schema_document_id, path=right_path):
        raise ValueError("right_path_invalid")
    if left_path == right_path:
        raise ValueError("same_path_invalid")

    join_rule = IntegrationJoinRule(
        definition_id=definition.id,
        source_schema_document_id=source_schema_document_id,
        left_path=left_path,
        right_path=right_path,
        operator=operator,
        name=str(payload["name"]).strip(),
        description=str(payload.get("description") or "").strip(),
        sequence_index=int(payload.get("sequence_index") or 0),
        status="ACTIVE",
        created_by=user.email,
    )
    db.add(join_rule)
    db.commit()
    db.refresh(join_rule)
    return join_rule


def serialize_integration_join_rule(join_rule: IntegrationJoinRule) -> dict[str, object]:
    return {
        "id": join_rule.id,
        "definition_id": join_rule.definition_id,
        "source_schema_document_id": join_rule.source_schema_document_id,
        "left_path": join_rule.left_path,
        "right_path": join_rule.right_path,
        "operator": join_rule.operator,
        "name": join_rule.name,
        "description": join_rule.description,
        "sequence_index": join_rule.sequence_index,
        "status": join_rule.status,
        "created_by": join_rule.created_by,
        "created_at": join_rule.created_at.isoformat() if join_rule.created_at else None,
        "updated_at": join_rule.updated_at.isoformat() if join_rule.updated_at else None,
    }
