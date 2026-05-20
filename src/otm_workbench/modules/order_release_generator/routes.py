from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import OrderReleaseBatch, OrderReleaseBatchRow, OrderReleaseTemplate, User
from otm_workbench.modules.order_release_generator.batches import (
    create_order_release_batch,
    serialize_order_release_batch,
)
from otm_workbench.modules.order_release_generator.job_tracking import record_completed_order_release_job
from otm_workbench.modules.order_release_generator.templates import (
    seed_order_release_templates,
    serialize_order_release_template,
)
from otm_workbench.modules.order_release_generator.xml_artifacts import generate_order_release_xml_artifact
from otm_workbench.modules.order_release_generator.xml_preview import build_order_release_xml


router = APIRouter(prefix="/api/v1/modules/order-release-generator", tags=["order-release-generator"])


class OrderReleaseBatchCreateRequest(BaseModel):
    template_id: str
    file_name: str
    rows: list[dict[str, object]]


@router.get("/health")
def order_release_generator_health(user: User = Depends(require_user)):
    return {"status": "ok", "module": "order_release_generator"}


@router.get("/templates")
def list_order_release_templates(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_order_release_templates(db)
    templates = (
        db.query(OrderReleaseTemplate)
        .order_by(OrderReleaseTemplate.code, OrderReleaseTemplate.version.desc())
        .all()
    )
    items = [serialize_order_release_template(template) for template in templates]
    return PageResponse(items=items, total=len(items))


@router.post("/batches")
def create_batch(
    payload: OrderReleaseBatchCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    template = db.get(OrderReleaseTemplate, payload.template_id)
    if template is None:
        raise api_error(404, "ORDER_RELEASE_TEMPLATE_NOT_FOUND", "Order Release template not found.")
    batch = create_order_release_batch(
        db,
        template=template,
        file_name=payload.file_name,
        rows=payload.rows,
        created_by=user.email,
    )
    rows = (
        db.query(OrderReleaseBatchRow)
        .filter(OrderReleaseBatchRow.batch_id == batch.id)
        .order_by(OrderReleaseBatchRow.row_number)
        .all()
    )
    return serialize_order_release_batch(batch, rows)


@router.get("/batches/{batch_id}")
def get_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.get(OrderReleaseBatch, batch_id)
    if batch is None:
        raise api_error(404, "ORDER_RELEASE_BATCH_NOT_FOUND", "Order Release batch not found.")
    rows = (
        db.query(OrderReleaseBatchRow)
        .filter(OrderReleaseBatchRow.batch_id == batch.id)
        .order_by(OrderReleaseBatchRow.row_number)
        .all()
    )
    return serialize_order_release_batch(batch, rows)


@router.post("/batches/{batch_id}/preview-xml")
def preview_batch_xml(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.get(OrderReleaseBatch, batch_id)
    if batch is None:
        raise api_error(404, "ORDER_RELEASE_BATCH_NOT_FOUND", "Order Release batch not found.")
    if batch.status != "VALID":
        raise api_error(409, "ORDER_RELEASE_BATCH_INVALID", "Order Release batch must be valid before XML preview.")
    rows = (
        db.query(OrderReleaseBatchRow)
        .filter(OrderReleaseBatchRow.batch_id == batch.id)
        .order_by(OrderReleaseBatchRow.row_number)
        .all()
    )
    payload = build_order_release_xml(batch, rows)
    job = record_completed_order_release_job(
        db,
        job_type="ORDER_RELEASE_XML_PREVIEW",
        batch_id=batch.id,
        result_payload={
            "batch_id": batch.id,
            "release_count": payload["release_count"],
            "line_count": payload["line_count"],
        },
        created_by=user.email,
        message="Order Release XML preview generated.",
    )
    return {**payload, "job_id": job.id}


@router.post("/batches/{batch_id}/generate-xml-artifact")
def generate_batch_xml_artifact(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.get(OrderReleaseBatch, batch_id)
    if batch is None:
        raise api_error(404, "ORDER_RELEASE_BATCH_NOT_FOUND", "Order Release batch not found.")
    if batch.status != "VALID":
        raise api_error(409, "ORDER_RELEASE_BATCH_INVALID", "Order Release batch must be valid before XML generation.")
    rows = (
        db.query(OrderReleaseBatchRow)
        .filter(OrderReleaseBatchRow.batch_id == batch.id)
        .order_by(OrderReleaseBatchRow.row_number)
        .all()
    )
    payload = generate_order_release_xml_artifact(
        db,
        batch=batch,
        rows=rows,
        artifact_root=get_settings().artifact_root,
    )
    job = record_completed_order_release_job(
        db,
        job_type="ORDER_RELEASE_XML_GENERATE",
        batch_id=batch.id,
        result_payload={
            "batch_id": batch.id,
            "artifact_id": payload["artifact_id"],
            "evidence_id": payload["evidence_id"],
            "sha256": payload["sha256"],
            "size_bytes": payload["size_bytes"],
            "release_count": payload["release_count"],
            "line_count": payload["line_count"],
        },
        created_by=user.email,
        message="Order Release XML artifact generated.",
    )
    return {**payload, "job_id": job.id}


@router.post("/batches/{batch_id}/submit-otm")
def submit_batch_to_otm(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.get(OrderReleaseBatch, batch_id)
    if batch is None:
        raise api_error(404, "ORDER_RELEASE_BATCH_NOT_FOUND", "Order Release batch not found.")
    raise api_error(
        409,
        "ORDER_RELEASE_OTM_SUBMIT_DISABLED",
        "Direct OTM submission is disabled in MVP0.",
        {
            "batch_id": batch.id,
            "required_capability": "order_release_generator.submit_otm",
            "reason": "MVP0 has no governed OTM connection/capability for direct submit.",
        },
    )
