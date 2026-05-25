from sqlalchemy.orm import Session

from otm_workbench.models import (
    IntegrationDefinition,
    IntegrationJoinBinding,
    IntegrationJoinBindingHop,
    IntegrationSchemaDocument,
    User,
)
from otm_workbench.modules.integration_mapping.joins import ALLOWED_JOIN_OPERATORS, normalize_join_operator
from otm_workbench.modules.integration_mapping.mappings import (
    schema_document_belongs_to_definition,
    schema_path_exists,
)


def absolute_hop_path(collection_path: str, value_path: str) -> str:
    return f"{collection_path.rstrip('/')}/{value_path.strip('/')}"


def validate_hop_sequences(hops: list[dict[str, object]]) -> None:
    sequences = [int(hop.get("hop_sequence") or 0) for hop in hops]
    if sorted(sequences) != list(range(1, len(hops) + 1)):
        raise ValueError("hop_sequence_invalid")


def validate_result_aliases(hops: list[dict[str, object]]) -> None:
    aliases = [str(hop.get("result_alias") or "").strip() for hop in hops]
    if any(not alias for alias in aliases) or len(set(aliases)) != len(aliases):
        raise ValueError("alias_invalid")


def validate_hop_paths(db: Session, *, source_schema_document_id: str, hop: dict[str, object]) -> None:
    left_collection_path = str(hop["left_collection_path"]).strip()
    left_value_path = str(hop["left_value_path"]).strip()
    right_collection_path = str(hop["right_collection_path"]).strip()
    right_value_path = str(hop["right_value_path"]).strip()
    if left_collection_path == right_collection_path and left_value_path == right_value_path:
        raise ValueError("same_path_invalid")
    for path in (
        left_collection_path,
        right_collection_path,
        absolute_hop_path(left_collection_path, left_value_path),
        absolute_hop_path(right_collection_path, right_value_path),
    ):
        if not schema_path_exists(db, schema_document_id=source_schema_document_id, path=path):
            raise ValueError("path_invalid")


def create_integration_join_binding(
    db: Session,
    *,
    definition: IntegrationDefinition,
    payload: dict[str, object],
    user: User,
) -> IntegrationJoinBinding:
    source_schema_document_id = str(payload["source_schema_document_id"])
    source_document = db.get(IntegrationSchemaDocument, source_schema_document_id)
    if not schema_document_belongs_to_definition(source_document, definition.id):
        raise ValueError("source_schema_document_invalid")

    hops = list(payload.get("hops") or [])
    if not hops:
        raise ValueError("hops_invalid")
    validate_hop_sequences(hops)
    validate_result_aliases(hops)

    root_collection_path = str(payload["root_collection_path"]).strip()
    target_collection_path = str(payload["target_collection_path"]).strip()
    for path in (root_collection_path, target_collection_path):
        if not schema_path_exists(db, schema_document_id=source_schema_document_id, path=path):
            raise ValueError("path_invalid")

    for hop in hops:
        operator = normalize_join_operator(hop.get("operator"))
        if operator not in ALLOWED_JOIN_OPERATORS:
            raise ValueError("operator_invalid")
        hop["operator"] = operator
        validate_hop_paths(db, source_schema_document_id=source_schema_document_id, hop=hop)

    binding = IntegrationJoinBinding(
        definition_id=definition.id,
        source_schema_document_id=source_schema_document_id,
        root_collection_path=root_collection_path,
        target_collection_path=target_collection_path,
        name=str(payload["name"]).strip(),
        description=str(payload.get("description") or "").strip(),
        sequence_index=int(payload.get("sequence_index") or 0),
        status="ACTIVE",
        created_by=user.email,
    )
    db.add(binding)
    db.flush()
    for hop in hops:
        db.add(
            IntegrationJoinBindingHop(
                binding_id=binding.id,
                definition_id=definition.id,
                source_schema_document_id=source_schema_document_id,
                hop_sequence=int(hop["hop_sequence"]),
                left_collection_path=str(hop["left_collection_path"]).strip(),
                left_value_path=str(hop["left_value_path"]).strip(),
                right_collection_path=str(hop["right_collection_path"]).strip(),
                right_value_path=str(hop["right_value_path"]).strip(),
                operator=str(hop["operator"]),
                result_alias=str(hop["result_alias"]).strip(),
                status="ACTIVE",
                created_by=user.email,
            )
        )
    db.commit()
    db.refresh(binding)
    return binding


def join_binding_hops(db: Session, binding_id: str) -> list[IntegrationJoinBindingHop]:
    return (
        db.query(IntegrationJoinBindingHop)
        .filter(IntegrationJoinBindingHop.binding_id == binding_id)
        .order_by(IntegrationJoinBindingHop.hop_sequence, IntegrationJoinBindingHop.created_at)
        .all()
    )


def serialize_integration_join_binding(db: Session, binding: IntegrationJoinBinding) -> dict[str, object]:
    return {
        "id": binding.id,
        "definition_id": binding.definition_id,
        "source_schema_document_id": binding.source_schema_document_id,
        "root_collection_path": binding.root_collection_path,
        "target_collection_path": binding.target_collection_path,
        "name": binding.name,
        "description": binding.description,
        "sequence_index": binding.sequence_index,
        "status": binding.status,
        "created_by": binding.created_by,
        "created_at": binding.created_at.isoformat() if binding.created_at else None,
        "updated_at": binding.updated_at.isoformat() if binding.updated_at else None,
        "hops": [
            {
                "id": hop.id,
                "binding_id": hop.binding_id,
                "hop_sequence": hop.hop_sequence,
                "left_collection_path": hop.left_collection_path,
                "left_value_path": hop.left_value_path,
                "right_collection_path": hop.right_collection_path,
                "right_value_path": hop.right_value_path,
                "operator": hop.operator,
                "result_alias": hop.result_alias,
                "status": hop.status,
            }
            for hop in join_binding_hops(db, binding.id)
        ],
    }
