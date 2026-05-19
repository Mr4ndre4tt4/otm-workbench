import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.catalog.services import reference_options_payload, serialize_table_definition
from otm_workbench.models import (
    Artifact,
    AuditLog,
    Evidence,
    RateBatch,
    RateBatchIssue,
    RateBatchTable,
    ReferenceObject,
    User,
)
from otm_workbench.modules.rates.batches import (
    add_rate_batch_tables,
    create_rate_batch,
    get_batch_table_rows,
)
from otm_workbench.modules.rates.approval import approve_rate_batch, get_rate_batch_readiness
from otm_workbench.modules.rates.csv_preview import build_otm_csv_preview
from otm_workbench.modules.rates.dictionary import (
    RATES_LOAD_SEQUENCE,
    load_table_definition,
    validate_load_sequence,
)
from otm_workbench.modules.rates.exports import (
    file_sha256,
    generate_rates_csv_export,
    latest_batch_export_bundle,
    list_batch_export_artifacts,
    list_batch_export_evidence,
)
from otm_workbench.modules.rates.scenarios import get_rate_scenario, list_rate_scenarios
from otm_workbench.modules.rates.validation import validate_rate_batch

router = APIRouter(prefix="/api/v1/modules/rates", tags=["rates"])


class LoadSequenceRequest(BaseModel):
    catalog_macro_object_code: str | None = None
    tables: list[str] = RATES_LOAD_SEQUENCE


class RateOfferingDuplicateCheckRequest(BaseModel):
    catalog_macro_object_code: str | None = None
    servprov_gid: str
    transport_mode_gid: str
    rate_service_gid: str
    equipment_group_profile_gid: str
    currency_gid: str


class CsvPreviewRequest(BaseModel):
    catalog_macro_object_code: str | None = None
    table_name: str
    columns: list[str]
    rows: list[dict[str, object]]


class CreateRateBatchRequest(BaseModel):
    scenario_code: str
    name: str
    domain_name: str
    project_id: str | None = None
    environment_id: str | None = None
    profile_id: str | None = None
    description: str = ""
    source_type: str = "api"


class RateBatchTablePayload(BaseModel):
    table_name: str
    rows: list[dict[str, object]] = []


class AddRateBatchTablesRequest(BaseModel):
    tables: list[RateBatchTablePayload]


class ApproveRateBatchRequest(BaseModel):
    approval_note: str = ""


def serialize_rate_batch(batch: RateBatch) -> dict[str, object]:
    scenario = get_rate_scenario(batch.scenario_code)
    return {
        "id": batch.id,
        "project_id": batch.project_id,
        "environment_id": batch.environment_id,
        "profile_id": batch.profile_id,
        "scenario_code": batch.scenario_code,
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
        "name": batch.name,
        "description": batch.description,
        "status": batch.status,
        "source_type": batch.source_type,
        "domain_name": batch.domain_name,
        "created_by": batch.created_by,
        "summary_json": batch.summary_json,
    }


def serialize_rate_batch_table(table: RateBatchTable) -> dict[str, object]:
    return {
        "id": table.id,
        "batch_id": table.batch_id,
        "table_name": table.table_name,
        "sequence_index": table.sequence_index,
        "requirement_level": table.requirement_level,
        "row_count": table.row_count,
        "status": table.status,
    }


def serialize_rate_batch_issue(issue: RateBatchIssue) -> dict[str, object]:
    return {
        "id": issue.id,
        "batch_id": issue.batch_id,
        "batch_table_id": issue.batch_table_id,
        "batch_row_id": issue.batch_row_id,
        "severity": issue.severity,
        "issue_code": issue.issue_code,
        "table_name": issue.table_name,
        "column_name": issue.column_name,
        "message": issue.message,
        "details_json": issue.details_json,
    }


def serialize_artifact(artifact: Artifact) -> dict[str, object]:
    return {
        "id": artifact.id,
        "artifact_type": artifact.artifact_type,
        "file_name": artifact.file_name,
        "content_type": artifact.content_type,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "sensitivity_level": artifact.sensitivity_level,
    }


def serialize_evidence(evidence: Evidence) -> dict[str, object]:
    return {
        "id": evidence.id,
        "evidence_type": evidence.evidence_type,
        "status": evidence.status,
        "summary_json": evidence.summary_json,
        "artifact_id": evidence.artifact_id,
        "manifest_id": evidence.manifest_id,
        "client_safe": evidence.client_safe,
        "sensitivity_level": evidence.sensitivity_level,
    }


@router.get("/templates")
def list_rates_templates(
    catalog_macro_object_code: str | None = None,
    user: User = Depends(require_user),
):
    items = [
        {
            "code": scenario.code,
            "name": scenario.name,
            "description": scenario.description,
            "catalog_macro_object_code": scenario.catalog_macro_object_code,
            "catalog_load_plan_path": scenario.catalog_load_plan_path,
            "tables": scenario.tables,
            "required_tables": scenario.required_tables,
            "optional_tables": scenario.optional_tables,
            "pre_existing_tables": scenario.pre_existing_tables,
        }
        for scenario in list_rate_scenarios()
    ]
    if catalog_macro_object_code:
        items = [
            item
            for item in items
            if item["catalog_macro_object_code"] == catalog_macro_object_code
        ]
    return PageResponse(items=items, total=len(items))


@router.post("/batches")
def create_rates_batch(
    payload: CreateRateBatchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    try:
        batch = create_rate_batch(
            db,
            scenario_code=payload.scenario_code,
            name=payload.name,
            domain_name=payload.domain_name,
            project_id=payload.project_id,
            environment_id=payload.environment_id,
            profile_id=payload.profile_id,
            description=payload.description,
            source_type=payload.source_type,
            created_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_rate_batch(batch)


@router.get("/batches")
def list_rates_batches(
    catalog_macro_object_code: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batches = db.query(RateBatch).order_by(RateBatch.created_at.desc()).all()
    items = [serialize_rate_batch(batch) for batch in batches]
    if catalog_macro_object_code:
        items = [
            item
            for item in items
            if item["catalog_macro_object_code"] == catalog_macro_object_code
        ]
    return PageResponse(items=items, total=len(items))


@router.get("/batches/{batch_id}")
def get_rates_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    tables = (
        db.query(RateBatchTable)
        .filter(RateBatchTable.batch_id == batch.id)
        .order_by(RateBatchTable.sequence_index)
        .all()
    )
    payload = serialize_rate_batch(batch)
    payload["tables"] = [serialize_rate_batch_table(table) for table in tables]
    return payload


@router.get("/batches/{batch_id}/readiness")
def get_rates_batch_readiness(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    scenario = get_rate_scenario(batch.scenario_code)
    payload = get_rate_batch_readiness(db, batch).to_dict()
    payload["catalog_macro_object_code"] = scenario.catalog_macro_object_code
    payload["catalog_load_plan_path"] = scenario.catalog_load_plan_path
    return payload


@router.post("/batches/{batch_id}/approve")
def approve_rates_batch(
    batch_id: str,
    payload: ApproveRateBatchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    try:
        return approve_rate_batch(
            db,
            batch=batch,
            approved_by=user.email,
            approval_note=payload.approval_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/batches/{batch_id}/tables")
def add_rates_batch_tables(
    batch_id: str,
    payload: AddRateBatchTablesRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    tables = add_rate_batch_tables(
        db,
        batch=batch,
        tables=[item.model_dump() for item in payload.tables],
    )
    return {
        "batch_id": batch.id,
        "tables": [serialize_rate_batch_table(table) for table in tables],
    }


@router.post("/batches/{batch_id}/validate")
def validate_rates_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    issues = validate_rate_batch(
        db,
        dictionary_root=Path(get_settings().otm_data_dictionary_root),
        batch=batch,
    )
    scenario = get_rate_scenario(batch.scenario_code)
    return {
        "batch_id": batch.id,
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
        "status": batch.status,
        "valid": not any(issue.severity == "ERROR" for issue in issues),
        "issues": [serialize_rate_batch_issue(issue) for issue in issues],
    }


@router.get("/batches/{batch_id}/issues")
def list_rates_batch_issues(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    issues = (
        db.query(RateBatchIssue)
        .filter(RateBatchIssue.batch_id == batch.id)
        .order_by(RateBatchIssue.severity, RateBatchIssue.issue_code)
        .all()
    )
    items = [serialize_rate_batch_issue(issue) for issue in issues]
    scenario = get_rate_scenario(batch.scenario_code)
    return {
        "batch_id": batch.id,
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
        "items": items,
        "total": len(items),
    }


@router.post("/batches/{batch_id}/csv-preview")
def preview_rates_batch_csv(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    batch_tables = (
        db.query(RateBatchTable)
        .filter(RateBatchTable.batch_id == batch.id)
        .order_by(RateBatchTable.sequence_index)
        .all()
    )
    previews = []
    for batch_table in batch_tables:
        rows = get_batch_table_rows(db, batch_table)
        columns = sorted({column for row in rows for column in row})
        content = build_otm_csv_preview(
            Path(get_settings().otm_data_dictionary_root),
            batch_table.table_name,
            columns,
            rows,
        )
        previews.append({"table_name": batch_table.table_name, "content": content})
    batch.status = "EXPORT_PREVIEWED"
    db.commit()
    scenario = get_rate_scenario(batch.scenario_code)
    return {
        "batch_id": batch.id,
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
        "previews": previews,
    }


@router.post("/batches/{batch_id}/export-csv")
def export_rates_batch_csv(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    try:
        result = generate_rates_csv_export(
            db,
            batch=batch,
            dictionary_root=Path(get_settings().otm_data_dictionary_root),
            artifact_root=Path(get_settings().artifact_root),
            generated_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    scenario = get_rate_scenario(batch.scenario_code)
    payload = result.__dict__
    payload["catalog_macro_object_code"] = scenario.catalog_macro_object_code
    payload["catalog_load_plan_path"] = scenario.catalog_load_plan_path
    return payload


@router.get("/batches/{batch_id}/artifacts")
def list_rates_batch_artifacts(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    artifacts = list_batch_export_artifacts(db, batch.id)
    items = [serialize_artifact(artifact) for artifact in artifacts]
    scenario = get_rate_scenario(batch.scenario_code)
    return {
        "batch_id": batch.id,
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
        "items": items,
        "total": len(items),
    }


@router.get("/batches/{batch_id}/exports/latest")
def get_latest_rates_batch_export(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    bundle = latest_batch_export_bundle(db, batch.id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Rates export not found.")
    scenario = get_rate_scenario(batch.scenario_code)
    return {
        "batch_id": batch.id,
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
        "artifact": serialize_artifact(bundle.artifact),
        "evidence": serialize_evidence(bundle.evidence),
        "manifest": json.loads(bundle.manifest.manifest_json or "{}"),
        "download_url": f"/api/v1/modules/rates/batches/{batch.id}/artifacts/{bundle.artifact.id}/download",
    }


@router.get("/batches/{batch_id}/artifacts/{artifact_id}/download")
def download_rates_batch_artifact(
    batch_id: str,
    artifact_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")

    artifacts = list_batch_export_artifacts(db, batch.id)
    artifact = next((item for item in artifacts if item.id == artifact_id), None)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")

    path = Path(artifact.file_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact file not found.")

    actual_sha256, actual_size = file_sha256(path)
    if actual_sha256 != artifact.sha256:
        raise HTTPException(status_code=409, detail="Artifact hash mismatch.")

    db.add(
        AuditLog(
            actor_user_id=user.email,
            action="rates.batch.artifact.download",
            target_type="artifact",
            target_id=artifact.id,
            metadata_json=json.dumps(
                {
                    "artifact_id": artifact.id,
                    "artifact_type": artifact.artifact_type,
                    "batch_id": batch.id,
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


@router.get("/batches/{batch_id}/evidence")
def list_rates_batch_evidence(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    evidence_items = list_batch_export_evidence(db, batch.id)
    items = [serialize_evidence(evidence) for evidence in evidence_items]
    scenario = get_rate_scenario(batch.scenario_code)
    return {
        "batch_id": batch.id,
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
        "items": items,
        "total": len(items),
    }


@router.get("/dictionary/tables")
def list_rates_dictionary_tables(
    catalog_macro_object_code: str | None = None,
    user: User = Depends(require_user),
):
    items = [{"table_name": item} for item in RATES_LOAD_SEQUENCE]
    if catalog_macro_object_code and catalog_macro_object_code != "RATE_RECORD":
        items = []
    return PageResponse(items=items, total=len(items))


@router.get("/dictionary/tables/{table_name}")
def get_rates_dictionary_table(
    table_name: str,
    user: User = Depends(require_user),
):
    definition = load_table_definition(Path(get_settings().otm_data_dictionary_root), table_name)
    payload = serialize_table_definition(definition)
    payload["foreign_keys"] = [item.__dict__ for item in definition.foreign_keys]
    return payload


@router.post("/dictionary/validate-load-sequence")
def validate_rates_load_sequence(
    payload: LoadSequenceRequest,
    user: User = Depends(require_user),
):
    if payload.catalog_macro_object_code and payload.catalog_macro_object_code != "RATE_RECORD":
        return {
            "catalog_macro_object_code": payload.catalog_macro_object_code,
            "valid": False,
            "known_tables": [],
            "missing_tables": [],
            "issues": [
                {
                    "severity": "ERROR",
                    "table_name": payload.tables[0] if payload.tables else None,
                    "parent_table_name": None,
                    "message": "Catalog macro-object is outside the Rates module sequence.",
                }
            ],
        }
    result = validate_load_sequence(Path(get_settings().otm_data_dictionary_root), payload.tables)
    response = {
        "valid": result.valid,
        "known_tables": result.known_tables,
        "missing_tables": result.missing_tables,
        "issues": [item.__dict__ for item in result.issues],
    }
    if payload.catalog_macro_object_code:
        response["catalog_macro_object_code"] = payload.catalog_macro_object_code
    return response


@router.get("/reference/options")
def list_rates_reference_options(
    object_type: str,
    domain_name: str = "OTM1",
    catalog_macro_object_code: str | None = None,
    project_id: str | None = None,
    environment_id: str | None = None,
    profile_id: str | None = None,
    can_view_all_domains: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    payload = reference_options_payload(
        db,
        module_id="rates",
        object_type=object_type,
        domain_name=domain_name,
        project_id=project_id,
        environment_id=environment_id,
        profile_id=profile_id,
        can_view_all_domains=can_view_all_domains,
    )
    if catalog_macro_object_code:
        payload["catalog_macro_object_code"] = catalog_macro_object_code
        if catalog_macro_object_code != "RATE_RECORD":
            payload["items"] = []
    return payload


@router.get("/reference/rate-offerings")
def list_rate_offerings(
    catalog_macro_object_code: str | None = None,
    servprov_gid: str | None = None,
    transport_mode_gid: str | None = None,
    rate_service_gid: str | None = None,
    equipment_group_profile_gid: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(ReferenceObject).filter(ReferenceObject.object_type == "RATE_OFFERING")
    for key, value in {
        "servprov_gid": servprov_gid,
        "transport_mode_gid": transport_mode_gid,
        "rate_service_gid": rate_service_gid,
        "equipment_group_profile_gid": equipment_group_profile_gid,
    }.items():
        if value:
            query = query.filter(ReferenceObject.metadata_json.contains(f'"{key}": "{value}"'))
    objects = query.order_by(ReferenceObject.gid).all()
    items = [
        {
            "gid": item.gid,
            "xid": item.xid,
            "domain_name": item.domain_name,
            "display_name": item.display_name,
            "metadata_json": item.metadata_json,
        }
        for item in objects
    ]
    payload = PageResponse(items=items, total=len(items)).model_dump()
    if catalog_macro_object_code:
        payload["catalog_macro_object_code"] = catalog_macro_object_code
        if catalog_macro_object_code != "RATE_RECORD":
            payload["items"] = []
            payload["total"] = 0
    return payload


@router.post("/reference/rate-offerings/duplicate-check")
def check_rate_offering_duplicate(
    payload: RateOfferingDuplicateCheckRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    candidates = []
    lookup_fields = payload.model_dump(exclude={"catalog_macro_object_code"})
    if payload.catalog_macro_object_code in (None, "RATE_RECORD"):
        for item in db.query(ReferenceObject).filter(ReferenceObject.object_type == "RATE_OFFERING").all():
            metadata = json.loads(item.metadata_json or "{}")
            if all(metadata.get(key) == value for key, value in lookup_fields.items()):
                candidates.append(
                    {
                        "gid": item.gid,
                        "xid": item.xid,
                        "domain_name": item.domain_name,
                        "display_name": item.display_name,
                    }
                )
    response = {
        "severity": "WARNING" if candidates else "INFO",
        "message": (
            "Potential duplicate Rate Offering found."
            if candidates
            else "No duplicate candidate found."
        ),
        "candidates": candidates,
    }
    if payload.catalog_macro_object_code:
        response["catalog_macro_object_code"] = payload.catalog_macro_object_code
    return response


@router.post("/csv/preview")
def preview_rates_csv(
    payload: CsvPreviewRequest,
    user: User = Depends(require_user),
):
    if payload.catalog_macro_object_code and payload.catalog_macro_object_code != "RATE_RECORD":
        raise HTTPException(status_code=400, detail="Catalog macro-object is outside the Rates module sequence.")
    content = build_otm_csv_preview(
        Path(get_settings().otm_data_dictionary_root),
        payload.table_name,
        payload.columns,
        payload.rows,
    )
    response = {"content": content}
    if payload.catalog_macro_object_code:
        response["catalog_macro_object_code"] = payload.catalog_macro_object_code
    return response
