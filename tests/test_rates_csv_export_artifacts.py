import json
from pathlib import Path
import zipfile

from otm_workbench.models import Artifact, AuditLog, Evidence, Manifest, RateBatch


def create_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    return client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic export batch", "domain_name": "OTM1"},
        headers=admin_header,
    ).json()


def add_accessorial_table(client, admin_header, batch_id):
    return client.post(
        f"/api/v1/modules/rates/batches/{batch_id}/tables",
        json={
            "tables": [
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": "OTM1.ACC_COST_001",
                            "ACCESSORIAL_COST_XID": "ACC_COST_001",
                        }
                    ],
                }
            ]
        },
        headers=admin_header,
    )


def test_export_rejects_unvalidated_batch(client, admin_header):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "validated" in response.json()["message"].lower()


def test_export_rejects_batch_with_error_issues(client, admin_header):
    batch = create_batch(client, admin_header, scenario_code="RATE_GEO_ONLY")
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "error" in response.json()["message"].lower()


def test_export_creates_zip_with_manifest_and_csv(client, admin_header):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    preview = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview",
        headers=admin_header,
    )
    assert preview.status_code == 200

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    zip_path = Path(payload["file_path"])
    assert zip_path.exists()
    assert payload["file_name"].endswith(".zip")
    assert payload["tables"] == ["ACCESSORIAL_COST"]

    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        assert "manifest.json" in names
        assert "csv/001_ACCESSORIAL_COST.csv" in names
        csv_text = archive.read("csv/001_ACCESSORIAL_COST.csv").decode("utf-8")
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

    assert csv_text.splitlines()[0] == "ACCESSORIAL_COST"
    assert csv_text.splitlines()[1].startswith("ACCESSORIAL_COST_GID")
    assert manifest["manifest_type"] == "rates_csv_export"
    assert manifest["batch"]["id"] == batch["id"]
    assert "OTM1.ACC_COST_001" not in json.dumps(manifest)


def test_export_registers_artifact_manifest_evidence_and_audit(client, admin_header, db_session):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    artifact = db_session.query(Artifact).filter(Artifact.id == payload["artifact_id"]).one()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "rates.batch.export_csv").one()
    refreshed_batch = db_session.query(RateBatch).filter(RateBatch.id == batch["id"]).one()

    assert artifact.artifact_type == "rates_csv_zip"
    assert artifact.content_type == "application/zip"
    assert artifact.sha256 == payload["sha256"]
    assert manifest.source_module == "rates"
    assert "OTM1.ACC_COST_001" not in manifest.manifest_json
    assert evidence.client_safe is True
    assert evidence.artifact_id == artifact.id
    assert evidence.manifest_id == manifest.id
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert audit.target_id == batch["id"]
    assert refreshed_batch.status == "EXPORTED"
    assert refreshed_batch.exported_at is not None


def test_batch_artifacts_and_evidence_endpoints_return_export_records(client, admin_header):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    export = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    ).json()

    artifacts = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/artifacts",
        headers=admin_header,
    )
    evidence = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/evidence",
        headers=admin_header,
    )

    assert artifacts.status_code == 200
    assert evidence.status_code == 200
    assert artifacts.json()["items"][0]["id"] == export["artifact_id"]
    assert evidence.json()["items"][0]["id"] == export["evidence_id"]
    assert "OTM1.ACC_COST_001" not in str(evidence.json())


def test_batch_artifact_download_returns_zip_and_audit(client, admin_header, db_session):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    export = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    ).json()

    response = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/artifacts/{export['artifact_id']}/download",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.content.startswith(b"PK")
    assert response.headers["content-type"] == "application/zip"
    assert export["file_name"] in response.headers["content-disposition"]
    assert response.headers["x-artifact-sha256"] == export["sha256"]
    audit = db_session.query(AuditLog).filter_by(action="rates.batch.artifact.download").one()
    assert audit.target_type == "artifact"
    assert audit.target_id == export["artifact_id"]
    assert batch["id"] in audit.metadata_json
    assert "OTM1.ACC_COST_001" not in audit.metadata_json
    assert export["file_path"] not in audit.metadata_json


def test_batch_artifact_download_rejects_artifact_from_another_batch_without_path(
    client,
    admin_header,
):
    first_batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, first_batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{first_batch['id']}/csv-preview", headers=admin_header)
    export = client.post(
        f"/api/v1/modules/rates/batches/{first_batch['id']}/export-csv",
        headers=admin_header,
    ).json()
    second_batch = create_batch(client, admin_header)

    response = client.get(
        f"/api/v1/modules/rates/batches/{second_batch['id']}/artifacts/{export['artifact_id']}/download",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert export["file_path"] not in str(response.json())


def test_batch_artifact_download_rejects_hash_mismatch_without_path(
    client,
    admin_header,
    db_session,
):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    export = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    ).json()
    artifact = db_session.query(Artifact).filter_by(id=export["artifact_id"]).one()
    Path(artifact.file_path).write_text("changed synthetic artifact", encoding="utf-8")

    response = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/artifacts/{export['artifact_id']}/download",
        headers=admin_header,
    )

    assert response.status_code == 409
    assert export["file_path"] not in str(response.json())
