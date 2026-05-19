from pathlib import Path

from otm_workbench.models import AuditLog, Job, JobEvent


def test_create_job(client, admin_header):
    response = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "HEALTH_CHECK",
            "source_module": "platform",
            "project_id": "project_demo",
            "profile_id": "profile_demo",
            "environment_id": "env_demo",
            "domain_name": "OTM1",
            "input": {"ping": "ok"},
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "PENDING"
    assert payload["progress"] == 0
    assert payload["message"] == "Job created."
    assert payload["input"] == {"ping": "ok"}


def test_list_and_detail_jobs_return_client_safe_payload(client, admin_header):
    created = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "CATALOG_IMPORT_DATA_DICTIONARY",
            "source_module": "catalog",
            "project_id": "project_demo",
            "profile_id": "profile_demo",
            "environment_id": "env_demo",
            "domain_name": "OTM1",
            "input": {"source": "local_data_dictionary"},
        },
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/platform/jobs?source_module=catalog&status=PENDING", headers=admin_header)
    detail = client.get(f"/api/v1/platform/jobs/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert detail.json()["input"] == {"source": "local_data_dictionary"}
    assert "input_json" not in detail.json()


def test_list_jobs_filters_by_environment_and_domain(client, admin_header):
    first = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "CATALOG_IMPORT_DATA_DICTIONARY",
            "source_module": "catalog",
            "environment_id": "env_dev",
            "domain_name": "OTM1",
        },
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "CATALOG_IMPORT_DATA_DICTIONARY",
            "source_module": "catalog",
            "environment_id": "env_test",
            "domain_name": "OTM2",
        },
        headers=admin_header,
    )

    response = client.get(
        "/api/v1/platform/jobs?source_module=catalog&environment_id=env_dev&domain_name=otm1",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == first["id"]
    assert response.json()["items"][0]["environment_id"] == "env_dev"
    assert response.json()["items"][0]["domain_name"] == "OTM1"


def test_cancel_pending_job_records_event_and_audit(client, admin_header, db_session):
    created = client.post(
        "/api/v1/platform/jobs",
        json={"job_type": "CATALOG_IMPORT_DATA_DICTIONARY", "source_module": "catalog"},
        headers=admin_header,
    ).json()

    response = client.post(f"/api/v1/platform/jobs/{created['id']}/cancel", headers=admin_header)

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    job = db_session.query(Job).filter(Job.id == created["id"]).one()
    assert job.status == "CANCELLED"
    assert job.cancelled_at is not None
    event = db_session.query(JobEvent).filter(JobEvent.job_id == created["id"], JobEvent.event_type == "JOB_CANCELLED").one()
    assert event.status_before == "PENDING"
    assert event.status_after == "CANCELLED"
    audit = db_session.query(AuditLog).filter(AuditLog.action == "job.cancel").one()
    assert audit.target_id == created["id"]


def test_cancel_running_job_is_rejected(client, admin_header, db_session):
    created = client.post(
        "/api/v1/platform/jobs",
        json={"job_type": "CATALOG_IMPORT_DATA_DICTIONARY", "source_module": "catalog"},
        headers=admin_header,
    ).json()
    job = db_session.query(Job).filter(Job.id == created["id"]).one()
    job.status = "RUNNING"
    db_session.commit()

    response = client.post(f"/api/v1/platform/jobs/{created['id']}/cancel", headers=admin_header)

    assert response.status_code == 400
    assert "pending" in response.json()["message"].lower()


def test_demo_job_handler_runs_to_success_with_events(client, admin_header, db_session):
    response = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "input": {"value": "synthetic"},
            "execute_now": True,
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "SUCCEEDED"
    assert payload["progress"] == 100
    assert payload["result"] == {"echo": {"value": "synthetic"}}
    events = db_session.query(JobEvent).filter(JobEvent.job_id == payload["id"]).order_by(JobEvent.created_at).all()
    assert [event.event_type for event in events] == ["JOB_CREATED", "JOB_STARTED", "JOB_SUCCEEDED"]


def test_missing_job_handler_fails_safely(client, admin_header):
    response = client.post(
        "/api/v1/platform/jobs",
        json={"job_type": "UNKNOWN_HANDLER", "source_module": "platform", "execute_now": True},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "FAILED"
    assert payload["error"]["code"] == "JOB_HANDLER_NOT_REGISTERED"
    assert "UNKNOWN_HANDLER" not in payload["error"]["message"]


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
