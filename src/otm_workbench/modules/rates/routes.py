import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.catalog.services import reference_options_payload, serialize_table_definition
from otm_workbench.models import (
    ActiveContext,
    Artifact,
    AuditLog,
    Evidence,
    RateBatch,
    RateBatchIssue,
    RateBatchRow,
    RateBatchTable,
    ReferenceObject,
    User,
)
from otm_workbench.modules.rates.batches import (
    UnknownRatesSchemaRoot,
    add_rate_batch_tables,
    create_rate_batch,
    get_batch_table_rows,
)
from otm_workbench.platform.scoping import (
    apply_operational_scope,
    normalize_domain_name,
    operational_scope_from_context,
)
from otm_workbench.modules.rates.approval import (
    approve_rate_batch,
    get_existing_approval_evidence,
    get_rate_batch_readiness,
)
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
from otm_workbench.modules.rates.validation import rate_batch_schema_validation_summary, validate_rate_batch

router = APIRouter(prefix="/api/v1/modules/rates", tags=["rates"])
UNSUPPORTED_RATES_CATALOG_CODE = "UNSUPPORTED_RATES_CATALOG_MACRO_OBJECT"
UNSUPPORTED_RATES_CATALOG_MESSAGE = "Catalog macro-object is outside the Rates module sequence."


def is_unsupported_rates_catalog_macro_object(catalog_macro_object_code: str | None) -> bool:
    return bool(catalog_macro_object_code and catalog_macro_object_code != "RATE_RECORD")


def unsupported_rates_catalog_payload(catalog_macro_object_code: str) -> dict[str, object]:
    return {
        "code": UNSUPPORTED_RATES_CATALOG_CODE,
        "message": UNSUPPORTED_RATES_CATALOG_MESSAGE,
        "details": {"catalog_macro_object_code": catalog_macro_object_code},
    }


def unsupported_rates_catalog_error(catalog_macro_object_code: str) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail=unsupported_rates_catalog_payload(catalog_macro_object_code),
    )


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
    schema_root_ids: list[str] = []


class RateBatchTablePayload(BaseModel):
    table_name: str
    rows: list[dict[str, object]] = []


class AddRateBatchTablesRequest(BaseModel):
    tables: list[RateBatchTablePayload]


class ApproveRateBatchRequest(BaseModel):
    approval_note: str = ""


def serialize_rate_batch(batch: RateBatch) -> dict[str, object]:
    scenario = get_rate_scenario(batch.scenario_code)
    try:
        schema_root_ids = json.loads(batch.schema_root_ids_json or "[]")
    except json.JSONDecodeError:
        schema_root_ids = []
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
        "schema_root_ids": schema_root_ids,
        "summary_json": batch.summary_json,
    }


def scoped_rate_batch_query(db: Session, user: User):
    query = db.query(RateBatch)
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    if active_context is None:
        if not user.is_admin:
            return query.filter(RateBatch.id.is_(None))
        return query
    return apply_operational_scope(query, RateBatch, operational_scope_from_context(active_context))


def resolve_rate_batch_create_scope(
    db: Session,
    user: User,
    payload: CreateRateBatchRequest,
) -> tuple[str | None, str | None, str | None, str]:
    if user.is_admin:
        return payload.project_id, payload.environment_id, payload.profile_id, normalize_domain_name(payload.domain_name)

    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    if active_context is None or not active_context.project_id or not active_context.environment_id:
        raise api_error(
            403,
            "ACTIVE_CONTEXT_REQUIRED",
            "Rates batch creation requires an active project and environment context.",
        )

    scope = operational_scope_from_context(active_context)
    project_id = payload.project_id or scope.project_id
    environment_id = payload.environment_id or scope.environment_id
    profile_id = payload.profile_id or scope.profile_id
    domain_name = normalize_domain_name(payload.domain_name)
    if project_id != scope.project_id or environment_id != scope.environment_id:
        raise api_error(
            403,
            "RATES_SCOPE_FORBIDDEN",
            "Rates batch creation is limited to the active project and environment.",
        )
    if not scope.can_view_all_domains and domain_name not in scope.allowed_domain_names:
        raise api_error(
            403,
            "RATES_SCOPE_FORBIDDEN",
            "Rates batch creation is limited to the active domain scope.",
        )
    if payload.profile_id and scope.profile_id and payload.profile_id != scope.profile_id:
        raise api_error(
            403,
            "RATES_SCOPE_FORBIDDEN",
            "Rates batch creation is limited to the active profile scope.",
        )
    return project_id, environment_id, profile_id, domain_name


def get_scoped_rate_batch_or_404(db: Session, user: User, batch_id: str) -> RateBatch:
    batch = scoped_rate_batch_query(db, user).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    return batch


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


def serialize_rate_batch_row(row: RateBatchRow) -> dict[str, object]:
    try:
        payload = json.loads(row.normalized_payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    return {
        "row_index": row.row_index,
        "status": row.status,
        "payload": payload,
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


def action_disabled_reason(blockers: list[str], fallback: str) -> str:
    return ";".join(blockers) if blockers else fallback


def rates_action(
    *,
    batch_id: str,
    key: str,
    label: str,
    method: str,
    path_suffix: str,
    variant: str,
    icon_key: str,
    requires_confirmation: bool,
    disabled: bool,
    disabled_reason: str | None,
    permission: str,
    result_hint: str,
) -> dict[str, object]:
    return {
        "key": key,
        "label": label,
        "method": method,
        "href": f"/api/v1/modules/rates/batches/{batch_id}{path_suffix}",
        "variant": variant,
        "icon_key": icon_key,
        "requires_confirmation": requires_confirmation,
        "disabled": disabled,
        "disabled_reason": disabled_reason,
        "permission": permission,
        "result_hint": result_hint,
    }


def build_rate_batch_available_actions(db: Session, batch: RateBatch) -> list[dict[str, object]]:
    readiness = get_rate_batch_readiness(db, batch)
    approval_disabled = not readiness.ready_for_approval
    export_disabled = not readiness.ready_for_export
    artifacts_disabled = not bool(list_batch_export_artifacts(db, batch.id))
    evidence_disabled = not bool(list_batch_export_evidence(db, batch.id))
    return [
        rates_action(
            batch_id=batch.id,
            key="validate",
            label="Validate",
            method="POST",
            path_suffix="/validate",
            variant="secondary",
            icon_key="check-circle",
            requires_confirmation=False,
            disabled=batch.status == "APPROVED",
            disabled_reason="ALREADY_APPROVED" if batch.status == "APPROVED" else None,
            permission="rates.batch.validate",
            result_hint="refresh_object",
        ),
        rates_action(
            batch_id=batch.id,
            key="approve",
            label="Approve",
            method="POST",
            path_suffix="/approve",
            variant="primary",
            icon_key="badge-check",
            requires_confirmation=True,
            disabled=approval_disabled,
            disabled_reason=(
                action_disabled_reason(readiness.blockers, "NOT_READY_FOR_APPROVAL")
                if approval_disabled
                else None
            ),
            permission="rates.batch.approve",
            result_hint="refresh_object",
        ),
        rates_action(
            batch_id=batch.id,
            key="export_csv",
            label="Export CSV",
            method="POST",
            path_suffix="/export-csv",
            variant="secondary",
            icon_key="download",
            requires_confirmation=False,
            disabled=export_disabled,
            disabled_reason=(
                action_disabled_reason(readiness.blockers, "NOT_READY_FOR_EXPORT")
                if export_disabled
                else None
            ),
            permission="rates.batch.export",
            result_hint="download",
        ),
        rates_action(
            batch_id=batch.id,
            key="view_artifacts",
            label="View artifacts",
            method="GET",
            path_suffix="/artifacts",
            variant="menu",
            icon_key="archive",
            requires_confirmation=False,
            disabled=artifacts_disabled,
            disabled_reason="NO_ARTIFACTS" if artifacts_disabled else None,
            permission="rates.batch.view",
            result_hint="refresh_list",
        ),
        rates_action(
            batch_id=batch.id,
            key="view_evidence",
            label="View evidence",
            method="GET",
            path_suffix="/evidence",
            variant="menu",
            icon_key="file-check",
            requires_confirmation=False,
            disabled=evidence_disabled,
            disabled_reason="NO_EVIDENCE" if evidence_disabled else None,
            permission="rates.batch.view",
            result_hint="refresh_list",
        ),
    ]


def module_action(
    *,
    key: str,
    label: str,
    method: str,
    href: str,
    variant: str,
    icon_key: str,
    requires_confirmation: bool,
    disabled: bool,
    disabled_reason: str | None,
    permission: str,
    result_hint: str,
) -> dict[str, object]:
    return {
        "key": key,
        "label": label,
        "method": method,
        "href": href,
        "variant": variant,
        "icon_key": icon_key,
        "requires_confirmation": requires_confirmation,
        "disabled": disabled,
        "disabled_reason": disabled_reason,
        "permission": permission,
        "result_hint": result_hint,
    }


def serialize_rate_batch_summary_item(db: Session, batch: RateBatch) -> dict[str, object]:
    readiness = get_rate_batch_readiness(db, batch)
    return {
        "id": batch.id,
        "code": batch.scenario_code,
        "display_name": batch.name,
        "status": batch.status,
        "project_id": batch.project_id,
        "profile_id": batch.profile_id,
        "environment_id": batch.environment_id,
        "domain_name": batch.domain_name,
        "summary": {
            "ready_for_approval": readiness.ready_for_approval,
            "ready_for_export": readiness.ready_for_export,
            "table_count": readiness.table_count,
            "row_count": readiness.row_count,
            "issue_summary": readiness.issue_summary,
        },
        "badges": readiness.blockers,
        "available_actions": build_rate_batch_available_actions(db, batch),
    }


def rates_summary_payload(db: Session, user: User) -> dict[str, object]:
    batches = scoped_rate_batch_query(db, user).order_by(RateBatch.created_at.desc()).all()
    readiness_by_batch = {batch.id: get_rate_batch_readiness(db, batch) for batch in batches}
    total = len(batches)
    ready_for_approval = sum(
        1 for readiness in readiness_by_batch.values() if readiness.ready_for_approval
    )
    ready_for_export = sum(1 for readiness in readiness_by_batch.values() if readiness.ready_for_export)
    blocked = sum(1 for readiness in readiness_by_batch.values() if readiness.blockers)
    open_blockers = []
    for batch in batches:
        readiness = readiness_by_batch[batch.id]
        if not readiness.blockers:
            continue
        reason = ";".join(readiness.blockers)
        open_blockers.append(
            {
                "object_id": batch.id,
                "object_type": "rate_batch",
                "severity": "warning",
                "codes": readiness.blockers,
                "message": f"Rate batch is not ready: {reason}",
            }
        )
    recent_artifacts = [
        serialize_artifact(artifact)
        for artifact in db.query(Artifact)
        .filter(Artifact.source_module == "rates")
        .order_by(Artifact.created_at.desc())
        .limit(5)
        .all()
    ]
    return {
        "module_id": "rates",
        "status": "ok",
        "title": "Rates Studio",
        "description": "Prepare, validate, approve and export OTM rates packages.",
        "primary_object": "rate_batch",
        "counts": [
            {"key": "total", "label": "Total", "value": total, "severity": "neutral"},
            {
                "key": "ready_for_approval",
                "label": "Ready for approval",
                "value": ready_for_approval,
                "severity": "success",
            },
            {
                "key": "ready_for_export",
                "label": "Ready for export",
                "value": ready_for_export,
                "severity": "success",
            },
            {"key": "blocked", "label": "Blocked", "value": blocked, "severity": "warning"},
        ],
        "recent_objects": [
            serialize_rate_batch_summary_item(db, batch)
            for batch in batches[:5]
        ],
        "open_blockers": open_blockers[:5],
        "recent_jobs": [],
        "recent_artifacts": recent_artifacts,
        "available_actions": [
            module_action(
                key="create_batch",
                label="Create rate batch",
                method="POST",
                href="/api/v1/modules/rates/batches",
                variant="primary",
                icon_key="plus",
                requires_confirmation=False,
                disabled=False,
                disabled_reason=None,
                permission="rates.batch.create",
                result_hint="refresh_list",
            )
        ],
    }


@router.get("/summary")
def get_rates_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    return rates_summary_payload(db, user)


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
        if is_unsupported_rates_catalog_macro_object(catalog_macro_object_code):
            payload = PageResponse(items=[], total=0).model_dump()
            payload.update(unsupported_rates_catalog_payload(catalog_macro_object_code))
            payload["catalog_macro_object_code"] = catalog_macro_object_code
            return payload
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
    project_id, environment_id, profile_id, domain_name = resolve_rate_batch_create_scope(db, user, payload)
    try:
        batch = create_rate_batch(
            db,
            scenario_code=payload.scenario_code,
            name=payload.name,
            domain_name=domain_name,
            project_id=project_id,
            environment_id=environment_id,
            profile_id=profile_id,
            description=payload.description,
            source_type=payload.source_type,
            schema_root_ids=payload.schema_root_ids,
            created_by=user.email,
        )
    except UnknownRatesSchemaRoot as exc:
        raise api_error(
            400,
            "RATES_SCHEMA_ROOT_NOT_FOUND",
            "Rate batch references an indexed Schema Pack root that does not exist.",
            details={"schema_root_id": exc.schema_root_id},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_rate_batch(batch)


@router.get("/batches")
def list_rates_batches(
    catalog_macro_object_code: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batches = scoped_rate_batch_query(db, user).order_by(RateBatch.created_at.desc()).all()
    items = [serialize_rate_batch(batch) for batch in batches]
    if catalog_macro_object_code:
        if is_unsupported_rates_catalog_macro_object(catalog_macro_object_code):
            payload = PageResponse(items=[], total=0).model_dump()
            payload.update(unsupported_rates_catalog_payload(catalog_macro_object_code))
            payload["catalog_macro_object_code"] = catalog_macro_object_code
            return payload
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
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)
    tables = (
        db.query(RateBatchTable)
        .filter(RateBatchTable.batch_id == batch.id)
        .order_by(RateBatchTable.sequence_index)
        .all()
    )
    payload = serialize_rate_batch(batch)
    payload["tables"] = [serialize_rate_batch_table(table) for table in tables]
    payload["available_actions"] = build_rate_batch_available_actions(db, batch)
    return payload


@router.get("/batches/{batch_id}/tables/{table_name}")
def get_rates_batch_table_detail(
    batch_id: str,
    table_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)
    normalized_table_name = table_name.upper()
    table = (
        db.query(RateBatchTable)
        .filter(RateBatchTable.batch_id == batch.id, RateBatchTable.table_name == normalized_table_name)
        .first()
    )
    if table is None:
        raise HTTPException(status_code=404, detail="Rate batch table not found.")
    rows = (
        db.query(RateBatchRow)
        .filter(RateBatchRow.batch_table_id == table.id)
        .order_by(RateBatchRow.row_index)
        .all()
    )
    issues = (
        db.query(RateBatchIssue)
        .filter(RateBatchIssue.batch_id == batch.id, RateBatchIssue.table_name == normalized_table_name)
        .order_by(RateBatchIssue.severity, RateBatchIssue.issue_code)
        .all()
    )
    scenario = get_rate_scenario(batch.scenario_code)
    return {
        "batch_id": batch.id,
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
        "table": serialize_rate_batch_table(table),
        "rows": [serialize_rate_batch_row(row) for row in rows],
        "issues": [serialize_rate_batch_issue(issue) for issue in issues],
        "total": len(rows),
    }


@router.get("/batches/{batch_id}/readiness")
def get_rates_batch_readiness(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)
    scenario = get_rate_scenario(batch.scenario_code)
    payload = get_rate_batch_readiness(db, batch).to_dict()
    payload["catalog_macro_object_code"] = scenario.catalog_macro_object_code
    payload["catalog_load_plan_path"] = scenario.catalog_load_plan_path
    payload["available_actions"] = build_rate_batch_available_actions(db, batch)
    return payload


@router.post("/batches/{batch_id}/approve")
def approve_rates_batch(
    batch_id: str,
    payload: ApproveRateBatchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)
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
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)
    tables = add_rate_batch_tables(
        db,
        batch=batch,
        tables=[item.model_dump() for item in payload.tables],
    )
    scenario = get_rate_scenario(batch.scenario_code)
    return {
        "batch_id": batch.id,
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
        "tables": [serialize_rate_batch_table(table) for table in tables],
    }


@router.post("/batches/{batch_id}/validate")
def validate_rates_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)
    issues = validate_rate_batch(
        db,
        dictionary_root=Path(get_settings().otm_data_dictionary_root),
        batch=batch,
    )
    scenario = get_rate_scenario(batch.scenario_code)
    result = {
        "batch_id": batch.id,
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
        "status": batch.status,
        "valid": not any(issue.severity == "ERROR" for issue in issues),
        "issues": [serialize_rate_batch_issue(issue) for issue in issues],
    }
    schema_validation = rate_batch_schema_validation_summary(db, batch)
    if schema_validation is not None:
        result["schema_validation"] = schema_validation
    return result


@router.get("/batches/{batch_id}/issues")
def list_rates_batch_issues(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)
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
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)
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
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)
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
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)
    artifacts = list_batch_export_artifacts(db, batch.id)
    items = []
    for artifact in artifacts:
        item = serialize_artifact(artifact)
        item["download_url"] = f"/api/v1/modules/rates/batches/{batch.id}/artifacts/{artifact.id}/download"
        items.append(item)
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
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)
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
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)

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

    scenario = get_rate_scenario(batch.scenario_code)
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
                    "catalog_macro_object_code": scenario.catalog_macro_object_code,
                    "catalog_load_plan_path": scenario.catalog_load_plan_path,
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
    batch = get_scoped_rate_batch_or_404(db, user, batch_id)
    evidence_items = list_batch_export_evidence(db, batch.id)
    approval_evidence = get_existing_approval_evidence(db, batch.id)
    if approval_evidence is not None and all(item.id != approval_evidence.id for item in evidence_items):
        evidence_items = [approval_evidence, *evidence_items]
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
    payload = PageResponse(items=items, total=len(items)).model_dump()
    scenario = get_rate_scenario("complete_tariff")
    if catalog_macro_object_code and catalog_macro_object_code != scenario.catalog_macro_object_code:
        payload.update(unsupported_rates_catalog_payload(catalog_macro_object_code))
        payload["catalog_macro_object_code"] = catalog_macro_object_code
        payload["items"] = []
        payload["total"] = 0
        return payload
    if catalog_macro_object_code:
        payload["catalog_macro_object_code"] = scenario.catalog_macro_object_code
        payload["catalog_load_plan_path"] = scenario.catalog_load_plan_path
    return payload


@router.get("/dictionary/tables/{table_name}")
def get_rates_dictionary_table(
    table_name: str,
    catalog_macro_object_code: str | None = None,
    user: User = Depends(require_user),
):
    if is_unsupported_rates_catalog_macro_object(catalog_macro_object_code):
        raise unsupported_rates_catalog_error(catalog_macro_object_code)
    definition = load_table_definition(Path(get_settings().otm_data_dictionary_root), table_name)
    payload = serialize_table_definition(definition)
    payload["foreign_keys"] = [item.__dict__ for item in definition.foreign_keys]
    if catalog_macro_object_code:
        scenario = get_rate_scenario("complete_tariff")
        payload["catalog_macro_object_code"] = scenario.catalog_macro_object_code
        payload["catalog_load_plan_path"] = scenario.catalog_load_plan_path
    return payload


@router.post("/dictionary/validate-load-sequence")
def validate_rates_load_sequence(
    payload: LoadSequenceRequest,
    user: User = Depends(require_user),
):
    scenario = get_rate_scenario("complete_tariff")
    if is_unsupported_rates_catalog_macro_object(payload.catalog_macro_object_code):
        return {
            **unsupported_rates_catalog_payload(payload.catalog_macro_object_code),
            "catalog_macro_object_code": payload.catalog_macro_object_code,
            "valid": False,
            "known_tables": [],
            "missing_tables": [],
            "issues": [
                {
                    "severity": "ERROR",
                    "table_name": payload.tables[0] if payload.tables else None,
                    "parent_table_name": None,
                    "message": UNSUPPORTED_RATES_CATALOG_MESSAGE,
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
        response["catalog_macro_object_code"] = scenario.catalog_macro_object_code
        response["catalog_load_plan_path"] = scenario.catalog_load_plan_path
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
        scenario = get_rate_scenario("complete_tariff")
        payload["catalog_macro_object_code"] = scenario.catalog_macro_object_code
        payload["catalog_load_plan_path"] = scenario.catalog_load_plan_path
        if is_unsupported_rates_catalog_macro_object(catalog_macro_object_code):
            payload.update(unsupported_rates_catalog_payload(catalog_macro_object_code))
            payload["catalog_macro_object_code"] = catalog_macro_object_code
            payload.pop("catalog_load_plan_path", None)
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
        scenario = get_rate_scenario("complete_tariff")
        payload["catalog_macro_object_code"] = scenario.catalog_macro_object_code
        payload["catalog_load_plan_path"] = scenario.catalog_load_plan_path
        if is_unsupported_rates_catalog_macro_object(catalog_macro_object_code):
            payload.update(unsupported_rates_catalog_payload(catalog_macro_object_code))
            payload["catalog_macro_object_code"] = catalog_macro_object_code
            payload.pop("catalog_load_plan_path", None)
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
        scenario = get_rate_scenario("complete_tariff")
        response["catalog_macro_object_code"] = scenario.catalog_macro_object_code
        response["catalog_load_plan_path"] = scenario.catalog_load_plan_path
        if is_unsupported_rates_catalog_macro_object(payload.catalog_macro_object_code):
            response.update(unsupported_rates_catalog_payload(payload.catalog_macro_object_code))
            response["catalog_macro_object_code"] = payload.catalog_macro_object_code
            response.pop("catalog_load_plan_path", None)
    return response


@router.post("/csv/preview")
def preview_rates_csv(
    payload: CsvPreviewRequest,
    user: User = Depends(require_user),
):
    if is_unsupported_rates_catalog_macro_object(payload.catalog_macro_object_code):
        raise unsupported_rates_catalog_error(payload.catalog_macro_object_code)
    content = build_otm_csv_preview(
        Path(get_settings().otm_data_dictionary_root),
        payload.table_name,
        payload.columns,
        payload.rows,
    )
    response = {"content": content}
    if payload.catalog_macro_object_code:
        scenario = get_rate_scenario("complete_tariff")
        response["catalog_macro_object_code"] = scenario.catalog_macro_object_code
        response["catalog_load_plan_path"] = scenario.catalog_load_plan_path
    return response
