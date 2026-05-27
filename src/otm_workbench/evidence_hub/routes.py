import hashlib
import json
import zipfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import ActiveContext, Artifact, AuditLog, DomainEvent, Evidence, Manifest, User, utcnow
from otm_workbench.platform.scoping import apply_operational_scope, operational_scope_from_context
from otm_workbench.platform.services import file_sha256, resolve_artifact_storage_path


router = APIRouter(prefix="/api/v1/evidence-hub", tags=["evidence-hub"])


class ArchivePackageRequest(BaseModel):
    source_module: str | None = None
    evidence_type: str | None = None
    status: str | None = None
    project_id: str | None = None
    sensitivity_level: str | None = None


def parse_json_object(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def json_bytes(payload: dict[str, object] | list[dict[str, object]]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def active_context_for_user(db: Session, user: User) -> ActiveContext | None:
    return db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()


def apply_evidence_visibility(query, db: Session, user: User):
    if user.is_admin:
        return query
    return apply_operational_scope(query, Evidence, operational_scope_from_context(active_context_for_user(db, user)))


def require_evidence_visible(db: Session, user: User, evidence: Evidence, *, code: str, message: str) -> None:
    if user.is_admin:
        return
    visible = apply_evidence_visibility(db.query(Evidence).filter(Evidence.id == evidence.id), db, user).first()
    if visible is None:
        raise api_error(403, code, message)


def entry_metadata(path: str, content: bytes) -> dict[str, object]:
    return {
        "path": path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
    }


def serialize_artifact_summary(artifact: Artifact | None) -> dict[str, object] | None:
    if artifact is None:
        return None
    return {
        "id": artifact.id,
        "project_id": artifact.project_id,
        "profile_id": artifact.profile_id,
        "environment_id": artifact.environment_id,
        "domain_name": artifact.domain_name,
        "visibility": artifact.visibility,
        "access_policy_id": artifact.access_policy_id,
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
        "project_id": manifest.project_id,
        "profile_id": manifest.profile_id,
        "environment_id": manifest.environment_id,
        "domain_name": manifest.domain_name,
        "visibility": manifest.visibility,
        "access_policy_id": manifest.access_policy_id,
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
        "profile_id": evidence.profile_id,
        "environment_id": evidence.environment_id,
        "domain_name": evidence.domain_name,
        "visibility": evidence.visibility,
        "access_policy_id": evidence.access_policy_id,
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


def client_safe_evidence_for_artifact(db: Session, artifact_id: str) -> Evidence | None:
    return (
        db.query(Evidence)
        .filter(Evidence.artifact_id == artifact_id)
        .filter(Evidence.client_safe.is_(True))
        .order_by(Evidence.created_at.desc())
        .first()
    )


def downloadable_artifact(db: Session, artifact_id: str) -> tuple[Artifact, Evidence]:
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    evidence = client_safe_evidence_for_artifact(db, artifact_id)
    if artifact is None or evidence is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return artifact, evidence


def archive_filters(payload: ArchivePackageRequest) -> dict[str, object]:
    return {
        "source_module": payload.source_module,
        "evidence_type": payload.evidence_type,
        "status": payload.status,
        "project_id": payload.project_id,
        "sensitivity_level": payload.sensitivity_level,
        "client_safe": True,
    }


def query_archive_evidence(db: Session, payload: ArchivePackageRequest, user: User) -> list[Evidence]:
    query = db.query(Evidence).filter(Evidence.client_safe.is_(True))
    if payload.source_module:
        query = query.filter(Evidence.source_module == payload.source_module)
    if payload.evidence_type:
        query = query.filter(Evidence.evidence_type == payload.evidence_type)
    if payload.status:
        query = query.filter(Evidence.status == payload.status)
    if payload.project_id:
        query = query.filter(Evidence.project_id == payload.project_id)
    if payload.sensitivity_level:
        query = query.filter(Evidence.sensitivity_level == payload.sensitivity_level)
    query = apply_evidence_visibility(query, db, user)
    return query.order_by(Evidence.created_at.desc()).all()


def unique_by_id(items: list[dict[str, object] | None]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    seen: set[object] = set()
    for item in items:
        if not item:
            continue
        item_id = item.get("id")
        if item_id in seen:
            continue
        seen.add(item_id)
        result.append(item)
    return result


def common_evidence_scope(evidence_items: list[Evidence]) -> dict[str, str | None]:
    if not evidence_items:
        return {
            "project_id": None,
            "profile_id": None,
            "environment_id": None,
            "domain_name": "PUBLIC",
            "visibility": "PUBLIC",
            "access_policy_id": None,
        }
    first = evidence_items[0]
    fields = {
        "project_id": first.project_id,
        "profile_id": first.profile_id,
        "environment_id": first.environment_id,
        "domain_name": first.domain_name,
        "visibility": first.visibility,
        "access_policy_id": first.access_policy_id,
    }
    for evidence in evidence_items[1:]:
        for key in ("project_id", "profile_id", "environment_id", "domain_name", "visibility", "access_policy_id"):
            if getattr(evidence, key) != fields[key]:
                raise api_error(
                    400,
                    "EVIDENCE_ARCHIVE_SCOPE_MISMATCH",
                    "Archive packages require all selected evidence to share the same operational scope.",
                )
    return fields


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
    query = apply_evidence_visibility(query, db, user)
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
    require_evidence_visible(
        db,
        user,
        evidence,
        code="EVIDENCE_FORBIDDEN",
        message="Evidence is not visible in the active context.",
    )
    return serialize_evidence_index_item(db, evidence)


@router.post("/archive-packages")
def create_archive_package(
    payload: ArchivePackageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    evidence_items = query_archive_evidence(db, payload, user)
    if not evidence_items:
        raise HTTPException(status_code=400, detail="No client-safe evidence matched the archive filters.")

    archive_scope = common_evidence_scope(evidence_items)
    evidence_index = [serialize_evidence_index_item(db, evidence) for evidence in evidence_items]
    artifact_index = unique_by_id([item["artifact"] for item in evidence_index])
    manifest_index = unique_by_id([item["manifest"] for item in evidence_index])
    filters = archive_filters(payload)
    generated_at = utcnow()
    timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")

    evidence_content = json_bytes(evidence_index)
    artifact_content = json_bytes(artifact_index)
    manifest_content = json_bytes(manifest_index)
    archive_manifest = {
        "schema_version": "evidence-hub-archive-manifest/v1",
        "manifest_type": "evidence_hub_archive",
        "source_module": "evidence_hub",
        "filters": filters,
        "files": [
            entry_metadata("evidence_index.json", evidence_content),
            entry_metadata("artifact_index.json", artifact_content),
            entry_metadata("manifest_index.json", manifest_content),
        ],
        "evidence_count": len(evidence_index),
        "artifact_ref_count": len(artifact_index),
        "manifest_ref_count": len(manifest_index),
        "generated_at": generated_at.isoformat(),
        "generated_by": user.email,
    }
    archive_manifest_content = json_bytes(archive_manifest)

    archive_dir = get_settings().artifact_root / "evidence_hub" / "archives" / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"evidence_hub_archive_{timestamp}.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("archive_manifest.json", archive_manifest_content)
        archive.writestr("evidence_index.json", evidence_content)
        archive.writestr("artifact_index.json", artifact_content)
        archive.writestr("manifest_index.json", manifest_content)

    sha256, size_bytes = file_sha256(str(archive_path))
    artifact = Artifact(
        project_id=archive_scope["project_id"],
        profile_id=archive_scope["profile_id"],
        environment_id=archive_scope["environment_id"],
        domain_name=archive_scope["domain_name"],
        visibility=archive_scope["visibility"] or "PRIVATE",
        access_policy_id=archive_scope["access_policy_id"],
        source_module="evidence_hub",
        artifact_type="evidence_hub_archive_zip",
        file_path=str(archive_path),
        file_name=archive_path.name,
        content_type="application/zip",
        sha256=sha256,
        size_bytes=size_bytes,
        sensitivity_level="internal",
    )
    db.add(artifact)
    db.flush()

    manifest = Manifest(
        project_id=archive_scope["project_id"],
        profile_id=archive_scope["profile_id"],
        environment_id=archive_scope["environment_id"],
        domain_name=archive_scope["domain_name"],
        visibility=archive_scope["visibility"] or "PRIVATE",
        access_policy_id=archive_scope["access_policy_id"],
        source_module="evidence_hub",
        status="CREATED",
        manifest_json=archive_manifest_content.decode("utf-8"),
    )
    db.add(manifest)
    db.flush()

    summary = {
        "source_entity_type": "evidence_hub_archive",
        "source_entity_id": artifact.id,
        "evidence_ids": [item["id"] for item in evidence_index],
        "evidence_count": len(evidence_index),
        "artifact_ref_count": len(artifact_index),
        "manifest_ref_count": len(manifest_index),
        "filters": filters,
        "artifact_type": "evidence_hub_archive_zip",
    }
    evidence = Evidence(
        project_id=archive_scope["project_id"],
        profile_id=archive_scope["profile_id"],
        environment_id=archive_scope["environment_id"],
        domain_name=archive_scope["domain_name"],
        visibility=archive_scope["visibility"] or "PRIVATE",
        access_policy_id=archive_scope["access_policy_id"],
        source_module="evidence_hub",
        evidence_type="evidence_hub_archive",
        summary_json=json.dumps(summary, sort_keys=True),
        artifact_id=artifact.id,
        manifest_id=manifest.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    db.add(
        AuditLog(
            actor_user_id=user.email,
            action="evidence_hub.archive_package.create",
            target_type="artifact",
            target_id=artifact.id,
            metadata_json=json.dumps(
                {
                    "artifact_id": artifact.id,
                    "manifest_id": manifest.id,
                    "evidence_id": evidence.id,
                    "evidence_count": len(evidence_index),
                    "artifact_ref_count": len(artifact_index),
                    "manifest_ref_count": len(manifest_index),
                    "filters": filters,
                    "project_id": archive_scope["project_id"],
                    "profile_id": archive_scope["profile_id"],
                    "environment_id": archive_scope["environment_id"],
                    "domain_name": archive_scope["domain_name"],
                    "visibility": archive_scope["visibility"],
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="evidence_hub.archive_package.created",
            source_module="evidence_hub",
            project_id=archive_scope["project_id"],
            aggregate_type="artifact",
            aggregate_id=artifact.id,
            payload_json=json.dumps(
                {
                    "artifact_id": artifact.id,
                    "manifest_id": manifest.id,
                    "evidence_id": evidence.id,
                    "evidence_count": len(evidence_index),
                },
                sort_keys=True,
            ),
            status="PENDING",
        )
    )
    db.commit()
    return {
        "archive_id": artifact.id,
        "artifact_id": artifact.id,
        "manifest_id": manifest.id,
        "evidence_id": evidence.id,
        "file_name": artifact.file_name,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "summary": summary,
    }


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    artifact, evidence = downloadable_artifact(db, artifact_id)
    require_evidence_visible(
        db,
        user,
        evidence,
        code="ARTIFACT_FORBIDDEN",
        message="Artifact is not visible in the active context.",
    )
    try:
        path = resolve_artifact_storage_path(artifact.file_path)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Artifact not found.") from exc
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact file not found.")

    actual_sha256, actual_size = file_sha256(str(path))
    if actual_sha256 != artifact.sha256:
        raise HTTPException(status_code=409, detail="Artifact hash mismatch.")

    db.add(
        AuditLog(
            actor_user_id=user.email,
            action="evidence_hub.artifact.download",
            target_type="artifact",
            target_id=artifact.id,
            metadata_json=json.dumps(
                {
                    "artifact_id": artifact.id,
                    "artifact_type": artifact.artifact_type,
                    "source_module": artifact.source_module,
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
