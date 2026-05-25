import json

from sqlalchemy.orm import Session

from otm_workbench.models import Artifact, Evidence, MasterDataBatch

REQUIRED_CAPABILITY = "master_data.submit_otm"
RECOMMENDED_TRANSPORT = "CSVUTIL_UPLOAD_OR_INTEGRATION"
OFFICIAL_SOURCE_BASIS = [
    "Oracle inbound integration supports HTTP POST, REST JSON, and SOAP.",
    "REST should be preferred where possible; Transmission XML remains for gaps.",
    "DB.XML is privileged and bypasses full business-context validation.",
]


def _json_loads(value: str, fallback):
    try:
        return json.loads(value or "")
    except json.JSONDecodeError:
        return fallback


def _evidence_batch_id(evidence: Evidence) -> str | None:
    summary = _json_loads(evidence.summary_json, {})
    if isinstance(summary, dict):
        return summary.get("source_entity_id")
    return None


def _master_data_export_artifact(db: Session, batch_id: str) -> Artifact | None:
    rows = (
        db.query(Artifact, Evidence)
        .join(Evidence, Evidence.artifact_id == Artifact.id)
        .filter(Artifact.source_module == "master_data")
        .filter(Artifact.artifact_type == "master_data_csv_zip")
        .filter(Evidence.source_module == "master_data")
        .filter(Evidence.evidence_type == "master_data_csv_export")
        .filter(Evidence.client_safe.is_(True))
        .order_by(Artifact.created_at.desc())
        .all()
    )
    for artifact, evidence in rows:
        if _evidence_batch_id(evidence) == batch_id:
            return artifact
    return None


def build_master_data_otm_import_readiness(db: Session, batch: MasterDataBatch) -> dict[str, object]:
    blockers: list[dict[str, str]] = []
    artifact_payload = None
    export_artifact = _master_data_export_artifact(db, batch.id)
    if batch.status != "EXPORTED" or export_artifact is None:
        blockers.append(
            {
                "code": "MASTER_DATA_EXPORT_REQUIRED",
                "message": "Build CSV and export the Master Data package before direct import readiness can be evaluated.",
            }
        )
    else:
        artifact_payload = {
            "artifact_id": export_artifact.id,
            "file_name": export_artifact.file_name,
            "sha256": export_artifact.sha256,
            "content_type": export_artifact.content_type,
        }
        blockers.extend(
            [
                {
                    "code": "OTM_CONNECTION_NOT_CONFIGURED",
                    "message": "No governed OTM connection profile is configured for this environment.",
                },
                {
                    "code": "OTM_CREDENTIALS_NOT_CONFIGURED",
                    "message": "No governed OTM credential reference is configured for this environment.",
                },
                {
                    "code": "OTM_SUBMIT_CAPABILITY_DISABLED",
                    "message": "Direct Master Data OTM submit capability is not enabled.",
                },
            ]
        )

    blocked_for_export = any(blocker["code"] == "MASTER_DATA_EXPORT_REQUIRED" for blocker in blockers)
    return {
        "batch_id": batch.id,
        "status": "BLOCKED" if blocked_for_export else "GUARDED",
        "ready": False,
        "required_capability": REQUIRED_CAPABILITY,
        "recommended_transport": RECOMMENDED_TRANSPORT,
        "official_source_basis": OFFICIAL_SOURCE_BASIS,
        "blockers": blockers,
        "artifact": artifact_payload,
    }
