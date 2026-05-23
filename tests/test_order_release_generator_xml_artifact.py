from pathlib import Path

from otm_workbench.models import Artifact, AuditLog, Evidence
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
    assert payload["download_url"].endswith(
        f"/api/v1/modules/order-release-generator/batches/{batch['id']}/artifacts/{payload['artifact_id']}/download"
    )
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


def test_order_release_xml_artifacts_are_listed_and_downloadable(client, admin_header, db_session):
    batch = create_batch(client, admin_header)
    generated = client.post(
        f"/api/v1/modules/order-release-generator/batches/{batch['id']}/generate-xml-artifact",
        headers=admin_header,
    ).json()

    artifacts = client.get(
        f"/api/v1/modules/order-release-generator/batches/{batch['id']}/artifacts",
        headers=admin_header,
    )
    download = client.get(generated["download_url"], headers=admin_header)

    assert artifacts.status_code == 200
    artifact_payload = artifacts.json()["items"][0]
    assert artifact_payload["id"] == generated["artifact_id"]
    assert artifact_payload["download_url"] == generated["download_url"]
    assert "file_path" not in artifact_payload
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/xml"
    assert download.headers["x-artifact-sha256"] == generated["sha256"]
    assert b"<Transmission>" in download.content
    audit = db_session.query(AuditLog).filter_by(action="order_release_generator.artifact.download").one()
    assert audit.target_id == generated["artifact_id"]
    assert batch["id"] in audit.metadata_json


def test_order_release_xml_artifact_download_rejects_cross_batch_artifact(client, admin_header):
    first_batch = create_batch(client, admin_header)
    second_batch = create_batch(client, admin_header)
    generated = client.post(
        f"/api/v1/modules/order-release-generator/batches/{first_batch['id']}/generate-xml-artifact",
        headers=admin_header,
    ).json()

    response = client.get(
        f"/api/v1/modules/order-release-generator/batches/{second_batch['id']}/artifacts/{generated['artifact_id']}/download",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "ORDER_RELEASE_ARTIFACT_NOT_FOUND"
