from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.config import get_settings
from otm_workbench.models import (
    Artifact,
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
    User,
)
from otm_workbench.modules.integration_mapping.definitions import (
    create_integration_definition,
    serialize_integration_definition,
)
from otm_workbench.modules.integration_mapping.payload_artifacts import (
    import_payload_artifact,
    serialize_payload_artifact,
)
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
    return validate_integration_definition(db, definition)


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
