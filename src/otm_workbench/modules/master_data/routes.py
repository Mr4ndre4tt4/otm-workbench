from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import MasterDataBatch, MasterDataTemplate, User
from otm_workbench.modules.master_data.coordinate_quality.routes import router as coordinate_quality_router
from otm_workbench.modules.master_data.templates import (
    build_master_data_csv_files,
    build_master_data_template_workbook,
    build_master_data_output_records,
    create_master_data_template_draft,
    create_master_data_template_version,
    map_master_data_batch_to_canonical_records,
    export_master_data_csv_package,
    publish_master_data_template,
    parse_master_data_template_workbook,
    seed_master_data_templates,
    serialize_master_data_template,
    update_master_data_template_draft,
    validate_master_data_template_definition,
    validate_master_data_batch_relationships,
    validate_master_data_template,
)

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
        return parse_master_data_template_workbook(
            db,
            template,
            file.file,
            file.filename or "master_data_upload.xlsx",
            file.content_type or "application/octet-stream",
        )
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
