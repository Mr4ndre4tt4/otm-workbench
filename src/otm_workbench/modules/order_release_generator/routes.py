import json
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import Artifact, AuditLog, Job, OrderReleaseBatch, OrderReleaseBatchRow, OrderReleaseTemplate, User
from otm_workbench.modules.order_release_generator.batches import (
    create_order_release_batch,
    serialize_order_release_batch,
)
from otm_workbench.modules.order_release_generator.job_tracking import record_completed_order_release_job
from otm_workbench.modules.order_release_generator.templates import (
    create_order_release_template,
    seed_order_release_templates,
    serialize_order_release_template,
)
from otm_workbench.modules.order_release_generator.xml_artifacts import generate_order_release_xml_artifact
from otm_workbench.modules.order_release_generator.xml_preview import build_order_release_xml
from otm_workbench.modules.rates.exports import file_sha256


router = APIRouter(prefix="/api/v1/modules/order-release-generator", tags=["order-release-generator"])


def artifact_ids_for_batch_jobs(db: Session, batch_id: str) -> list[str]:
    artifact_ids: list[str] = []
    jobs = (
        db.query(Job)
        .filter(Job.source_module == "order_release_generator")
        .filter(Job.job_type == "ORDER_RELEASE_XML_GENERATE")
        .order_by(Job.created_at.desc())
        .all()
    )
    for job in jobs:
        try:
            input_payload = json.loads(job.input_json or "{}")
            result_payload = json.loads(job.result_json or "{}")
        except json.JSONDecodeError:
            continue
        if input_payload.get("batch_id") != batch_id:
            continue
        artifact_id = result_payload.get("artifact_id")
        if isinstance(artifact_id, str) and artifact_id not in artifact_ids:
            artifact_ids.append(artifact_id)
    return artifact_ids


def list_batch_artifacts(db: Session, batch_id: str) -> list[Artifact]:
    artifacts: list[Artifact] = []
    for artifact_id in artifact_ids_for_batch_jobs(db, batch_id):
        artifact = db.get(Artifact, artifact_id)
        if artifact is not None and artifact.source_module == "order_release_generator":
            artifacts.append(artifact)
    return artifacts


def serialize_order_release_artifact(artifact: Artifact, batch_id: str) -> dict[str, object]:
    path = Path(artifact.file_path)
    download_url = None
    if path.exists() and path.is_file():
        download_url = f"/api/v1/modules/order-release-generator/batches/{batch_id}/artifacts/{artifact.id}/download"
    return {
        "id": artifact.id,
        "batch_id": batch_id,
        "source_module": artifact.source_module,
        "artifact_type": artifact.artifact_type,
        "file_name": artifact.file_name,
        "content_type": artifact.content_type,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "sensitivity_level": artifact.sensitivity_level,
        "download_url": download_url,
    }


class OrderReleaseBatchCreateRequest(BaseModel):
    template_id: str
    file_name: str
    rows: list[dict[str, object]]


class OrderReleaseTemplateCreateRequest(BaseModel):
    code: str
    name: str
    description: str = ""
    required_columns: list[str]
    optional_columns: list[str] = []
    defaults: dict[str, object] = {}


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


@router.post("/templates")
def create_template(
    payload: OrderReleaseTemplateCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_order_release_templates(db)
    template, issues = create_order_release_template(
        db,
        code=payload.code,
        name=payload.name,
        description=payload.description,
        required_columns=payload.required_columns,
        optional_columns=payload.optional_columns,
        defaults=payload.defaults,
        created_by=user.email,
    )
    if template is None:
        raise api_error(
            422,
            "ORDER_RELEASE_TEMPLATE_INVALID",
            "Order Release template contract is invalid.",
            {"issues": issues},
        )
    return serialize_order_release_template(template)


@router.get("/batches")
def list_batches(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batches = (
        db.query(OrderReleaseBatch)
        .order_by(OrderReleaseBatch.created_at.desc(), OrderReleaseBatch.id.desc())
        .limit(25)
        .all()
    )
    items = [serialize_order_release_batch(batch) for batch in batches]
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
    return {
        **payload,
        "job_id": job.id,
        "download_url": f"/api/v1/modules/order-release-generator/batches/{batch.id}/artifacts/{payload['artifact_id']}/download",
    }


@router.get("/batches/{batch_id}/artifacts")
def list_batch_xml_artifacts(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.get(OrderReleaseBatch, batch_id)
    if batch is None:
        raise api_error(404, "ORDER_RELEASE_BATCH_NOT_FOUND", "Order Release batch not found.")
    artifacts = list_batch_artifacts(db, batch.id)
    return {
        "batch_id": batch.id,
        "items": [serialize_order_release_artifact(artifact, batch.id) for artifact in artifacts],
        "total": len(artifacts),
    }


@router.get("/batches/{batch_id}/artifacts/{artifact_id}/download")
def download_batch_xml_artifact(
    batch_id: str,
    artifact_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.get(OrderReleaseBatch, batch_id)
    if batch is None:
        raise api_error(404, "ORDER_RELEASE_BATCH_NOT_FOUND", "Order Release batch not found.")
    artifact = next((item for item in list_batch_artifacts(db, batch.id) if item.id == artifact_id), None)
    if artifact is None:
        raise api_error(404, "ORDER_RELEASE_ARTIFACT_NOT_FOUND", "Order Release artifact not found.")
    path = Path(artifact.file_path)
    if not path.exists() or not path.is_file():
        raise api_error(404, "ORDER_RELEASE_ARTIFACT_FILE_NOT_FOUND", "Order Release artifact file not found.")
    actual_sha256, actual_size = file_sha256(path)
    if actual_sha256 != artifact.sha256:
        raise api_error(409, "ORDER_RELEASE_ARTIFACT_HASH_MISMATCH", "Order Release artifact hash mismatch.")
    db.add(
        AuditLog(
            actor_user_id=user.email,
            action="order_release_generator.artifact.download",
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
