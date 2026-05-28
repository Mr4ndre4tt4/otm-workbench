from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import (
    Artifact,
    IntegrationDefinition,
    IntegrationEnrichedField,
    IntegrationEnrichmentStep,
    IntegrationEnrichmentSubStep,
    IntegrationJoinRule,
    IntegrationLookupDefinition,
    IntegrationLoopDefinition,
    IntegrationMapping,
    IntegrationResponseHandler,
    IntegrationSchemaDocument,
    Job,
    utcnow,
)
from otm_workbench.modules.integration_mapping.enrichment import parse_json_list
from otm_workbench.modules.integration_mapping.mappings import parse_transform_config
from otm_workbench.modules.rates.exports import file_sha256, utc_timestamp
from otm_workbench.platform.jobs import audit_job, dumps_limited_json_object, emit_job_event


SOURCE_MODULE = "integration_mapping"
SPEC_JOB_TYPE = "INTEGRATION_MAPPING_GENERATE_SPEC"
SPEC_SECTIONS = [
    "Identification",
    "Schema Documents",
    "Mappings",
    "Loops",
    "Joins",
    "Enrichment Pipeline",
    "Lookups",
    "Response Handling",
    "Synthetic Test Cases",
]


def _rows_or_empty(rows: list[str]) -> str:
    if not rows:
        return "- None registered for this definition."
    return "\n".join(rows)


def _format_transform_config(mapping: IntegrationMapping) -> str:
    config = parse_transform_config(mapping.transform_config_json)
    if not config:
        return ""
    fragments = [f"{key}={value}" for key, value in sorted(config.items())]
    config_text = "; ".join(fragments)
    return f" config `{config_text}`"


def _build_markdown(
    *,
    definition: IntegrationDefinition,
    schema_documents: list[IntegrationSchemaDocument],
    mappings: list[IntegrationMapping],
    loops: list[IntegrationLoopDefinition],
    joins: list[IntegrationJoinRule],
    enrichment_steps: list[IntegrationEnrichmentStep],
    enrichment_substeps: list[IntegrationEnrichmentSubStep],
    enriched_fields: list[IntegrationEnrichedField],
    lookups: list[IntegrationLookupDefinition],
    response_handlers: list[IntegrationResponseHandler],
    validation: dict[str, object],
) -> str:
    document_rows = [
        f"- `{document.id}`: format `{document.payload_format}`, root `{document.root_name}`, "
        f"{document.node_count} schema nodes, status `{document.status}`."
        for document in schema_documents
    ]
    mapping_rows = [
        f"- `{mapping.sequence_index}` `{mapping.transform_type}`: `{mapping.source_path}` -> "
        f"`{mapping.target_path}`{_format_transform_config(mapping)}."
        for mapping in mappings
    ]
    loop_rows = [
        f"- `{loop.sequence_index}`: `{loop.source_collection_path}` -> `{loop.target_collection_path}`."
        for loop in loops
    ]
    join_rows = [
        f"- `{join_rule.sequence_index}` `{join_rule.operator}`: `{join_rule.left_path}` to `{join_rule.right_path}`."
        for join_rule in joins
    ]
    enrichment_rows = enrichment_markdown_rows(
        enrichment_steps=enrichment_steps,
        enrichment_substeps=enrichment_substeps,
        enriched_fields=enriched_fields,
    )
    lookup_rows = [
        f"- `{lookup.sequence_index}` `{lookup.lookup_type}`: `{lookup.input_path}` -> `{lookup.output_path}`."
        for lookup in lookups
    ]
    response_handler_rows = [
        f"- `{handler.sequence_index}` `{handler.outcome}`: `{handler.response_path}` "
        f"`{handler.success_condition}` `{handler.expected_value}`."
        for handler in response_handlers
    ]

    return "\n".join(
        [
            "# Integration Mapping Spec",
            "",
            "## Identification",
            f"- Definition ID: `{definition.id}`",
            f"- Code: `{definition.code}`",
            f"- Source system: `{definition.source_system}`",
            f"- Target system: `{definition.target_system}`",
            f"- Source format: `{definition.source_format}`",
            f"- Target format: `{definition.target_format}`",
            f"- Status: `{definition.status}`",
            f"- Validation: `{validation['issue_count']}` open issue(s).",
            "",
            "## Schema Documents",
            _rows_or_empty(document_rows),
            "",
            "## Mappings",
            _rows_or_empty(mapping_rows),
            "",
            "## Loops",
            _rows_or_empty(loop_rows),
            "",
            "## Joins",
            _rows_or_empty(join_rows),
            "",
            "## Enrichment Pipeline",
            _rows_or_empty(enrichment_rows),
            "- External enrichment calls are not executed by this spec generator.",
            "- Published enriched fields are metadata contracts for downstream mappings and preview provenance.",
            "",
            "## Lookups",
            _rows_or_empty(lookup_rows),
            "",
            "## Response Handling",
            _rows_or_empty(response_handler_rows),
            "- Runtime external calls are not executed by this spec generator.",
            "",
            "## Synthetic Test Cases",
            "- Create a metadata-only happy path with one generated source envelope and one target document.",
            "- Verify required source paths exist before transformation.",
            "- Verify mock lookups resolve with non-sensitive demo values.",
            "- Store scenario payloads separately; this markdown intentionally excludes raw XML and JSON samples.",
            "",
        ]
    )


def enrichment_markdown_rows(
    *,
    enrichment_steps: list[IntegrationEnrichmentStep],
    enrichment_substeps: list[IntegrationEnrichmentSubStep],
    enriched_fields: list[IntegrationEnrichedField],
) -> list[str]:
    fields_by_step: dict[tuple[str, str | None], list[IntegrationEnrichedField]] = {}
    for field in enriched_fields:
        fields_by_step.setdefault((field.enrichment_step_id, field.enrichment_substep_id), []).append(field)

    rows: list[str] = []
    for step in enrichment_steps:
        mappings = parse_json_list(step.response_field_mappings_json)
        mapping_text = _format_enrichment_mapping_text(mappings)
        key_fields = ", ".join(f"`{field}`" for field in parse_json_list(step.key_source_fields_json))
        fields = fields_by_step.get((step.id, None), [])
        field_text = _format_published_field_text(fields)
        rows.append(
            f"- `{step.sequence_index}` `{step.step_type}`: `{step.name}`, key {key_fields or '`n/a`'}, "
            f"response {mapping_text}, published {field_text}."
        )
    for substep in enrichment_substeps:
        mappings = parse_json_list(substep.response_field_mappings_json)
        mapping_text = _format_enrichment_mapping_text(mappings)
        fields = fields_by_step.get((substep.enrichment_step_id, substep.id), [])
        field_text = _format_published_field_text(fields)
        rows.append(
            f"- `{substep.sequence_index}` `SUBSTEP`: `{substep.name}`, request `{substep.request_path_template}`, "
            f"response {mapping_text}, published {field_text}."
        )
    return rows


def _format_enrichment_mapping_text(mappings: list[object]) -> str:
    fragments: list[str] = []
    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        output_field = str(mapping.get("output_field") or "").strip()
        response_path = str(mapping.get("response_path") or "").strip()
        if output_field and response_path:
            fragments.append(f"`{output_field}` <- `{response_path}`")
    return ", ".join(fragments) if fragments else "`n/a`"


def _format_published_field_text(fields: list[IntegrationEnrichedField]) -> str:
    if not fields:
        return "`none`"
    return ", ".join(f"`{field.name}`" for field in fields)


def create_spec_artifact(
    db: Session,
    *,
    definition: IntegrationDefinition,
    artifact_root: Path,
    markdown: str,
) -> Artifact:
    export_dir = artifact_root / "integration_mapping" / definition.id / "specs" / utc_timestamp()
    export_dir.mkdir(parents=True, exist_ok=True)
    file_name = "integration_mapping_spec.md"
    file_path = export_dir / file_name
    file_path.write_text(markdown, encoding="utf-8")
    digest, size = file_sha256(file_path)
    artifact = Artifact(
        project_id=definition.project_id,
        profile_id=definition.profile_id,
        environment_id=definition.environment_id,
        domain_name=definition.domain_name,
        visibility="PROJECT",
        source_module=SOURCE_MODULE,
        artifact_type="integration_markdown_spec",
        file_path=str(file_path),
        file_name=file_name,
        content_type="text/markdown",
        sha256=digest,
        size_bytes=size,
        sensitivity_level="internal",
    )
    db.add(artifact)
    db.flush()
    return artifact


def record_completed_spec_job(
    db: Session,
    *,
    definition: IntegrationDefinition,
    artifact: Artifact,
    result_payload: dict[str, object],
    created_by: str,
) -> Job:
    job = Job(
        job_type=SPEC_JOB_TYPE,
        source_module=SOURCE_MODULE,
        status="PENDING",
        progress=0,
        message="Job created.",
        input_json=dumps_limited_json_object({"definition_id": definition.id}, label="input"),
        result_json="{}",
        error_details_json="{}",
        created_by=created_by,
    )
    db.add(job)
    db.flush()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_CREATED",
        status_before=None,
        status_after="PENDING",
        message="Job created.",
        created_by=created_by,
    )
    audit_job(db, actor=created_by, action="job.create", job=job)
    db.flush()

    job.status = "RUNNING"
    job.progress = 1
    job.message = "Job started."
    job.started_at = utcnow()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_STARTED",
        status_before="PENDING",
        status_after="RUNNING",
        message="Job started.",
        created_by=created_by,
    )
    db.flush()

    job.status = "SUCCEEDED"
    job.progress = 100
    job.message = "Integration Mapping markdown spec generated."
    job.result_json = dumps_limited_json_object(
        {
            "definition_id": definition.id,
            "artifact_id": artifact.id,
            "spec": result_payload["spec"],
            "validation": result_payload["validation"],
        },
        label="result",
    )
    job.finished_at = utcnow()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_SUCCEEDED",
        status_before="RUNNING",
        status_after="SUCCEEDED",
        message="Integration Mapping markdown spec generated.",
        created_by=created_by,
        payload={"artifact_id": artifact.id},
    )
    audit_job(db, actor=created_by, action="job.succeed", job=job, metadata={"artifact_id": artifact.id})
    db.flush()
    return job


def generate_integration_markdown_spec(
    db: Session,
    *,
    definition: IntegrationDefinition,
    validation: dict[str, object],
    artifact_root: Path,
    created_by: str,
) -> dict[str, object]:
    schema_documents = (
        db.query(IntegrationSchemaDocument)
        .filter(IntegrationSchemaDocument.definition_id == definition.id)
        .order_by(IntegrationSchemaDocument.created_at, IntegrationSchemaDocument.id)
        .all()
    )
    mappings = (
        db.query(IntegrationMapping)
        .filter(IntegrationMapping.definition_id == definition.id)
        .order_by(IntegrationMapping.sequence_index, IntegrationMapping.created_at)
        .all()
    )
    loops = (
        db.query(IntegrationLoopDefinition)
        .filter(IntegrationLoopDefinition.definition_id == definition.id)
        .order_by(IntegrationLoopDefinition.sequence_index, IntegrationLoopDefinition.created_at)
        .all()
    )
    joins = (
        db.query(IntegrationJoinRule)
        .filter(IntegrationJoinRule.definition_id == definition.id)
        .order_by(IntegrationJoinRule.sequence_index, IntegrationJoinRule.created_at)
        .all()
    )
    enrichment_steps = (
        db.query(IntegrationEnrichmentStep)
        .filter(
            IntegrationEnrichmentStep.definition_id == definition.id,
            IntegrationEnrichmentStep.status == "ACTIVE",
        )
        .order_by(IntegrationEnrichmentStep.sequence_index, IntegrationEnrichmentStep.created_at)
        .all()
    )
    enrichment_substeps = (
        db.query(IntegrationEnrichmentSubStep)
        .filter(
            IntegrationEnrichmentSubStep.definition_id == definition.id,
            IntegrationEnrichmentSubStep.status == "ACTIVE",
        )
        .order_by(IntegrationEnrichmentSubStep.sequence_index, IntegrationEnrichmentSubStep.created_at)
        .all()
    )
    enriched_fields = (
        db.query(IntegrationEnrichedField)
        .filter(
            IntegrationEnrichedField.definition_id == definition.id,
            IntegrationEnrichedField.status == "ACTIVE",
        )
        .order_by(IntegrationEnrichedField.created_at, IntegrationEnrichedField.name)
        .all()
    )
    lookups = (
        db.query(IntegrationLookupDefinition)
        .filter(IntegrationLookupDefinition.definition_id == definition.id)
        .order_by(IntegrationLookupDefinition.sequence_index, IntegrationLookupDefinition.created_at)
        .all()
    )
    response_handlers = (
        db.query(IntegrationResponseHandler)
        .filter(IntegrationResponseHandler.definition_id == definition.id)
        .order_by(IntegrationResponseHandler.sequence_index, IntegrationResponseHandler.created_at)
        .all()
    )
    markdown = _build_markdown(
        definition=definition,
        schema_documents=schema_documents,
        mappings=mappings,
        loops=loops,
        joins=joins,
        enrichment_steps=enrichment_steps,
        enrichment_substeps=enrichment_substeps,
        enriched_fields=enriched_fields,
        lookups=lookups,
        response_handlers=response_handlers,
        validation=validation,
    )
    artifact = create_spec_artifact(db, definition=definition, artifact_root=artifact_root, markdown=markdown)
    result_payload = {
        "definition_id": definition.id,
        "spec": {"format": "MARKDOWN", "sections": SPEC_SECTIONS},
        "validation": validation,
    }
    job = record_completed_spec_job(
        db,
        definition=definition,
        artifact=artifact,
        result_payload=result_payload,
        created_by=created_by,
    )
    db.commit()
    db.refresh(job)
    db.refresh(artifact)
    return {
        "definition_id": definition.id,
        "status": job.status,
        "job_id": job.id,
        "artifact_id": artifact.id,
        "spec": result_payload["spec"],
        "validation": validation,
    }
