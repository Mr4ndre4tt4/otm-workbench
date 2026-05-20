from sqlalchemy.orm import Session

from otm_workbench.models import (
    Artifact,
    IntegrationPayloadArtifact,
    IntegrationSchemaDocument,
    IntegrationSchemaNode,
    User,
)
from otm_workbench.modules.integration_mapping.schema_tree import parse_payload_artifact_schema_tree


def flatten_tree(node: dict[str, object], parent_path: str | None = None) -> list[dict[str, object]]:
    current = {
        "name": str(node["name"]),
        "path": str(node["path"]),
        "node_type": str(node["node_type"]),
        "parent_path": parent_path,
    }
    rows = [current]
    for child in node.get("children", []):
        rows.extend(flatten_tree(child, current["path"]))
    return rows


def create_schema_document(
    db: Session,
    *,
    payload_artifact: IntegrationPayloadArtifact,
    artifact: Artifact,
    user: User,
) -> IntegrationSchemaDocument:
    tree = parse_payload_artifact_schema_tree(artifact.file_path, payload_artifact.payload_format)
    flattened = flatten_tree(tree)
    document = IntegrationSchemaDocument(
        definition_id=payload_artifact.definition_id,
        payload_artifact_id=payload_artifact.id,
        payload_format=payload_artifact.payload_format,
        root_name=str(tree["name"]),
        node_count=len(flattened),
        status="PARSED",
        created_by=user.email,
    )
    db.add(document)
    db.flush()
    for index, row in enumerate(flattened, start=1):
        db.add(
            IntegrationSchemaNode(
                schema_document_id=document.id,
                parent_path=row["parent_path"],
                path=row["path"],
                name=row["name"],
                node_type=row["node_type"],
                sequence_index=index,
            )
        )
    db.commit()
    db.refresh(document)
    return document


def serialize_schema_document(document: IntegrationSchemaDocument) -> dict[str, object]:
    return {
        "id": document.id,
        "definition_id": document.definition_id,
        "payload_artifact_id": document.payload_artifact_id,
        "payload_format": document.payload_format,
        "root_name": document.root_name,
        "node_count": document.node_count,
        "status": document.status,
        "created_by": document.created_by,
        "created_at": document.created_at.isoformat() if document.created_at else None,
        "updated_at": document.updated_at.isoformat() if document.updated_at else None,
    }


def serialize_schema_node(node: IntegrationSchemaNode) -> dict[str, object]:
    return {
        "id": node.id,
        "schema_document_id": node.schema_document_id,
        "parent_path": node.parent_path,
        "path": node.path,
        "name": node.name,
        "node_type": node.node_type,
        "sequence_index": node.sequence_index,
    }
