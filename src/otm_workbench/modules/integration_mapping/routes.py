import json
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.config import get_settings
from otm_workbench.models import (
    Artifact,
    AuditLog,
    IntegrationDefinition,
    IntegrationEndpoint,
    IntegrationJoinRule,
    IntegrationLoopDefinition,
    IntegrationLookupDefinition,
    IntegrationMapping,
    IntegrationPayloadArtifact,
    IntegrationSchemaDocument,
    IntegrationSchemaNode,
    IntegrationSystem,
    Job,
    User,
)
from otm_workbench.modules.rates.exports import file_sha256
from otm_workbench.modules.integration_mapping.definitions import (
    create_integration_definition,
    serialize_integration_definition,
)
from otm_workbench.modules.integration_mapping.audit_events import (
    definition_metadata,
    record_definition_audit_event,
)
from otm_workbench.modules.integration_mapping.payload_artifacts import (
    import_payload_artifact,
    serialize_payload_artifact,
)
from otm_workbench.modules.integration_mapping.preview import build_integration_preview
from otm_workbench.modules.integration_mapping.spec_generator import generate_integration_markdown_spec
from otm_workbench.modules.integration_mapping.mappings import (
    create_integration_mapping,
    serialize_integration_mapping,
)
from otm_workbench.modules.integration_mapping.loops import (
    create_integration_loop_definition,
    serialize_integration_loop_definition,
)
from otm_workbench.modules.integration_mapping.joins import (
    create_integration_join_rule,
    serialize_integration_join_rule,
)
from otm_workbench.modules.integration_mapping.lookups import (
    create_integration_lookup_definition,
    serialize_integration_lookup_definition,
)
from otm_workbench.modules.integration_mapping.schema_tree import parse_payload_artifact_schema_tree
from otm_workbench.modules.integration_mapping.schema_documents import (
    create_schema_document,
    serialize_schema_document,
    serialize_schema_node,
)
from otm_workbench.modules.integration_mapping.systems import (
    create_integration_endpoint,
    create_integration_system,
    serialize_integration_endpoint,
    serialize_integration_system,
)
from otm_workbench.modules.integration_mapping.transform_types import (
    list_active_transform_types,
    serialize_transform_type,
)
from otm_workbench.modules.integration_mapping.validation import validate_integration_definition


router = APIRouter(prefix="/api/v1/modules/integration-mapping", tags=["integration-mapping"])


def serialize_integration_artifact(artifact: Artifact, definition_id: str) -> dict[str, object]:
    return {
        "id": artifact.id,
        "definition_id": definition_id,
        "source_module": artifact.source_module,
        "artifact_type": artifact.artifact_type,
        "file_name": artifact.file_name,
        "content_type": artifact.content_type,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "sensitivity_level": artifact.sensitivity_level,
        "download_url": (
            f"/api/v1/modules/integration-mapping/definitions/{definition_id}/artifacts/{artifact.id}/download"
        ),
    }


def artifact_ids_for_definition_jobs(db: Session, definition_id: str) -> list[str]:
    artifact_ids: list[str] = []
    jobs = (
        db.query(Job)
        .filter(Job.source_module == "integration_mapping")
        .order_by(Job.created_at.desc())
        .all()
    )
    for job in jobs:
        try:
            input_payload = json.loads(job.input_json or "{}")
            result_payload = json.loads(job.result_json or "{}")
        except json.JSONDecodeError:
            continue
        if input_payload.get("definition_id") != definition_id:
            continue
        artifact_id = result_payload.get("artifact_id")
        if isinstance(artifact_id, str) and artifact_id not in artifact_ids:
            artifact_ids.append(artifact_id)
    return artifact_ids


def list_definition_generated_artifacts(db: Session, definition_id: str) -> list[Artifact]:
    artifacts: list[Artifact] = []
    for artifact_id in artifact_ids_for_definition_jobs(db, definition_id):
        artifact = db.get(Artifact, artifact_id)
        if artifact is not None and artifact.source_module == "integration_mapping":
            artifacts.append(artifact)
    return artifacts


class IntegrationDefinitionCreateRequest(BaseModel):
    code: str
    name: str
    description: str = ""
    source_system: str
    target_system: str
    source_format: str
    target_format: str
    status: str | None = None


class IntegrationSystemCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str
    name: str
    system_type: str
    base_url: str = ""
    description: str = ""


class IntegrationEndpointCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    system_id: str | None = None
    code: str
    name: str
    path: str
    method: str
    payload_format: str
    description: str = ""


class IntegrationPayloadArtifactCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    payload_role: str
    payload_format: str
    file_name: str
    content: str
    description: str = ""


class IntegrationMappingCreateRequest(BaseModel):
    source_schema_document_id: str
    target_schema_document_id: str
    source_path: str
    target_path: str
    transform_type: str = "DIRECT"
    description: str = ""
    sequence_index: int = 0


class IntegrationLoopDefinitionCreateRequest(BaseModel):
    source_schema_document_id: str
    target_schema_document_id: str
    source_collection_path: str
    target_collection_path: str
    name: str
    description: str = ""
    sequence_index: int = 0


class IntegrationJoinRuleCreateRequest(BaseModel):
    source_schema_document_id: str
    left_path: str
    right_path: str
    operator: str = "EQ"
    name: str
    description: str = ""
    sequence_index: int = 0


class IntegrationLookupDefinitionCreateRequest(BaseModel):
    source_schema_document_id: str
    target_schema_document_id: str
    input_path: str
    output_path: str
    lookup_type: str = "MOCK"
    name: str
    description: str = ""
    mock_response_json: str = ""
    sequence_index: int = 0


@router.get("/health")
def integration_mapping_health(user: User = Depends(require_user)):
    return {
        "status": "ok",
        "module": "integration_mapping",
        "mode": "specification_first",
    }


@router.get("/transform-types")
def list_transform_types(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    transform_types = list_active_transform_types(db)
    items = [serialize_transform_type(transform_type) for transform_type in transform_types]
    return PageResponse(items=items, total=len(items))


@router.post("/definitions")
def create_definition(
    payload: IntegrationDefinitionCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    try:
        definition = create_integration_definition(db, payload=payload.model_dump(), user=user)
    except IntegrityError as exc:
        db.rollback()
        raise api_error(
            409,
            "INTEGRATION_DEFINITION_CODE_EXISTS",
            "Integration definition code already exists.",
        ) from exc
    record_definition_audit_event(
        db,
        definition=definition,
        user=user,
        action="integration_mapping.definition.create",
        event_type="integration_mapping.definition.created",
        metadata=definition_metadata(definition),
    )
    db.commit()
    return serialize_integration_definition(definition)


@router.get("/definitions")
def list_definitions(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definitions = db.query(IntegrationDefinition).order_by(IntegrationDefinition.created_at.desc()).all()
    items = [serialize_integration_definition(definition) for definition in definitions]
    return PageResponse(items=items, total=len(items))


@router.get("/definitions/{definition_id}")
def get_definition(
    definition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    return serialize_integration_definition(definition)


@router.post("/definitions/{definition_id}/validate")
def validate_definition(
    definition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    validation = validate_integration_definition(db, definition)
    record_definition_audit_event(
        db,
        definition=definition,
        user=user,
        action="integration_mapping.definition.validate",
        event_type="integration_mapping.definition.validated",
        metadata=definition_metadata(
            definition,
            {"is_valid": validation["is_valid"], "issue_count": validation["issue_count"]},
        ),
    )
    db.commit()
    return validation


@router.post("/definitions/{definition_id}/preview")
def preview_definition(
    definition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    validation = validate_integration_definition(db, definition)
    if not validation["is_valid"]:
        raise api_error(
            409,
            "INTEGRATION_PREVIEW_VALIDATION_FAILED",
            "Integration Mapping definition must pass validation before preview.",
            {"issue_count": validation["issue_count"], "issues": validation["issues"]},
        )
    payload = build_integration_preview(
        db,
        definition=definition,
        validation=validation,
        artifact_root=get_settings().artifact_root,
        created_by=user.email,
    )
    record_definition_audit_event(
        db,
        definition=definition,
        user=user,
        action="integration_mapping.definition.preview",
        event_type="integration_mapping.definition.previewed",
        metadata=definition_metadata(
            definition,
            {
                "artifact_id": payload["artifact_id"],
                "job_id": payload["job_id"],
                "is_valid": validation["is_valid"],
                "issue_count": validation["issue_count"],
            },
        ),
    )
    db.commit()
    return payload


@router.post("/definitions/{definition_id}/generate-spec")
def generate_definition_spec(
    definition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    validation = validate_integration_definition(db, definition)
    readiness = validation["readiness"]
    if not readiness["specification_ready"]:
        raise api_error(
            409,
            "INTEGRATION_SPEC_VALIDATION_FAILED",
            "Integration Mapping definition must be specification-ready before spec generation.",
            {"issue_count": validation["issue_count"], "issues": validation["issues"]},
        )
    payload = generate_integration_markdown_spec(
        db,
        definition=definition,
        validation=validation,
        artifact_root=get_settings().artifact_root,
        created_by=user.email,
    )
    record_definition_audit_event(
        db,
        definition=definition,
        user=user,
        action="integration_mapping.definition.generate_spec",
        event_type="integration_mapping.definition.spec_generated",
        metadata=definition_metadata(
            definition,
            {
                "artifact_id": payload["artifact_id"],
                "job_id": payload["job_id"],
                "is_valid": validation["is_valid"],
                "issue_count": validation["issue_count"],
            },
        ),
    )
    db.commit()
    return payload


@router.get("/definitions/{definition_id}/artifacts")
def list_definition_artifacts(
    definition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    artifacts = list_definition_generated_artifacts(db, definition.id)
    return {
        "definition_id": definition.id,
        "items": [serialize_integration_artifact(artifact, definition.id) for artifact in artifacts],
        "total": len(artifacts),
    }


@router.get("/definitions/{definition_id}/artifacts/{artifact_id}/download")
def download_definition_artifact(
    definition_id: str,
    artifact_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    artifact = next(
        (item for item in list_definition_generated_artifacts(db, definition.id) if item.id == artifact_id),
        None,
    )
    if artifact is None:
        raise api_error(404, "INTEGRATION_ARTIFACT_NOT_FOUND", "Integration Mapping artifact not found.")

    path = Path(artifact.file_path)
    if not path.exists() or not path.is_file():
        raise api_error(404, "INTEGRATION_ARTIFACT_FILE_NOT_FOUND", "Integration Mapping artifact file not found.")

    actual_sha256, actual_size = file_sha256(path)
    if actual_sha256 != artifact.sha256:
        raise api_error(409, "INTEGRATION_ARTIFACT_HASH_MISMATCH", "Integration Mapping artifact hash mismatch.")

    db.add(
        AuditLog(
            actor_user_id=user.email,
            action="integration_mapping.artifact.download",
            target_type="artifact",
            target_id=artifact.id,
            metadata_json=json.dumps(
                {
                    "artifact_id": artifact.id,
                    "artifact_type": artifact.artifact_type,
                    "definition_id": definition.id,
                    "source_module": artifact.source_module,
                    "sha256": artifact.sha256,
                    "size_bytes": actual_size,
                },
                sort_keys=True,
            ),
        )
    )
    db.commit()
    return FileResponse(
        path,
        media_type=artifact.content_type,
        filename=artifact.file_name,
        headers={"X-Artifact-SHA256": artifact.sha256},
    )


@router.post("/systems")
def create_system(
    payload: IntegrationSystemCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    try:
        system = create_integration_system(db, payload=payload.model_dump(), user=user)
    except IntegrityError as exc:
        db.rollback()
        raise api_error(409, "INTEGRATION_SYSTEM_CODE_EXISTS", "Integration system code already exists.") from exc
    except ValueError as exc:
        raise api_error(400, "INTEGRATION_SECRET_RISK", str(exc)) from exc
    return serialize_integration_system(system)


@router.get("/systems")
def list_systems(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    systems = db.query(IntegrationSystem).order_by(IntegrationSystem.created_at.desc()).all()
    items = [serialize_integration_system(system) for system in systems]
    return PageResponse(items=items, total=len(items))


@router.post("/systems/{system_id}/endpoints")
def create_endpoint(
    system_id: str,
    payload: IntegrationEndpointCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    system = db.get(IntegrationSystem, system_id)
    if system is None:
        raise api_error(404, "INTEGRATION_SYSTEM_NOT_FOUND", "Integration system not found.")
    try:
        endpoint = create_integration_endpoint(db, system=system, payload=payload.model_dump(), user=user)
    except ValueError as exc:
        raise api_error(400, "INTEGRATION_SECRET_RISK", str(exc)) from exc
    return serialize_integration_endpoint(endpoint)


@router.get("/systems/{system_id}/endpoints")
def list_endpoints(
    system_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    system = db.get(IntegrationSystem, system_id)
    if system is None:
        raise api_error(404, "INTEGRATION_SYSTEM_NOT_FOUND", "Integration system not found.")
    endpoints = (
        db.query(IntegrationEndpoint)
        .filter(IntegrationEndpoint.system_id == system.id)
        .order_by(IntegrationEndpoint.created_at.desc())
        .all()
    )
    items = [serialize_integration_endpoint(endpoint) for endpoint in endpoints]
    return PageResponse(items=items, total=len(items))


@router.post("/definitions/{definition_id}/payload-artifacts")
def create_payload_artifact(
    definition_id: str,
    payload: IntegrationPayloadArtifactCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    try:
        payload_artifact = import_payload_artifact(
            db,
            definition=definition,
            payload=payload.model_dump(),
            artifact_root=get_settings().artifact_root,
            user=user,
        )
    except ValueError as exc:
        if str(exc) == "payload_format_unsupported":
            raise api_error(
                400,
                "INTEGRATION_PAYLOAD_FORMAT_UNSUPPORTED",
                "Integration payload format must be XML or JSON.",
            ) from exc
        raise api_error(400, "INTEGRATION_SECRET_RISK", str(exc)) from exc
    artifact = db.get(Artifact, payload_artifact.artifact_id)
    return serialize_payload_artifact(payload_artifact, artifact)


@router.get("/definitions/{definition_id}/payload-artifacts")
def list_payload_artifacts(
    definition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    rows = (
        db.query(IntegrationPayloadArtifact, Artifact)
        .join(Artifact, Artifact.id == IntegrationPayloadArtifact.artifact_id)
        .filter(IntegrationPayloadArtifact.definition_id == definition.id)
        .order_by(IntegrationPayloadArtifact.created_at.desc())
        .all()
    )
    items = [serialize_payload_artifact(payload_artifact, artifact) for payload_artifact, artifact in rows]
    return PageResponse(items=items, total=len(items))


@router.post("/payload-artifacts/{payload_artifact_id}/parse-schema-tree")
def parse_payload_artifact_schema(
    payload_artifact_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    payload_artifact = db.get(IntegrationPayloadArtifact, payload_artifact_id)
    if payload_artifact is None:
        raise api_error(
            404,
            "INTEGRATION_PAYLOAD_ARTIFACT_NOT_FOUND",
            "Integration payload artifact not found.",
        )
    artifact = db.get(Artifact, payload_artifact.artifact_id)
    if artifact is None:
        raise api_error(404, "ARTIFACT_NOT_FOUND", "Artifact not found.")
    try:
        tree = parse_payload_artifact_schema_tree(artifact.file_path, payload_artifact.payload_format)
    except ValueError as exc:
        raise api_error(
            400,
            "INTEGRATION_PAYLOAD_FORMAT_UNSUPPORTED",
            "Integration payload format must be XML or JSON.",
        ) from exc
    return {
        "payload_artifact_id": payload_artifact.id,
        "definition_id": payload_artifact.definition_id,
        "payload_format": payload_artifact.payload_format,
        "tree": tree,
    }


@router.post("/payload-artifacts/{payload_artifact_id}/schema-documents")
def create_payload_schema_document(
    payload_artifact_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    payload_artifact = db.get(IntegrationPayloadArtifact, payload_artifact_id)
    if payload_artifact is None:
        raise api_error(
            404,
            "INTEGRATION_PAYLOAD_ARTIFACT_NOT_FOUND",
            "Integration payload artifact not found.",
        )
    artifact = db.get(Artifact, payload_artifact.artifact_id)
    if artifact is None:
        raise api_error(404, "ARTIFACT_NOT_FOUND", "Artifact not found.")
    document = create_schema_document(db, payload_artifact=payload_artifact, artifact=artifact, user=user)
    return serialize_schema_document(document)


@router.get("/definitions/{definition_id}/schema-documents")
def list_schema_documents(
    definition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    documents = (
        db.query(IntegrationSchemaDocument)
        .filter(IntegrationSchemaDocument.definition_id == definition.id)
        .order_by(IntegrationSchemaDocument.created_at.desc())
        .all()
    )
    items = [serialize_schema_document(document) for document in documents]
    return PageResponse(items=items, total=len(items))


@router.get("/schema-documents/{schema_document_id}/nodes")
def list_schema_nodes(
    schema_document_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    document = db.get(IntegrationSchemaDocument, schema_document_id)
    if document is None:
        raise api_error(404, "INTEGRATION_SCHEMA_DOCUMENT_NOT_FOUND", "Integration schema document not found.")
    nodes = (
        db.query(IntegrationSchemaNode)
        .filter(IntegrationSchemaNode.schema_document_id == document.id)
        .order_by(IntegrationSchemaNode.sequence_index)
        .all()
    )
    items = [serialize_schema_node(node) for node in nodes]
    return PageResponse(items=items, total=len(items))


@router.post("/definitions/{definition_id}/mappings")
def create_mapping(
    definition_id: str,
    payload: IntegrationMappingCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    try:
        mapping = create_integration_mapping(db, definition=definition, payload=payload.model_dump(), user=user)
    except ValueError as exc:
        if "schema_document_invalid" in str(exc):
            raise api_error(
                400,
                "INTEGRATION_MAPPING_SCHEMA_DOCUMENT_INVALID",
                "Mapping schema documents must belong to the Integration Definition.",
            ) from exc
        if str(exc) == "transform_type_invalid":
            raise api_error(
                400,
                "INTEGRATION_MAPPING_TRANSFORM_TYPE_INVALID",
                "Mapping transform_type must be active in the Integration Mapping catalog.",
            ) from exc
        raise api_error(
            400,
            "INTEGRATION_MAPPING_PATH_INVALID",
            "Mapping source_path and target_path must exist in their schema documents.",
        ) from exc
    return serialize_integration_mapping(mapping)


@router.get("/definitions/{definition_id}/mappings")
def list_mappings(
    definition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    mappings = (
        db.query(IntegrationMapping)
        .filter(IntegrationMapping.definition_id == definition.id)
        .order_by(IntegrationMapping.sequence_index, IntegrationMapping.created_at)
        .all()
    )
    items = [serialize_integration_mapping(mapping) for mapping in mappings]
    return PageResponse(items=items, total=len(items))


@router.get("/mappings/{mapping_id}")
def get_mapping(
    mapping_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    mapping = db.get(IntegrationMapping, mapping_id)
    if mapping is None:
        raise api_error(404, "INTEGRATION_MAPPING_NOT_FOUND", "Integration mapping not found.")
    return serialize_integration_mapping(mapping)


@router.post("/definitions/{definition_id}/loops")
def create_loop_definition(
    definition_id: str,
    payload: IntegrationLoopDefinitionCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    try:
        loop = create_integration_loop_definition(db, definition=definition, payload=payload.model_dump(), user=user)
    except ValueError as exc:
        if "schema_document_invalid" in str(exc):
            raise api_error(
                400,
                "INTEGRATION_LOOP_SCHEMA_DOCUMENT_INVALID",
                "Loop schema documents must belong to the Integration Definition.",
            ) from exc
        raise api_error(
            400,
            "INTEGRATION_LOOP_PATH_INVALID",
            "Loop source_collection_path and target_collection_path must exist in their schema documents.",
        ) from exc
    return serialize_integration_loop_definition(loop)


@router.get("/definitions/{definition_id}/loops")
def list_loop_definitions(
    definition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    loops = (
        db.query(IntegrationLoopDefinition)
        .filter(IntegrationLoopDefinition.definition_id == definition.id)
        .order_by(IntegrationLoopDefinition.sequence_index, IntegrationLoopDefinition.created_at)
        .all()
    )
    items = [serialize_integration_loop_definition(loop) for loop in loops]
    return PageResponse(items=items, total=len(items))


@router.get("/loops/{loop_id}")
def get_loop_definition(
    loop_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    loop = db.get(IntegrationLoopDefinition, loop_id)
    if loop is None:
        raise api_error(404, "INTEGRATION_LOOP_NOT_FOUND", "Integration loop definition not found.")
    return serialize_integration_loop_definition(loop)


@router.post("/definitions/{definition_id}/joins")
def create_join_rule(
    definition_id: str,
    payload: IntegrationJoinRuleCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    try:
        join_rule = create_integration_join_rule(db, definition=definition, payload=payload.model_dump(), user=user)
    except ValueError as exc:
        if str(exc) == "source_schema_document_invalid":
            raise api_error(
                400,
                "INTEGRATION_JOIN_SCHEMA_DOCUMENT_INVALID",
                "Join schema document must belong to the Integration Definition.",
            ) from exc
        if str(exc) == "operator_invalid":
            raise api_error(
                400,
                "INTEGRATION_JOIN_OPERATOR_INVALID",
                "Join operator must be one of the controlled Integration Mapping operators.",
            ) from exc
        if str(exc) == "same_path_invalid":
            raise api_error(
                400,
                "INTEGRATION_JOIN_SAME_PATH",
                "Join left_path and right_path must reference different source schema paths.",
            ) from exc
        raise api_error(
            400,
            "INTEGRATION_JOIN_PATH_INVALID",
            "Join left_path and right_path must exist in the source schema document.",
        ) from exc
    return serialize_integration_join_rule(join_rule)


@router.get("/definitions/{definition_id}/joins")
def list_join_rules(
    definition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    join_rules = (
        db.query(IntegrationJoinRule)
        .filter(IntegrationJoinRule.definition_id == definition.id)
        .order_by(IntegrationJoinRule.sequence_index, IntegrationJoinRule.created_at)
        .all()
    )
    items = [serialize_integration_join_rule(join_rule) for join_rule in join_rules]
    return PageResponse(items=items, total=len(items))


@router.get("/joins/{join_rule_id}")
def get_join_rule(
    join_rule_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    join_rule = db.get(IntegrationJoinRule, join_rule_id)
    if join_rule is None:
        raise api_error(404, "INTEGRATION_JOIN_NOT_FOUND", "Integration join rule not found.")
    return serialize_integration_join_rule(join_rule)


@router.post("/definitions/{definition_id}/lookups")
def create_lookup_definition(
    definition_id: str,
    payload: IntegrationLookupDefinitionCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    try:
        lookup = create_integration_lookup_definition(
            db,
            definition=definition,
            payload=payload.model_dump(),
            user=user,
        )
    except ValueError as exc:
        if str(exc) == "lookup_type_invalid":
            raise api_error(
                400,
                "INTEGRATION_LOOKUP_TYPE_INVALID",
                "Lookup type must be MOCK for Integration Mapping MVP0.",
            ) from exc
        if "schema_document_invalid" in str(exc):
            raise api_error(
                400,
                "INTEGRATION_LOOKUP_SCHEMA_DOCUMENT_INVALID",
                "Lookup schema documents must belong to the Integration Definition.",
            ) from exc
        if "secret" in str(exc).lower() or "credential" in str(exc).lower():
            raise api_error(400, "INTEGRATION_SECRET_RISK", str(exc)) from exc
        raise api_error(
            400,
            "INTEGRATION_LOOKUP_PATH_INVALID",
            "Lookup input_path and output_path must exist in their schema documents.",
        ) from exc
    return serialize_integration_lookup_definition(lookup)


@router.get("/definitions/{definition_id}/lookups")
def list_lookup_definitions(
    definition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    lookups = (
        db.query(IntegrationLookupDefinition)
        .filter(IntegrationLookupDefinition.definition_id == definition.id)
        .order_by(IntegrationLookupDefinition.sequence_index, IntegrationLookupDefinition.created_at)
        .all()
    )
    items = [serialize_integration_lookup_definition(lookup) for lookup in lookups]
    return PageResponse(items=items, total=len(items))


@router.get("/lookups/{lookup_id}")
def get_lookup_definition(
    lookup_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    lookup = db.get(IntegrationLookupDefinition, lookup_id)
    if lookup is None:
        raise api_error(404, "INTEGRATION_LOOKUP_NOT_FOUND", "Integration lookup definition not found.")
    return serialize_integration_lookup_definition(lookup)
