import json

from sqlalchemy.orm import Session

from otm_workbench.models import (
    IntegrationDefinition,
    IntegrationEnrichedField,
    IntegrationEnrichmentStep,
    IntegrationEnrichmentSubStep,
    IntegrationSchemaDocument,
    User,
)
from otm_workbench.modules.integration_mapping.mappings import (
    schema_document_belongs_to_definition,
    schema_path_exists,
)


ALLOWED_ENRICHMENT_STEP_TYPES = {"SINGLE", "CHAIN", "LOOP"}
ALLOWED_ENRICHMENT_POLICIES = {"FAIL", "WARN", "USE_DEFAULT", "SKIP"}
ALLOWED_ENRICHED_FIELD_CARDINALITIES = {"SCALAR", "ARRAY", "LOOP_SCOPED"}


def normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("key_source_fields_invalid")
    items = [str(item).strip() for item in value if str(item).strip()]
    if not items:
        raise ValueError("key_source_fields_invalid")
    return items


def normalize_response_field_mappings(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("response_field_mappings_invalid")
    items: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("response_field_mappings_invalid")
        response_path = str(item.get("response_path") or "").strip()
        output_field = str(item.get("output_field") or "").strip()
        if not response_path or not output_field:
            raise ValueError("response_field_mappings_invalid")
        cardinality = str(item.get("cardinality") or "SCALAR").strip().upper()
        if cardinality not in ALLOWED_ENRICHED_FIELD_CARDINALITIES:
            raise ValueError("response_field_mappings_invalid")
        items.append(
            {
                "response_path": response_path,
                "output_field": output_field,
                "data_type": str(item.get("data_type") or "String").strip() or "String",
                "cardinality": cardinality,
            }
        )
    if not items:
        raise ValueError("response_field_mappings_invalid")
    return items


def normalize_request_key_bindings(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("request_key_bindings_invalid")
    return {
        str(key).strip(): str(config_value).strip()
        for key, config_value in value.items()
        if str(key).strip() and str(config_value).strip()
    }


def parse_json_list(value: str | None) -> list[object]:
    try:
        payload = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def parse_json_object(value: str | None) -> dict[str, object]:
    try:
        payload = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def create_integration_enrichment_step(
    db: Session,
    *,
    definition: IntegrationDefinition,
    payload: dict[str, object],
    user: User,
) -> IntegrationEnrichmentStep:
    source_schema_document_id = str(payload["source_schema_document_id"])
    response_schema_document_id = str(payload["response_schema_document_id"])
    source_document = db.get(IntegrationSchemaDocument, source_schema_document_id)
    response_document = db.get(IntegrationSchemaDocument, response_schema_document_id)
    if not schema_document_belongs_to_definition(source_document, definition.id):
        raise ValueError("source_schema_document_invalid")
    if not schema_document_belongs_to_definition(response_document, definition.id):
        raise ValueError("response_schema_document_invalid")

    step_type = str(payload.get("step_type") or "SINGLE").strip().upper()
    if step_type not in ALLOWED_ENRICHMENT_STEP_TYPES:
        raise ValueError("step_type_invalid")
    on_empty_response = str(payload.get("on_empty_response") or "FAIL").strip().upper()
    on_error = str(payload.get("on_error") or "FAIL").strip().upper()
    if on_empty_response not in ALLOWED_ENRICHMENT_POLICIES:
        raise ValueError("on_empty_response_invalid")
    if on_error not in ALLOWED_ENRICHMENT_POLICIES:
        raise ValueError("on_error_invalid")

    key_source_fields = normalize_string_list(payload.get("key_source_fields"))
    for source_path in key_source_fields:
        if not schema_path_exists(db, schema_document_id=source_schema_document_id, path=source_path):
            raise ValueError("key_source_field_invalid")

    response_field_mappings = normalize_response_field_mappings(payload.get("response_field_mappings"))
    for mapping in response_field_mappings:
        if not schema_path_exists(
            db,
            schema_document_id=response_schema_document_id,
            path=str(mapping["response_path"]),
        ):
            raise ValueError("response_path_invalid")

    step = IntegrationEnrichmentStep(
        definition_id=definition.id,
        source_schema_document_id=source_schema_document_id,
        response_schema_document_id=response_schema_document_id,
        endpoint_id=str(payload.get("endpoint_id") or "").strip() or None,
        name=str(payload["name"]).strip(),
        description=str(payload.get("description") or "").strip(),
        step_type=step_type,
        key_template=str(payload.get("key_template") or "").strip(),
        key_source_fields_json=json.dumps(key_source_fields, sort_keys=True),
        response_field_mappings_json=json.dumps(response_field_mappings, sort_keys=True),
        loop_source_path=str(payload.get("loop_source_path") or "").strip(),
        loop_filter_expression=str(payload.get("loop_filter_expression") or "").strip(),
        on_empty_response=on_empty_response,
        on_error=on_error,
        sequence_index=int(payload.get("sequence_index") or 0),
        status="ACTIVE",
        created_by=user.email,
    )
    db.add(step)
    db.flush()
    for mapping in response_field_mappings:
        db.add(
            IntegrationEnrichedField(
                definition_id=definition.id,
                enrichment_step_id=step.id,
                enrichment_substep_id=None,
                name=str(mapping["output_field"]),
                data_type=str(mapping["data_type"]),
                cardinality=str(mapping["cardinality"]),
                response_path=str(mapping["response_path"]),
                fallback_policy_json=json.dumps({}, sort_keys=True),
                source_trace_json=json.dumps(
                    {
                        "step_id": step.id,
                        "step_name": step.name,
                        "step_type": step.step_type,
                        "response_schema_document_id": response_schema_document_id,
                    },
                    sort_keys=True,
                ),
                status="ACTIVE",
                created_by=user.email,
            )
        )
    db.commit()
    db.refresh(step)
    return step


def republish_step_enriched_fields(
    db: Session,
    *,
    step: IntegrationEnrichmentStep,
    response_schema_document_id: str,
    response_field_mappings: list[dict[str, object]],
    user: User,
) -> None:
    existing_fields = (
        db.query(IntegrationEnrichedField)
        .filter(
            IntegrationEnrichedField.enrichment_step_id == step.id,
            IntegrationEnrichedField.enrichment_substep_id.is_(None),
        )
        .all()
    )
    for field in existing_fields:
        field.status = "RETIRED"
    for mapping in response_field_mappings:
        db.add(
            IntegrationEnrichedField(
                definition_id=step.definition_id,
                enrichment_step_id=step.id,
                enrichment_substep_id=None,
                name=str(mapping["output_field"]),
                data_type=str(mapping["data_type"]),
                cardinality=str(mapping["cardinality"]),
                response_path=str(mapping["response_path"]),
                fallback_policy_json=json.dumps({}, sort_keys=True),
                source_trace_json=json.dumps(
                    {
                        "step_id": step.id,
                        "step_name": step.name,
                        "step_type": step.step_type,
                        "response_schema_document_id": response_schema_document_id,
                    },
                    sort_keys=True,
                ),
                status="ACTIVE",
                created_by=user.email,
            )
        )


def update_integration_enrichment_step(
    db: Session,
    *,
    step: IntegrationEnrichmentStep,
    payload: dict[str, object],
    user: User,
) -> IntegrationEnrichmentStep:
    response_schema_document_id = str(payload["response_schema_document_id"])
    source_schema_document_id = str(payload["source_schema_document_id"])
    source_document = db.get(IntegrationSchemaDocument, source_schema_document_id)
    response_document = db.get(IntegrationSchemaDocument, response_schema_document_id)
    if not schema_document_belongs_to_definition(source_document, step.definition_id):
        raise ValueError("source_schema_document_invalid")
    if not schema_document_belongs_to_definition(response_document, step.definition_id):
        raise ValueError("response_schema_document_invalid")

    step_type = str(payload.get("step_type") or "SINGLE").strip().upper()
    if step_type not in ALLOWED_ENRICHMENT_STEP_TYPES:
        raise ValueError("step_type_invalid")
    on_empty_response = str(payload.get("on_empty_response") or "FAIL").strip().upper()
    on_error = str(payload.get("on_error") or "FAIL").strip().upper()
    if on_empty_response not in ALLOWED_ENRICHMENT_POLICIES:
        raise ValueError("on_empty_response_invalid")
    if on_error not in ALLOWED_ENRICHMENT_POLICIES:
        raise ValueError("on_error_invalid")

    key_source_fields = normalize_string_list(payload.get("key_source_fields"))
    for source_path in key_source_fields:
        if not schema_path_exists(db, schema_document_id=source_schema_document_id, path=source_path):
            raise ValueError("key_source_field_invalid")

    response_field_mappings = normalize_response_field_mappings(payload.get("response_field_mappings"))
    for mapping in response_field_mappings:
        if not schema_path_exists(
            db,
            schema_document_id=response_schema_document_id,
            path=str(mapping["response_path"]),
        ):
            raise ValueError("response_path_invalid")

    step.source_schema_document_id = source_schema_document_id
    step.response_schema_document_id = response_schema_document_id
    step.endpoint_id = str(payload.get("endpoint_id") or "").strip() or None
    step.name = str(payload["name"]).strip()
    step.description = str(payload.get("description") or "").strip()
    step.step_type = step_type
    step.key_template = str(payload.get("key_template") or "").strip()
    step.key_source_fields_json = json.dumps(key_source_fields, sort_keys=True)
    step.response_field_mappings_json = json.dumps(response_field_mappings, sort_keys=True)
    step.loop_source_path = str(payload.get("loop_source_path") or "").strip()
    step.loop_filter_expression = str(payload.get("loop_filter_expression") or "").strip()
    step.on_empty_response = on_empty_response
    step.on_error = on_error
    step.sequence_index = int(payload.get("sequence_index") or 0)
    step.status = "ACTIVE"
    republish_step_enriched_fields(
        db,
        step=step,
        response_schema_document_id=response_schema_document_id,
        response_field_mappings=response_field_mappings,
        user=user,
    )
    db.commit()
    db.refresh(step)
    return step


def reorder_integration_enrichment_steps(
    db: Session,
    *,
    definition_id: str,
    items: list[dict[str, object]],
) -> list[IntegrationEnrichmentStep]:
    if not items:
        raise ValueError("reorder_items_invalid")
    steps_by_id = {
        step.id: step
        for step in db.query(IntegrationEnrichmentStep)
        .filter(
            IntegrationEnrichmentStep.definition_id == definition_id,
            IntegrationEnrichmentStep.status == "ACTIVE",
        )
        .all()
    }
    for item in items:
        step_id = str(item.get("id") or "").strip()
        if step_id not in steps_by_id:
            raise ValueError("reorder_step_invalid")
        steps_by_id[step_id].sequence_index = int(item.get("sequence_index") or 0)
    db.commit()
    return (
        db.query(IntegrationEnrichmentStep)
        .filter(
            IntegrationEnrichmentStep.definition_id == definition_id,
            IntegrationEnrichmentStep.status == "ACTIVE",
        )
        .order_by(IntegrationEnrichmentStep.sequence_index, IntegrationEnrichmentStep.created_at)
        .all()
    )


def retire_integration_enrichment_step(db: Session, *, step: IntegrationEnrichmentStep) -> dict[str, object]:
    fields = (
        db.query(IntegrationEnrichedField)
        .filter(
            IntegrationEnrichedField.enrichment_step_id == step.id,
            IntegrationEnrichedField.status == "ACTIVE",
        )
        .all()
    )
    substeps = (
        db.query(IntegrationEnrichmentSubStep)
        .filter(
            IntegrationEnrichmentSubStep.enrichment_step_id == step.id,
            IntegrationEnrichmentSubStep.status == "ACTIVE",
        )
        .all()
    )
    step.status = "RETIRED"
    for substep in substeps:
        substep.status = "RETIRED"
    for field in fields:
        field.status = "RETIRED"
    db.commit()
    return {
        "retired": True,
        "id": step.id,
        "definition_id": step.definition_id,
        "impact": {
            "substeps_retired": len(substeps),
            "enriched_fields_retired": len(fields),
        },
    }


def create_integration_enrichment_substep(
    db: Session,
    *,
    step: IntegrationEnrichmentStep,
    payload: dict[str, object],
    user: User,
) -> IntegrationEnrichmentSubStep:
    response_schema_document_id = str(payload["response_schema_document_id"])
    response_document = db.get(IntegrationSchemaDocument, response_schema_document_id)
    if not schema_document_belongs_to_definition(response_document, step.definition_id):
        raise ValueError("response_schema_document_invalid")

    request_key_bindings = normalize_request_key_bindings(payload.get("request_key_bindings"))
    for source_path in request_key_bindings.values():
        if not schema_path_exists(db, schema_document_id=step.source_schema_document_id, path=source_path):
            raise ValueError("request_key_binding_path_invalid")

    response_field_mappings = normalize_response_field_mappings(payload.get("response_field_mappings"))
    for mapping in response_field_mappings:
        if not schema_path_exists(
            db,
            schema_document_id=response_schema_document_id,
            path=str(mapping["response_path"]),
        ):
            raise ValueError("response_path_invalid")

    substep = IntegrationEnrichmentSubStep(
        definition_id=step.definition_id,
        enrichment_step_id=step.id,
        endpoint_id=str(payload.get("endpoint_id") or "").strip() or None,
        name=str(payload["name"]).strip(),
        request_path_template=str(payload.get("request_path_template") or "").strip(),
        request_key_bindings_json=json.dumps(request_key_bindings, sort_keys=True),
        response_schema_document_id=response_schema_document_id,
        response_field_mappings_json=json.dumps(response_field_mappings, sort_keys=True),
        sequence_index=int(payload.get("sequence_index") or 0),
        status="ACTIVE",
        created_by=user.email,
    )
    db.add(substep)
    db.flush()
    for mapping in response_field_mappings:
        db.add(
            IntegrationEnrichedField(
                definition_id=step.definition_id,
                enrichment_step_id=step.id,
                enrichment_substep_id=substep.id,
                name=str(mapping["output_field"]),
                data_type=str(mapping["data_type"]),
                cardinality=str(mapping["cardinality"]),
                response_path=str(mapping["response_path"]),
                fallback_policy_json=json.dumps({}, sort_keys=True),
                source_trace_json=json.dumps(
                    {
                        "step_id": step.id,
                        "step_name": step.name,
                        "substep_id": substep.id,
                        "substep_name": substep.name,
                        "response_schema_document_id": response_schema_document_id,
                    },
                    sort_keys=True,
                ),
                status="ACTIVE",
                created_by=user.email,
            )
        )
    db.commit()
    db.refresh(substep)
    return substep


def serialize_integration_enrichment_step(step: IntegrationEnrichmentStep) -> dict[str, object]:
    return {
        "id": step.id,
        "definition_id": step.definition_id,
        "source_schema_document_id": step.source_schema_document_id,
        "response_schema_document_id": step.response_schema_document_id,
        "endpoint_id": step.endpoint_id,
        "name": step.name,
        "description": step.description,
        "step_type": step.step_type,
        "key_template": step.key_template,
        "key_source_fields": parse_json_list(step.key_source_fields_json),
        "response_field_mappings": parse_json_list(step.response_field_mappings_json),
        "loop_source_path": step.loop_source_path,
        "loop_filter_expression": step.loop_filter_expression,
        "on_empty_response": step.on_empty_response,
        "on_error": step.on_error,
        "sequence_index": step.sequence_index,
        "status": step.status,
        "created_by": step.created_by,
        "created_at": step.created_at.isoformat() if step.created_at else None,
        "updated_at": step.updated_at.isoformat() if step.updated_at else None,
    }


def serialize_integration_enrichment_substep(substep: IntegrationEnrichmentSubStep) -> dict[str, object]:
    return {
        "id": substep.id,
        "definition_id": substep.definition_id,
        "enrichment_step_id": substep.enrichment_step_id,
        "endpoint_id": substep.endpoint_id,
        "name": substep.name,
        "request_path_template": substep.request_path_template,
        "request_key_bindings": parse_json_object(substep.request_key_bindings_json),
        "response_schema_document_id": substep.response_schema_document_id,
        "response_field_mappings": parse_json_list(substep.response_field_mappings_json),
        "sequence_index": substep.sequence_index,
        "status": substep.status,
        "created_by": substep.created_by,
        "created_at": substep.created_at.isoformat() if substep.created_at else None,
        "updated_at": substep.updated_at.isoformat() if substep.updated_at else None,
    }


def serialize_integration_enriched_field(field: IntegrationEnrichedField) -> dict[str, object]:
    return {
        "id": field.id,
        "definition_id": field.definition_id,
        "enrichment_step_id": field.enrichment_step_id,
        "enrichment_substep_id": field.enrichment_substep_id,
        "name": field.name,
        "data_type": field.data_type,
        "cardinality": field.cardinality,
        "response_path": field.response_path,
        "fallback_policy": parse_json_object(field.fallback_policy_json),
        "source_trace": parse_json_object(field.source_trace_json),
        "status": field.status,
        "created_by": field.created_by,
        "created_at": field.created_at.isoformat() if field.created_at else None,
        "updated_at": field.updated_at.isoformat() if field.updated_at else None,
    }


def validate_enrichment_step(db: Session, step: IntegrationEnrichmentStep) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []
    if db.get(IntegrationSchemaDocument, step.source_schema_document_id) is None:
        blockers.append("Source schema document is missing.")
    if db.get(IntegrationSchemaDocument, step.response_schema_document_id) is None:
        blockers.append("Response schema document is missing.")
    fields = (
        db.query(IntegrationEnrichedField)
        .filter(
            IntegrationEnrichedField.enrichment_step_id == step.id,
            IntegrationEnrichedField.status == "ACTIVE",
        )
        .all()
    )
    if not fields:
        blockers.append("At least one enriched field must be published.")
    return {
        "definition_id": step.definition_id,
        "enrichment_step_id": step.id,
        "ready": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "enriched_field_count": len(fields),
    }


def build_enrichment_readiness(db: Session, definition_id: str) -> dict[str, object]:
    steps = (
        db.query(IntegrationEnrichmentStep)
        .filter(
            IntegrationEnrichmentStep.definition_id == definition_id,
            IntegrationEnrichmentStep.status == "ACTIVE",
        )
        .order_by(IntegrationEnrichmentStep.sequence_index, IntegrationEnrichmentStep.created_at)
        .all()
    )
    fields = (
        db.query(IntegrationEnrichedField)
        .filter(
            IntegrationEnrichedField.definition_id == definition_id,
            IntegrationEnrichedField.status == "ACTIVE",
        )
        .all()
    )
    validations = [validate_enrichment_step(db, step) for step in steps]
    blockers = [blocker for validation in validations for blocker in validation["blockers"]]
    warnings = [warning for validation in validations for warning in validation["warnings"]]
    return {
        "definition_id": definition_id,
        "ready": bool(steps) and not blockers,
        "step_count": len(steps),
        "enriched_field_count": len(fields),
        "blockers": blockers,
        "warnings": warnings,
        "steps": validations,
    }
