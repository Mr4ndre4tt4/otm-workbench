from pathlib import Path

from otm_workbench.models import Artifact, Evidence
from tests.test_order_release_generator_batches import valid_rows
from tests.test_order_release_generator_xml_preview import create_batch


def test_generate_order_release_xml_artifact_writes_db_xml(client, admin_header, db_session):
    batch = create_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/order-release-generator/batches/{batch['id']}/generate-xml-artifact",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    artifact = db_session.get(Artifact, payload["artifact_id"])
    evidence = db_session.get(Evidence, payload["evidence_id"])
    assert payload["batch_id"] == batch["id"]
    assert payload["file_name"] == "db.xml"
    assert payload["content_type"] == "application/xml"
    assert payload["release_count"] == 2
    assert payload["line_count"] == 3
    assert artifact is not None
    assert artifact.source_module == "order_release_generator"
    assert artifact.artifact_type == "order_release_xml"
    assert artifact.file_name == "db.xml"
    assert artifact.sha256 == payload["sha256"]
    assert artifact.size_bytes == payload["size_bytes"]
    assert evidence is not None
    assert evidence.source_module == "order_release_generator"
    assert evidence.evidence_type == "order_release_xml_generated"
    assert evidence.artifact_id == artifact.id
    assert evidence.client_safe is True
    assert "<Transmission>" not in evidence.summary_json
    assert "OR_SYN_001" not in evidence.summary_json
    xml_path = Path(payload["file_path"])
    assert xml_path.exists()
    xml_text = xml_path.read_text(encoding="utf-8")
    assert "<Transmission>" in xml_text
    assert "OR_SYN_001" in xml_text
    assert "cliente" not in xml_text.lower()
    assert "customer" not in xml_text.lower()


def test_generate_order_release_xml_artifact_rejects_invalid_batch(client, admin_header):
    rows = valid_rows()
    rows[0].pop("release_gid")
    batch = create_batch(client, admin_header, rows)

    response = client.post(
        f"/api/v1/modules/order-release-generator/batches/{batch['id']}/generate-xml-artifact",
        headers=admin_header,
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ORDER_RELEASE_BATCH_INVALID"
