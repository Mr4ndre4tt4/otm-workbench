import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import RateBatch, RateBatchIssue, RateBatchTable, ReferenceObject, User
from otm_workbench.modules.rates.batches import (
    add_rate_batch_tables,
    create_rate_batch,
)
from otm_workbench.modules.rates.csv_preview import build_otm_csv_preview
from otm_workbench.modules.rates.dictionary import (
    RATES_LOAD_SEQUENCE,
    load_table_definition,
    validate_load_sequence,
)
from otm_workbench.modules.rates.scenarios import list_rate_scenarios
from otm_workbench.modules.rates.validation import validate_rate_batch

router = APIRouter(prefix="/api/v1/modules/rates", tags=["rates"])


class LoadSequenceRequest(BaseModel):
    tables: list[str] = RATES_LOAD_SEQUENCE


class RateOfferingDuplicateCheckRequest(BaseModel):
    servprov_gid: str
    transport_mode_gid: str
    rate_service_gid: str
    equipment_group_profile_gid: str
    currency_gid: str


class CsvPreviewRequest(BaseModel):
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


def serialize_rate_batch(batch: RateBatch) -> dict[str, object]:
    return {
        "id": batch.id,
        "project_id": batch.project_id,
        "environment_id": batch.environment_id,
        "profile_id": batch.profile_id,
        "scenario_code": batch.scenario_code,
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


@router.get("/templates")
def list_rates_templates(user: User = Depends(require_user)):
    items = [
        {
            "code": scenario.code,
            "name": scenario.name,
            "description": scenario.description,
            "tables": scenario.tables,
            "required_tables": scenario.required_tables,
            "optional_tables": scenario.optional_tables,
            "pre_existing_tables": scenario.pre_existing_tables,
        }
        for scenario in list_rate_scenarios()
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
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batches = db.query(RateBatch).order_by(RateBatch.created_at.desc()).all()
    items = [serialize_rate_batch(batch) for batch in batches]
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
    return {
        "batch_id": batch.id,
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
    return PageResponse(items=items, total=len(items))


@router.get("/dictionary/tables")
def list_rates_dictionary_tables(user: User = Depends(require_user)):
    items = [{"table_name": item} for item in RATES_LOAD_SEQUENCE]
    return PageResponse(items=items, total=len(items))


@router.get("/dictionary/tables/{table_name}")
def get_rates_dictionary_table(
    table_name: str,
    user: User = Depends(require_user),
):
    definition = load_table_definition(Path(get_settings().otm_data_dictionary_root), table_name)
    return {
        "table_name": definition.table_name,
        "schema_name": definition.schema_name,
        "description": definition.description,
        "primary_key": definition.primary_key,
        "required_columns": definition.required_columns,
        "date_columns": definition.date_columns,
        "foreign_keys": [item.__dict__ for item in definition.foreign_keys],
    }


@router.post("/dictionary/validate-load-sequence")
def validate_rates_load_sequence(
    payload: LoadSequenceRequest,
    user: User = Depends(require_user),
):
    result = validate_load_sequence(Path(get_settings().otm_data_dictionary_root), payload.tables)
    return {
        "valid": result.valid,
        "known_tables": result.known_tables,
        "missing_tables": result.missing_tables,
        "issues": [item.__dict__ for item in result.issues],
    }


@router.get("/reference/rate-offerings")
def list_rate_offerings(
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
    return PageResponse(items=items, total=len(items))


@router.post("/reference/rate-offerings/duplicate-check")
def check_rate_offering_duplicate(
    payload: RateOfferingDuplicateCheckRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    candidates = []
    for item in db.query(ReferenceObject).filter(ReferenceObject.object_type == "RATE_OFFERING").all():
        metadata = json.loads(item.metadata_json or "{}")
        if all(metadata.get(key) == value for key, value in payload.model_dump().items()):
            candidates.append(
                {
                    "gid": item.gid,
                    "xid": item.xid,
                    "domain_name": item.domain_name,
                    "display_name": item.display_name,
                }
            )
    return {
        "severity": "WARNING" if candidates else "INFO",
        "message": (
            "Potential duplicate Rate Offering found."
            if candidates
            else "No duplicate candidate found."
        ),
        "candidates": candidates,
    }


@router.post("/csv/preview")
def preview_rates_csv(
    payload: CsvPreviewRequest,
    user: User = Depends(require_user),
):
    content = build_otm_csv_preview(
        Path(get_settings().otm_data_dictionary_root),
        payload.table_name,
        payload.columns,
        payload.rows,
    )
    return {"content": content}
