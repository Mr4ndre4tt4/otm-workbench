from pathlib import Path
import json

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import (
    Artifact,
    AuditLog,
    Evidence,
    MasterDataBatch,
    MasterDataCsvFile,
    MasterDataOutputRecord,
    MasterDataTemplate,
    User,
)
from otm_workbench.modules.master_data.coordinate_quality.routes import router as coordinate_quality_router
from otm_workbench.modules.master_data.templates import (
    build_master_data_csv_files,
    build_master_data_template_workbook,
    build_master_data_output_records,
    create_master_data_template_draft,
    create_master_data_template_version,
    map_master_data_batch_to_canonical_records,
    export_master_data_csv_package,
    master_data_template_definition,
    publish_master_data_template,
    parse_master_data_template_workbook,
    seed_master_data_templates,
    serialize_master_data_template,
    update_master_data_template_draft,
    validate_master_data_template_definition,
    validate_master_data_batch_relationships,
    validate_master_data_template,
)
from otm_workbench.platform.services import file_sha256

router = APIRouter(prefix="/api/v1/modules/master-data", tags=["master-data"])
router.include_router(coordinate_quality_router)


def dictionary_root() -> Path:
    return Path(get_settings().otm_data_dictionary_root)


class MasterDataTemplateDraftRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str
    name: str
    catalog_macro_object_code: str
    data_category: str = "MASTER_DATA"
    target_tables: list[dict[str, object]]
    sheets: list[dict[str, object]]
    fields: list[dict[str, object]]
    mappings: list[dict[str, object]]
    relationship_rules: list[dict[str, object]] = []
    documentation_refs: list[dict[str, object]] = []


class MasterDataTemplateVersionRequest(BaseModel):
    new_code: str | None = None


def _json_loads(value: str, fallback):
    try:
        return json.loads(value or "")
    except json.JSONDecodeError:
        return fallback


def master_data_batch_action(
    *,
    batch_id: str,
    key: str,
    label: str,
    path_suffix: str,
    variant: str,
    icon_key: str,
    disabled: bool,
    disabled_reason: str | None,
    result_hint: str,
) -> dict[str, object]:
    return {
        "key": key,
        "label": label,
        "method": "POST",
        "href": f"/api/v1/modules/master-data/batches/{batch_id}{path_suffix}",
        "variant": variant,
        "icon_key": icon_key,
        "requires_confirmation": False,
        "disabled": disabled,
        "disabled_reason": disabled_reason,
        "permission": f"master_data.batch.{key}",
        "result_hint": result_hint,
    }


def build_master_data_batch_available_actions(db: Session, batch: MasterDataBatch) -> list[dict[str, object]]:
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == batch.template_code).first()
    has_relationship_rules = False
    if template is not None:
        has_relationship_rules = bool(master_data_template_definition(template).get("relationship_rules", []))
    can_validate = batch.status == "PARSED"
    can_map = batch.status == "RELATIONSHIP_VALIDATED" or (batch.status == "PARSED" and not has_relationship_rules)
    can_build_output = batch.status == "MAPPED"
    can_build_csv = batch.status in {"OUTPUT_BUILT", "CSV_BUILT"}
    can_export = batch.status in {"CSV_BUILT", "EXPORTED"}
    can_register = batch.status == "EXPORTED"
    return [
        master_data_batch_action(
            batch_id=batch.id,
            key="validate_relationships",
            label="Validate relationships",
            path_suffix="/validate-relationships",
            variant="primary",
            icon_key="check-circle",
            disabled=not can_validate,
            disabled_reason=None if can_validate else "PARSED_STATUS_REQUIRED",
            result_hint="refresh_object",
        ),
        master_data_batch_action(
            batch_id=batch.id,
            key="map_records",
            label="Map records",
            path_suffix="/map",
            variant="primary",
            icon_key="map",
            disabled=not can_map,
            disabled_reason=None if can_map else "RELATIONSHIP_VALIDATION_REQUIRED",
            result_hint="refresh_object",
        ),
        master_data_batch_action(
            batch_id=batch.id,
            key="build_output",
            label="Build output",
            path_suffix="/build-output",
            variant="primary",
            icon_key="database",
            disabled=not can_build_output,
            disabled_reason=None if can_build_output else "MAPPED_STATUS_REQUIRED",
            result_hint="refresh_object",
        ),
        master_data_batch_action(
            batch_id=batch.id,
            key="build_csv",
            label="Build CSV",
            path_suffix="/build-csv",
            variant="secondary",
            icon_key="file-text",
            disabled=not can_build_csv,
            disabled_reason=None if can_build_csv else "OUTPUT_BUILT_STATUS_REQUIRED",
            result_hint="refresh_object",
        ),
        master_data_batch_action(
            batch_id=batch.id,
            key="export_csv_package",
            label="Export package",
            path_suffix="/export-csv-package",
            variant="secondary",
            icon_key="package",
            disabled=not can_export,
            disabled_reason=None if can_export else "CSV_BUILT_STATUS_REQUIRED",
            result_hint="refresh_object",
        ),
        {
            "key": "register_load_plan_package",
            "label": "Register for Load Plan",
            "method": "POST",
            "href": f"/api/v1/modules/load-plan/packages/from-master-data/{batch.id}",
            "variant": "secondary",
            "icon_key": "send",
            "requires_confirmation": False,
            "disabled": not can_register,
            "disabled_reason": None if can_register else "EXPORT_REQUIRED",
            "permission": "load_plan.package.create_from_master_data",
            "result_hint": "refresh_object",
        },
    ]


def serialize_master_data_batch(db: Session, batch: MasterDataBatch) -> dict[str, object]:
    csv_file_count = (
        db.query(MasterDataCsvFile)
        .filter(MasterDataCsvFile.batch_id == batch.id)
        .count()
    )
    return {
        "batch_id": batch.id,
        "template_code": batch.template_code,
        "status": batch.status,
        "file_name": batch.file_name,
        "content_type": batch.content_type,
        "sheet_count": len(_json_loads(batch.sheet_summaries_json, [])),
        "row_count": batch.row_count,
        "issue_count": batch.issue_count,
        "sheet_summaries": _json_loads(batch.sheet_summaries_json, []),
        "issues": _json_loads(batch.issues_json, []),
        "csv_file_count": csv_file_count,
        "available_actions": build_master_data_batch_available_actions(db, batch),
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
    }


def _evidence_batch_id(evidence: Evidence) -> str | None:
    summary = _json_loads(evidence.summary_json, {})
    if isinstance(summary, dict):
        return summary.get("source_entity_id")
    return None


def master_data_batch_artifacts(db: Session, batch_id: str) -> list[tuple[Artifact, Evidence]]:
    rows = (
        db.query(Artifact, Evidence)
        .join(Evidence, Evidence.artifact_id == Artifact.id)
        .filter(Artifact.source_module == "master_data")
        .filter(Evidence.source_module == "master_data")
        .filter(Evidence.client_safe.is_(True))
        .order_by(Artifact.created_at.desc())
        .all()
    )
    return [(artifact, evidence) for artifact, evidence in rows if _evidence_batch_id(evidence) == batch_id]


def serialize_master_data_artifact(batch_id: str, artifact: Artifact, evidence: Evidence) -> dict[str, object]:
    path = Path(artifact.file_path)
    is_available = path.exists() and path.is_file()
    return {
        "id": artifact.id,
        "artifact_type": artifact.artifact_type,
        "file_name": artifact.file_name,
        "content_type": artifact.content_type,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "sensitivity_level": artifact.sensitivity_level,
        "evidence_id": evidence.id,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
        "availability_status": "AVAILABLE" if is_available else "FILE_MISSING",
        "download_url": (
            f"/api/v1/modules/master-data/batches/{batch_id}/artifacts/{artifact.id}/download"
            if is_available
            else None
        ),
    }


def serialize_master_data_output_record(record: MasterDataOutputRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "batch_id": record.batch_id,
        "template_code": record.template_code,
        "target_table": record.target_table,
        "record_index": record.record_index,
        "payload": _json_loads(record.payload_json, {}),
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def serialize_master_data_csv_file(csv_file: MasterDataCsvFile) -> dict[str, object]:
    preview_lines = csv_file.content.splitlines()[:5]
    return {
        "id": csv_file.id,
        "batch_id": csv_file.batch_id,
        "template_code": csv_file.template_code,
        "table_name": csv_file.table_name,
        "file_name": csv_file.file_name,
        "row_count": csv_file.row_count,
        "content_preview": "\n".join(preview_lines),
        "line_count": len(csv_file.content.splitlines()),
        "created_at": csv_file.created_at.isoformat() if csv_file.created_at else None,
        "updated_at": csv_file.updated_at.isoformat() if csv_file.updated_at else None,
    }


def get_master_data_batch_or_404(db: Session, batch_id: str) -> MasterDataBatch:
    batch = db.query(MasterDataBatch).filter(MasterDataBatch.id == batch_id).first()
    if batch is None:
        raise api_error(404, "MASTER_DATA_BATCH_NOT_FOUND", "Master Data batch not found.")
    return batch


def filtered_master_data_batch_query(
    db: Session,
    *,
    template_code: str | None = None,
    status: str | None = None,
    file_name_contains: str | None = None,
    min_row_count: int | None = None,
):
    query = db.query(MasterDataBatch)
    if template_code:
        query = query.filter(MasterDataBatch.template_code == template_code.upper())
    if status:
        query = query.filter(MasterDataBatch.status == status.upper())
    if file_name_contains and file_name_contains.strip():
        query = query.filter(MasterDataBatch.file_name.ilike(f"%{file_name_contains.strip()}%"))
    if min_row_count is not None:
        query = query.filter(MasterDataBatch.row_count >= max(min_row_count, 0))
    return query


def get_batch_artifact_or_404(db: Session, batch_id: str, artifact_id: str) -> tuple[Artifact, Evidence]:
    for artifact, evidence in master_data_batch_artifacts(db, batch_id):
        if artifact.id == artifact_id:
            return artifact, evidence
    raise api_error(404, "MASTER_DATA_ARTIFACT_NOT_FOUND", "Master Data artifact not found for this batch.")


@router.get("/health")
def master_data_health(user: User = Depends(require_user)):
    return {"status": "ok", "module": "master_data", "catalog_macro_object_code": "REGION"}


@router.get("/templates")
def list_master_data_templates(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    templates = db.query(MasterDataTemplate).order_by(MasterDataTemplate.code).all()
    items = [serialize_master_data_template(template) for template in templates]
    return PageResponse(items=items, total=len(items))


@router.post("/templates/drafts")
def create_master_data_template_draft_endpoint(
    payload: MasterDataTemplateDraftRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    try:
        return create_master_data_template_draft(db, payload.model_dump())
    except ValueError as exc:
        raise api_error(
            409,
            "MASTER_DATA_TEMPLATE_DRAFT_CONFLICT",
            "Master Data template draft could not be created.",
            details={"error": str(exc)},
        ) from exc


@router.get("/templates/{template_code}/definition")
def get_master_data_template_definition(
    template_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    return serialize_master_data_template(template)["definition"]


@router.patch("/templates/{template_code}/draft")
def update_master_data_template_draft_endpoint(
    template_code: str,
    payload: MasterDataTemplateDraftRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    try:
        return update_master_data_template_draft(db, template, payload.model_dump())
    except ValueError as exc:
        raise api_error(
            409,
            "MASTER_DATA_TEMPLATE_DRAFT_NOT_UPDATABLE",
            "Master Data template draft could not be updated.",
            details={"error": str(exc)},
        ) from exc


@router.post("/templates/{template_code}/versions")
def create_master_data_template_version_endpoint(
    template_code: str,
    payload: MasterDataTemplateVersionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    try:
        return create_master_data_template_version(db, template, payload.new_code)
    except ValueError as exc:
        raise api_error(
            409,
            "MASTER_DATA_TEMPLATE_VERSION_CONFLICT",
            "Master Data template version could not be created.",
            details={"error": str(exc)},
        ) from exc


@router.post("/templates/{template_code}/validate-definition")
def validate_master_data_template_definition_endpoint(
    template_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    return validate_master_data_template_definition(template, dictionary_root())


@router.post("/templates/{template_code}/publish")
def publish_master_data_template_endpoint(
    template_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    try:
        return publish_master_data_template(db, template, dictionary_root())
    except ValueError as exc:
        raise api_error(
            409,
            "MASTER_DATA_TEMPLATE_NOT_PUBLISHABLE",
            "Master Data template definition must be valid before publishing.",
            details={"error": str(exc)},
        ) from exc


@router.get("/templates/{template_code}")
def get_master_data_template(
    template_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    return serialize_master_data_template(template)


@router.get("/batches")
def list_master_data_batches(
    template_code: str | None = None,
    status: str | None = None,
    file_name_contains: str | None = None,
    min_row_count: int | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    safe_page = max(page, 1)
    safe_page_size = max(1, min(page_size, 100))
    query = filtered_master_data_batch_query(
        db,
        template_code=template_code,
        status=status,
        file_name_contains=file_name_contains,
        min_row_count=min_row_count,
    )
    total = query.count()
    batches = (
        query.order_by(MasterDataBatch.created_at.desc())
        .offset((safe_page - 1) * safe_page_size)
        .limit(safe_page_size)
        .all()
    )
    items = [serialize_master_data_batch(db, batch) for batch in batches]
    return PageResponse(items=items, total=total, page=safe_page, page_size=safe_page_size)


@router.get("/batches/summary")
def get_master_data_batch_summary(
    template_code: str | None = None,
    status: str | None = None,
    file_name_contains: str | None = None,
    min_row_count: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batches = filtered_master_data_batch_query(
        db,
        template_code=template_code,
        status=status,
        file_name_contains=file_name_contains,
        min_row_count=min_row_count,
    ).all()
    status_totals: dict[str, dict[str, int | str]] = {}
    template_totals: dict[str, dict[str, int | str]] = {}
    latest_batch = max(batches, key=lambda batch: batch.created_at) if batches else None
    for batch in batches:
        status_bucket = status_totals.setdefault(
            batch.status,
            {"status": batch.status, "batch_count": 0, "row_count": 0, "issue_count": 0},
        )
        template_bucket = template_totals.setdefault(
            batch.template_code,
            {"template_code": batch.template_code, "batch_count": 0, "row_count": 0, "issue_count": 0},
        )
        for bucket in (status_bucket, template_bucket):
            bucket["batch_count"] = int(bucket["batch_count"]) + 1
            bucket["row_count"] = int(bucket["row_count"]) + batch.row_count
            bucket["issue_count"] = int(bucket["issue_count"]) + batch.issue_count
    return {
        "total_batches": len(batches),
        "total_rows": sum(batch.row_count for batch in batches),
        "total_issues": sum(batch.issue_count for batch in batches),
        "latest_batch_id": latest_batch.id if latest_batch else None,
        "status_breakdown": sorted(status_totals.values(), key=lambda item: str(item["status"])),
        "template_breakdown": sorted(template_totals.values(), key=lambda item: str(item["template_code"])),
    }


@router.get("/batches/{batch_id}")
def get_master_data_batch_detail(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = get_master_data_batch_or_404(db, batch_id)
    return serialize_master_data_batch(db, batch)


@router.get("/batches/{batch_id}/artifacts")
def list_master_data_batch_artifacts(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    get_master_data_batch_or_404(db, batch_id)
    artifacts = [
        serialize_master_data_artifact(batch_id, artifact, evidence)
        for artifact, evidence in master_data_batch_artifacts(db, batch_id)
    ]
    return PageResponse(items=artifacts, total=len(artifacts))


@router.get("/batches/{batch_id}/output-records")
def list_master_data_batch_output_records(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    get_master_data_batch_or_404(db, batch_id)
    records = (
        db.query(MasterDataOutputRecord)
        .filter(MasterDataOutputRecord.batch_id == batch_id)
        .order_by(MasterDataOutputRecord.target_table, MasterDataOutputRecord.record_index)
        .all()
    )
    items = [serialize_master_data_output_record(record) for record in records]
    return PageResponse(items=items, total=len(items))


@router.get("/batches/{batch_id}/csv-files")
def list_master_data_batch_csv_files(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    get_master_data_batch_or_404(db, batch_id)
    csv_files = (
        db.query(MasterDataCsvFile)
        .filter(MasterDataCsvFile.batch_id == batch_id)
        .order_by(MasterDataCsvFile.file_name)
        .all()
    )
    items = [serialize_master_data_csv_file(csv_file) for csv_file in csv_files]
    return PageResponse(items=items, total=len(items))


@router.get("/batches/{batch_id}/artifacts/{artifact_id}/download")
def download_master_data_batch_artifact(
    batch_id: str,
    artifact_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    get_master_data_batch_or_404(db, batch_id)
    artifact, evidence = get_batch_artifact_or_404(db, batch_id, artifact_id)
    path = Path(artifact.file_path)
    if not path.exists() or not path.is_file():
        raise api_error(404, "MASTER_DATA_ARTIFACT_FILE_NOT_FOUND", "Master Data artifact file not found.")
    actual_sha256, actual_size = file_sha256(str(path))
    if actual_sha256 != artifact.sha256:
        raise api_error(409, "MASTER_DATA_ARTIFACT_HASH_MISMATCH", "Master Data artifact hash mismatch.")
    db.add(
        AuditLog(
            actor_user_id=user.email,
            action="master_data.batch.artifact.download",
            target_type="artifact",
            target_id=artifact.id,
            metadata_json=json.dumps(
                {
                    "artifact_id": artifact.id,
                    "batch_id": batch_id,
                    "evidence_id": evidence.id,
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


@router.post("/templates/{template_code}/validate")
def validate_master_data_template_endpoint(
    template_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    return validate_master_data_template(template, dictionary_root())


@router.post("/templates/{template_code}/build-workbook")
def build_master_data_template_workbook_endpoint(
    template_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    if template.status != "PUBLISHED":
        raise api_error(
            409,
            "MASTER_DATA_TEMPLATE_NOT_PUBLISHED",
            "Master Data template must be published before workbook generation.",
        )
    validation = validate_master_data_template(template, dictionary_root())
    if not validation["valid"]:
        raise api_error(
            409,
            "MASTER_DATA_TEMPLATE_INVALID",
            "Master Data template must be valid before workbook generation.",
            details=validation,
        )
    return build_master_data_template_workbook(db, template, Path(get_settings().artifact_root))


@router.post("/templates/{template_code}/batches")
def create_master_data_batch_from_workbook(
    template_code: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    if template.status != "PUBLISHED":
        raise api_error(
            409,
            "MASTER_DATA_TEMPLATE_NOT_PUBLISHED",
            "Master Data template must be published before batch parsing.",
        )
    validation = validate_master_data_template(template, dictionary_root())
    if not validation["valid"]:
        raise api_error(
            409,
            "MASTER_DATA_TEMPLATE_INVALID",
            "Master Data template must be valid before batch parsing.",
            details=validation,
        )
    try:
        result = parse_master_data_template_workbook(
            db,
            template,
            file.file,
            file.filename or "master_data_upload.xlsx",
            file.content_type or "application/octet-stream",
        )
        return serialize_master_data_batch(db, get_master_data_batch_or_404(db, str(result["batch_id"])))
    except (KeyError, ValueError) as exc:
        raise api_error(
            422,
            "MASTER_DATA_WORKBOOK_INVALID",
            "Uploaded workbook does not match the template.",
            details={"error": str(exc)},
        ) from exc


@router.post("/batches/{batch_id}/validate-relationships")
def validate_master_data_batch_relationships_endpoint(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(MasterDataBatch).filter(MasterDataBatch.id == batch_id).first()
    if batch is None:
        raise api_error(404, "MASTER_DATA_BATCH_NOT_FOUND", "Master Data batch not found.")
    try:
        return validate_master_data_batch_relationships(db, batch)
    except ValueError as exc:
        raise api_error(
            409,
            "MASTER_DATA_BATCH_RELATIONSHIP_NOT_READY",
            "Master Data batch is not ready for relationship validation.",
            details={"error": str(exc)},
        ) from exc


@router.post("/batches/{batch_id}/map")
def map_master_data_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    batch = db.query(MasterDataBatch).filter(MasterDataBatch.id == batch_id).first()
    if batch is None:
        raise api_error(404, "MASTER_DATA_BATCH_NOT_FOUND", "Master Data batch not found.")
    template = (
        db.query(MasterDataTemplate)
        .filter(MasterDataTemplate.code == batch.template_code)
        .first()
    )
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    try:
        return map_master_data_batch_to_canonical_records(db, template, batch)
    except ValueError as exc:
        raise api_error(
            409,
            "MASTER_DATA_BATCH_NOT_MAPPABLE",
            "Master Data batch is not ready for mapping.",
            details={"error": str(exc)},
        ) from exc


@router.post("/batches/{batch_id}/build-output")
def build_master_data_batch_output(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(MasterDataBatch).filter(MasterDataBatch.id == batch_id).first()
    if batch is None:
        raise api_error(404, "MASTER_DATA_BATCH_NOT_FOUND", "Master Data batch not found.")
    try:
        return build_master_data_output_records(db, batch)
    except ValueError as exc:
        raise api_error(
            409,
            "MASTER_DATA_BATCH_OUTPUT_NOT_READY",
            "Master Data batch is not ready for output record generation.",
            details={"error": str(exc)},
        ) from exc


@router.post("/batches/{batch_id}/build-csv")
def build_master_data_batch_csv(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(MasterDataBatch).filter(MasterDataBatch.id == batch_id).first()
    if batch is None:
        raise api_error(404, "MASTER_DATA_BATCH_NOT_FOUND", "Master Data batch not found.")
    try:
        return build_master_data_csv_files(db, batch, dictionary_root())
    except ValueError as exc:
        raise api_error(
            409,
            "MASTER_DATA_BATCH_CSV_NOT_READY",
            "Master Data batch is not ready for CSV generation.",
            details={"error": str(exc)},
        ) from exc


@router.post("/batches/{batch_id}/export-csv-package")
def export_master_data_batch_csv_package(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(MasterDataBatch).filter(MasterDataBatch.id == batch_id).first()
    if batch is None:
        raise api_error(404, "MASTER_DATA_BATCH_NOT_FOUND", "Master Data batch not found.")
    try:
        return export_master_data_csv_package(
            db,
            batch,
            Path(get_settings().artifact_root),
            user.id,
        )
    except ValueError as exc:
        raise api_error(
            409,
            "MASTER_DATA_BATCH_EXPORT_NOT_READY",
            "Master Data batch is not ready for CSV package export.",
            details={"error": str(exc)},
        ) from exc
