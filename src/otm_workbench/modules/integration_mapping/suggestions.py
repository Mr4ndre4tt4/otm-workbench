from dataclasses import dataclass

from sqlalchemy.orm import Session

from otm_workbench.models import IntegrationSchemaDocument, IntegrationSchemaNode
from otm_workbench.modules.integration_mapping.mappings import schema_document_belongs_to_definition


@dataclass(frozen=True)
class MappingSuggestionCandidate:
    target_node: IntegrationSchemaNode
    confidence: float
    reason: str


def semantic_node_key(node: IntegrationSchemaNode) -> str:
    key = node.name.lower()
    if key.endswith("gid"):
        key = f"{key[:-3]}id"
    return "".join(character for character in key if character.isalnum())


def semantic_path(path: str) -> str:
    return "".join(character for character in path.lower() if character.isalnum())


def leaf_schema_nodes(db: Session, *, schema_document_id: str) -> list[IntegrationSchemaNode]:
    return (
        db.query(IntegrationSchemaNode)
        .filter(IntegrationSchemaNode.schema_document_id == schema_document_id)
        .order_by(IntegrationSchemaNode.sequence_index, IntegrationSchemaNode.path)
        .all()
    )


def score_candidate(source_node: IntegrationSchemaNode, target_node: IntegrationSchemaNode) -> MappingSuggestionCandidate | None:
    source_key = semantic_node_key(source_node)
    target_key = semantic_node_key(target_node)
    source_path_key = semantic_path(source_node.path)
    target_path_key = semantic_path(target_node.path)

    if source_key == target_key:
        return MappingSuggestionCandidate(
            target_node=target_node,
            confidence=0.9,
            reason=f"EXACT_NAME: normalized schema leaf names match: {source_key}",
        )

    if (
        source_key == "stopsequence"
        and target_key == "sequence"
        and "shipmentstop" in source_path_key
        and "deliveries" in target_path_key
    ):
        return MappingSuggestionCandidate(
            target_node=target_node,
            confidence=0.82,
            reason="OTM_CONTEXT_SYNONYM: ShipmentStop StopSequence maps to delivery sequence",
        )

    if (
        source_key in {"releaserefnumvalue", "refnumvalue"}
        and target_key in {"accesskey", "chaveacesso"}
        and "releaserefnum" in source_path_key
    ):
        return MappingSuggestionCandidate(
            target_node=target_node,
            confidence=0.78,
            reason="OTM_REFNUM_ACCESS_KEY: ReleaseRefnumValue can populate accessKey",
        )

    return None


def best_candidate(
    source_node: IntegrationSchemaNode,
    target_nodes: list[IntegrationSchemaNode],
    *,
    used_target_ids: set[str],
) -> MappingSuggestionCandidate | None:
    candidates = [
        candidate
        for target_node in target_nodes
        if target_node.id not in used_target_ids
        for candidate in [score_candidate(source_node, target_node)]
        if candidate is not None
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda candidate: (-candidate.confidence, candidate.target_node.sequence_index, candidate.target_node.path))
    top_candidate = candidates[0]
    tied_candidates = [
        candidate
        for candidate in candidates
        if candidate.confidence == top_candidate.confidence
        and candidate.reason == top_candidate.reason
    ]
    if len(tied_candidates) > 1 and top_candidate.reason.startswith("EXACT_NAME"):
        source_key = semantic_node_key(source_node)
        return MappingSuggestionCandidate(
            target_node=top_candidate.target_node,
            confidence=0.75,
            reason=f"AMBIGUOUS_EXACT_NAME: {len(tied_candidates)} target nodes normalize to {source_key}",
        )
    return top_candidate


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
        candidate = best_candidate(source_node, target_nodes, used_target_ids=used_targets)
        if candidate is None:
            continue
        target_node = candidate.target_node
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
                "confidence": candidate.confidence,
                "reason": candidate.reason,
            }
        )
    suggestions.sort(key=lambda item: (-float(item["confidence"]), str(item["source_path"]), str(item["target_path"])))
    return suggestions[:10]
