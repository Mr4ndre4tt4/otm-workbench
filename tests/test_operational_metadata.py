from pathlib import Path


def test_create_job(client, admin_header):
    response = client.post(
        "/api/v1/platform/jobs",
        json={"job_type": "health_check", "source_module": "platform", "input_json": "{}"},
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"

def test_artifact_hash_metadata_and_evidence_are_client_safe(client, admin_header):
    artifact_dir = Path("var/test-artifacts")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_file = artifact_dir / "sample.txt"
    artifact_file.write_text("safe sample", encoding="utf-8")

    artifact = client.post(
        "/api/v1/platform/artifacts",
        json={
            "source_module": "platform",
            "artifact_type": "sample",
            "file_path": str(artifact_file),
            "file_name": "sample.txt",
            "content_type": "text/plain",
            "sensitivity_level": "internal",
        },
        headers=admin_header,
    )
    assert artifact.status_code == 200
    assert len(artifact.json()["sha256"]) == 64

    evidence = client.post(
        "/api/v1/platform/evidence",
        json={
            "source_module": "platform",
            "evidence_type": "sample",
            "summary_json": '{"status":"ok"}',
            "artifact_id": artifact.json()["id"],
        },
        headers=admin_header,
    )
    assert evidence.status_code == 200
    assert evidence.json()["client_safe"] is True
    assert "safe sample" not in str(evidence.json())


def test_audit_log_records_feature_flag_change(client, admin_header):
    client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=admin_header,
    )

    response = client.get("/api/v1/platform/audit-logs", headers=admin_header)
    assert response.status_code == 200
    assert any(item["action"] == "feature_flag.upsert" for item in response.json()["items"])
