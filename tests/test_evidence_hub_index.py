import json
from pathlib import Path

from otm_workbench.models import Evidence


def test_evidence_hub_list_requires_authentication(client):
    response = client.get("/api/v1/evidence-hub/evidence")

    assert response.status_code == 401


def test_evidence_hub_list_returns_empty_page(client, admin_header):
    response = client.get("/api/v1/evidence-hub/evidence", headers=admin_header)

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def create_platform_evidence(client, admin_header):
    artifact_dir = Path("var/test-artifacts/evidence-hub")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_file = artifact_dir / "demo.txt"
    artifact_file.write_text("OTM1.ACC_COST_001 should not be exposed", encoding="utf-8")
    artifact = client.post(
        "/api/v1/platform/artifacts",
        json={
            "source_module": "rates",
            "artifact_type": "rates_csv_zip",
            "file_path": str(artifact_file),
            "file_name": "demo.zip",
            "content_type": "application/zip",
            "sensitivity_level": "internal",
        },
        headers=admin_header,
    )
    assert artifact.status_code == 200
    manifest = client.post(
        "/api/v1/platform/manifests",
        json={
            "source_module": "rates",
            "status": "CREATED",
            "manifest_json": json.dumps(
                {
                    "schema_version": "rates-csv-export-manifest/v1",
                    "manifest_type": "rates_csv_export",
                    "raw_value": "OTM1.ACC_COST_001",
                },
                sort_keys=True,
            ),
        },
        headers=admin_header,
    )
    assert manifest.status_code == 200
    evidence = client.post(
        "/api/v1/platform/evidence",
        json={
            "source_module": "rates",
            "evidence_type": "rates_csv_export",
            "summary_json": json.dumps({"status": "ok", "note_present": True}, sort_keys=True),
            "artifact_id": artifact.json()["id"],
            "manifest_id": manifest.json()["id"],
        },
        headers=admin_header,
    )
    assert evidence.status_code == 200
    return evidence.json()["id"], artifact.json()["id"], manifest.json()["id"]


def test_evidence_hub_detail_returns_linked_summaries_without_sensitive_fields(client, admin_header):
    evidence_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)

    response = client.get(f"/api/v1/evidence-hub/evidence/{evidence_id}", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == evidence_id
    assert payload["summary"] == {"note_present": True, "status": "ok"}
    assert payload["artifact"]["id"] == artifact_id
    assert payload["artifact"]["file_name"] == "demo.zip"
    assert "file_path" not in payload["artifact"]
    assert payload["manifest"]["id"] == manifest_id
    assert payload["manifest"]["manifest_type"] == "rates_csv_export"
    assert payload["manifest"]["schema_version"] == "rates-csv-export-manifest/v1"
    assert "manifest_json" not in payload["manifest"]
    assert "OTM1.ACC_COST_001" not in str(payload)


def test_evidence_hub_detail_rejects_missing_evidence(client, admin_header):
    response = client.get("/api/v1/evidence-hub/evidence/missing_evidence", headers=admin_header)

    assert response.status_code == 404


def test_evidence_hub_list_filters_by_metadata(client, admin_header):
    evidence_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)

    response = client.get(
        "/api/v1/evidence-hub/evidence",
        params={
            "source_module": "rates",
            "evidence_type": "rates_csv_export",
            "status": "CREATED",
            "sensitivity_level": "client_safe",
            "artifact_id": artifact_id,
            "manifest_id": manifest_id,
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == evidence_id


def test_evidence_hub_list_defaults_to_client_safe_only(client, admin_header, db_session):
    safe_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)
    unsafe = Evidence(
        source_module="rates",
        evidence_type="rates_csv_export",
        summary_json='{"status":"unsafe"}',
        artifact_id=artifact_id,
        manifest_id=manifest_id,
        client_safe=False,
        sensitivity_level="internal",
    )
    db_session.add(unsafe)
    db_session.commit()

    default_response = client.get("/api/v1/evidence-hub/evidence", headers=admin_header)
    unsafe_response = client.get(
        "/api/v1/evidence-hub/evidence",
        params={"client_safe": "false"},
        headers=admin_header,
    )

    assert default_response.status_code == 200
    assert [item["id"] for item in default_response.json()["items"]] == [safe_id]
    assert unsafe_response.status_code == 200
    assert unsafe_response.json()["items"][0]["id"] == unsafe.id
