from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import Artifact, IntegrationDefinition, IntegrationPayloadArtifact, User
from otm_workbench.modules.integration_mapping.systems import reject_secret_like_payload
from otm_workbench.modules.rates.exports import file_sha256, utc_timestamp


SUPPORTED_FORMATS = {
    "XML": "application/xml",
    "JSON": "application/json",
}


def safe_file_name(value: str, payload_format: str) -> str:
    cleaned = Path(value.strip()).name
    if cleaned:
        return cleaned
    return f"payload.{payload_format.lower()}"


def import_payload_artifact(
    db: Session,
    *,
    definition: IntegrationDefinition,
    payload: dict[str, object],
    artifact_root: Path,
    user: User,
) -> IntegrationPayloadArtifact:
    reject_secret_like_payload(payload)
    payload_format = str(payload["payload_format"]).strip().upper()
    if payload_format not in SUPPORTED_FORMATS:
        raise ValueError("payload_format_unsupported")
    content = str(payload["content"])
    file_name = safe_file_name(str(payload.get("file_name") or ""), payload_format)
    export_dir = artifact_root / "integration_mapping" / definition.id / "payloads" / utc_timestamp()
    export_dir.mkdir(parents=True, exist_ok=True)
    payload_path = export_dir / file_name
    payload_path.write_text(content, encoding="utf-8")
    digest, size = file_sha256(payload_path)
    artifact = Artifact(
        source_module="integration_mapping",
        artifact_type="integration_payload_sample",
        file_path=str(payload_path),
        file_name=file_name,
        content_type=SUPPORTED_FORMATS[payload_format],
        sha256=digest,
        size_bytes=size,
        sensitivity_level="internal",
    )
    db.add(artifact)
    db.flush()
    payload_artifact = IntegrationPayloadArtifact(
        definition_id=definition.id,
        artifact_id=artifact.id,
        payload_role=str(payload["payload_role"]).strip().upper(),
        payload_format=payload_format,
        file_name=file_name,
        description=str(payload.get("description") or "").strip(),
        created_by=user.email,
    )
    db.add(payload_artifact)
    db.commit()
    db.refresh(payload_artifact)
    return payload_artifact


def serialize_payload_artifact(payload_artifact: IntegrationPayloadArtifact, artifact: Artifact) -> dict[str, object]:
    return {
        "id": payload_artifact.id,
        "definition_id": payload_artifact.definition_id,
        "artifact_id": payload_artifact.artifact_id,
        "payload_role": payload_artifact.payload_role,
        "payload_format": payload_artifact.payload_format,
        "file_name": payload_artifact.file_name,
        "description": payload_artifact.description,
        "content_type": artifact.content_type,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "created_by": payload_artifact.created_by,
        "created_at": payload_artifact.created_at.isoformat() if payload_artifact.created_at else None,
        "updated_at": payload_artifact.updated_at.isoformat() if payload_artifact.updated_at else None,
    }
