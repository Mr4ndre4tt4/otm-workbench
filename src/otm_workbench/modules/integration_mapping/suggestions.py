from sqlalchemy.orm import Session

from otm_workbench.models import IntegrationSchemaDocument, IntegrationSchemaNode
from otm_workbench.modules.integration_mapping.mappings import schema_document_belongs_to_definition


def semantic_node_key(node: IntegrationSchemaNode) -> str:
    key = node.name.lower()
    if key.endswith("gid"):
        key = f"{key[:-3]}id"
    return "".join(character for character in key if character.isalnum())


def leaf_schema_nodes(db: Session, *, schema_document_id: str) -> list[IntegrationSchemaNode]:
    return (
        db.query(IntegrationSchemaNode)
        .filter(IntegrationSchemaNode.schema_document_id == schema_document_id)
        .order_by(IntegrationSchemaNode.sequence_index, IntegrationSchemaNode.path)
        .all()
    )


def suggest_integration_mappings(
    db: Session,
    *,
    definition_id: str,
    source_schema_document_id: str,
    target_schema_document_id: str,
) -> list[dict[str, object]]:
    source_document = db.get(IntegrationSchemaDocument, source_schema_document_id)
    target_document = db.get(IntegrationSchemaDocument, target_schema_document_id)
    if not schema_document_belongs_to_definition(source_document, definition_id):
        raise ValueError("source_schema_document_invalid")
    if not schema_document_belongs_to_definition(target_document, definition_id):
        raise ValueError("target_schema_document_invalid")

    source_nodes = [
        node
        for node in leaf_schema_nodes(db, schema_document_id=source_schema_document_id)
        if node.node_type.lower() not in {"array", "object"}
    ]
    target_nodes = [
        node
        for node in leaf_schema_nodes(db, schema_document_id=target_schema_document_id)
        if node.node_type.lower() not in {"array", "object"}
    ]
    suggestions: list[dict[str, object]] = []
    used_targets: set[str] = set()
    for source_node in source_nodes:
        source_key = semantic_node_key(source_node)
        target_node = next(
            (
                candidate
                for candidate in target_nodes
                if candidate.id not in used_targets and semantic_node_key(candidate) == source_key
            ),
            None,
        )
        if target_node is None:
            continue
        used_targets.add(target_node.id)
        suggestions.append(
            {
                "id": (
                    f"{source_schema_document_id}:{source_node.path}->"
                    f"{target_schema_document_id}:{target_node.path}"
                ),
                "definition_id": definition_id,
                "source_schema_document_id": source_schema_document_id,
                "target_schema_document_id": target_schema_document_id,
                "source_path": source_node.path,
                "target_path": target_node.path,
                "transform_type": "DIRECT",
                "confidence": 0.9,
                "reason": f"Normalized schema leaf names match: {source_key}",
            }
        )
    return suggestions[:10]
