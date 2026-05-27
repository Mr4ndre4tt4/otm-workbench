from pathlib import Path
import json

from sqlalchemy.orm import Session

from otm_workbench.models import Artifact, Evidence, OrderReleaseBatch, OrderReleaseBatchRow
from otm_workbench.modules.order_release_generator.xml_preview import build_order_release_xml
from otm_workbench.modules.rates.exports import file_sha256, utc_timestamp


def generate_order_release_xml_artifact(
    db: Session,
    *,
    batch: OrderReleaseBatch,
    rows: list[OrderReleaseBatchRow],
    artifact_root: Path,
) -> dict[str, object]:
    preview = build_order_release_xml(batch, rows)
    export_dir = artifact_root / "order_release_generator" / batch.id / "xml_exports" / utc_timestamp()
    export_dir.mkdir(parents=True, exist_ok=True)
    xml_path = export_dir / "db.xml"
    xml_path.write_text(str(preview["xml"]), encoding="utf-8")
    digest, size = file_sha256(xml_path)
    artifact = Artifact(
        project_id=batch.project_id,
        environment_id=batch.environment_id,
        profile_id=batch.profile_id,
        domain_name=batch.domain_name,
        visibility="PROJECT",
        source_module="order_release_generator",
        artifact_type="order_release_xml",
        file_path=str(xml_path),
        file_name=xml_path.name,
        content_type="application/xml",
        sha256=digest,
        size_bytes=size,
        sensitivity_level="internal",
    )
    db.add(artifact)
    db.flush()
    evidence = Evidence(
        project_id=batch.project_id,
        environment_id=batch.environment_id,
        profile_id=batch.profile_id,
        domain_name=batch.domain_name,
        visibility="PROJECT",
        source_module="order_release_generator",
        evidence_type="order_release_xml_generated",
        summary_json=json.dumps(
            {
                "source_entity_type": "order_release_batch",
                "source_entity_id": batch.id,
                "artifact_type": artifact.artifact_type,
                "file_name": artifact.file_name,
                "release_count": preview["release_count"],
                "line_count": preview["line_count"],
                "sha256": digest,
                "size_bytes": size,
            },
            sort_keys=True,
        ),
        artifact_id=artifact.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.commit()
    db.refresh(artifact)
    db.refresh(evidence)
    return {
        "batch_id": batch.id,
        "artifact_id": artifact.id,
        "evidence_id": evidence.id,
        "file_name": artifact.file_name,
        "file_path": artifact.file_path,
        "content_type": artifact.content_type,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "release_count": preview["release_count"],
        "line_count": preview["line_count"],
    }
