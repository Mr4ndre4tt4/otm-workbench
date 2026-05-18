import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import Artifact, Evidence, Manifest, User


router = APIRouter(prefix="/api/v1/evidence-hub", tags=["evidence-hub"])


def parse_json_object(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def serialize_artifact_summary(artifact: Artifact | None) -> dict[str, object] | None:
    if artifact is None:
        return None
    return {
        "id": artifact.id,
        "source_module": artifact.source_module,
        "artifact_type": artifact.artifact_type,
        "file_name": artifact.file_name,
        "content_type": artifact.content_type,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "sensitivity_level": artifact.sensitivity_level,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
    }


def serialize_manifest_summary(manifest: Manifest | None) -> dict[str, object] | None:
    if manifest is None:
        return None
    manifest_payload = parse_json_object(manifest.manifest_json)
    return {
        "id": manifest.id,
        "source_module": manifest.source_module,
        "status": manifest.status,
        "manifest_type": manifest_payload.get("manifest_type"),
        "schema_version": manifest_payload.get("schema_version"),
        "created_at": manifest.created_at.isoformat() if manifest.created_at else None,
    }


def serialize_evidence_index_item(db: Session, evidence: Evidence) -> dict[str, object]:
    artifact = db.query(Artifact).filter(Artifact.id == evidence.artifact_id).first() if evidence.artifact_id else None
    manifest = db.query(Manifest).filter(Manifest.id == evidence.manifest_id).first() if evidence.manifest_id else None
    return {
        "id": evidence.id,
        "project_id": evidence.project_id,
        "source_module": evidence.source_module,
        "evidence_type": evidence.evidence_type,
        "status": evidence.status,
        "summary": parse_json_object(evidence.summary_json),
        "artifact": serialize_artifact_summary(artifact),
        "manifest": serialize_manifest_summary(manifest),
        "client_safe": evidence.client_safe,
        "sensitivity_level": evidence.sensitivity_level,
        "created_at": evidence.created_at.isoformat() if evidence.created_at else None,
    }


@router.get("/evidence")
def list_evidence(
    source_module: str | None = None,
    evidence_type: str | None = None,
    status: str | None = None,
    project_id: str | None = None,
    client_safe: bool = True,
    sensitivity_level: str | None = None,
    artifact_id: str | None = None,
    manifest_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(Evidence).filter(Evidence.client_safe.is_(client_safe))
    if source_module:
        query = query.filter(Evidence.source_module == source_module)
    if evidence_type:
        query = query.filter(Evidence.evidence_type == evidence_type)
    if status:
        query = query.filter(Evidence.status == status)
    if project_id:
        query = query.filter(Evidence.project_id == project_id)
    if sensitivity_level:
        query = query.filter(Evidence.sensitivity_level == sensitivity_level)
    if artifact_id:
        query = query.filter(Evidence.artifact_id == artifact_id)
    if manifest_id:
        query = query.filter(Evidence.manifest_id == manifest_id)
    items = query.order_by(Evidence.created_at.desc()).all()
    return PageResponse(items=[serialize_evidence_index_item(db, item) for item in items], total=len(items))


@router.get("/evidence/{evidence_id}")
def get_evidence_detail(
    evidence_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found.")
    return serialize_evidence_index_item(db, evidence)
