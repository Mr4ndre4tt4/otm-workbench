import json

from otm_workbench.config import get_settings
from otm_workbench.models import (
    AccessPolicy,
    AuditLog,
    Capability,
    Job,
    JobEvent,
    Role,
    RoleCapability,
    SessionToken,
    UserProjectRole,
)


def create_platform_scope(client, admin_header, *, prefix: str = "Metadata"):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": f"{prefix} Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": f"{prefix} Project"},
        headers=admin_header,
    ).json()
    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Default"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    return project, profile, environment


def test_create_job(client, admin_header, db_session):
    project, profile, environment = create_platform_scope(client, admin_header, prefix="Create Job")
    response = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "HEALTH_CHECK",
            "source_module": "platform",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
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
    audit = db_session.query(AuditLog).filter(AuditLog.action == "job.create").one()
    audit_metadata = json.loads(audit.metadata_json)
    assert audit_metadata["project_id"] == project["id"]
    assert audit_metadata["profile_id"] == profile["id"]
    assert audit_metadata["environment_id"] == environment["id"]
    assert audit_metadata["domain_name"] == "OTM1"


def test_platform_artifacts_manifests_and_evidence_preserve_scope(client, admin_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Metadata Scope Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Metadata Scope Project"},
        headers=admin_header,
    ).json()
    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Default"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    policy = client.post(
        "/api/v1/platform/access-policies",
        json={
            "project_id": project["id"],
            "name": "Rates evidence policy",
            "visibility": "PROJECT",
            "domain_name": "otm1",
            "rule_json": "{\"mode\":\"domain_role\"}",
        },
        headers=admin_header,
    ).json()
    artifact_path = get_settings().artifact_root / "test-artifacts" / "scoped-platform-artifact.txt"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("synthetic scoped artifact", encoding="utf-8")

    artifact = client.post(
        "/api/v1/platform/artifacts",
        json={
            "source_module": "rates",
            "artifact_type": "rates_csv_zip",
            "file_path": str(artifact_path),
            "file_name": "scoped-platform-artifact.zip",
            "content_type": "application/zip",
            "sensitivity_level": "internal",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
            "visibility": "PROJECT",
            "access_policy_id": policy["id"],
        },
        headers=admin_header,
    )
    manifest = client.post(
        "/api/v1/platform/manifests",
        json={
            "source_module": "rates",
            "status": "CREATED",
            "manifest_json": '{"status":"ok"}',
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
            "visibility": "PROJECT",
            "access_policy_id": policy["id"],
        },
        headers=admin_header,
    )
    evidence = client.post(
        "/api/v1/platform/evidence",
        json={
            "source_module": "rates",
            "evidence_type": "rates_csv_export",
            "summary_json": '{"status":"ok"}',
            "artifact_id": artifact.json()["id"],
            "manifest_id": manifest.json()["id"],
        },
        headers=admin_header,
    )

    assert artifact.status_code == 200
    assert manifest.status_code == 200
    assert evidence.status_code == 200
    assert artifact.json()["domain_name"] == "OTM1"
    assert manifest.json()["environment_id"] == environment["id"]
    assert evidence.json()["project_id"] == project["id"]
    assert evidence.json()["profile_id"] == profile["id"]
    assert evidence.json()["environment_id"] == environment["id"]
    assert evidence.json()["domain_name"] == "OTM1"
    assert evidence.json()["visibility"] == "PROJECT"
    assert evidence.json()["access_policy_id"] == policy["id"]


def test_platform_artifact_rejects_access_policy_outside_record_scope(client, admin_header, db_session):
    artifact_path = get_settings().artifact_root / "test-artifacts" / "cross-policy-platform-artifact.txt"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("synthetic scoped artifact", encoding="utf-8")
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Cross Policy Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Artifact Project"},
        headers=admin_header,
    ).json()
    other_project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Other Artifact Project"},
        headers=admin_header,
    ).json()
    policy = AccessPolicy(
        project_id=other_project["id"],
        name="Other project evidence policy",
        visibility="PROJECT",
        domain_name="OTM1",
        rule_json="{\"mode\":\"domain_role\"}",
    )
    db_session.add(policy)
    db_session.commit()

    missing_policy = client.post(
        "/api/v1/platform/artifacts",
        json={
            "source_module": "rates",
            "artifact_type": "rates_csv_zip",
            "file_path": str(artifact_path),
            "file_name": "missing-policy.zip",
            "content_type": "application/zip",
            "project_id": project["id"],
            "domain_name": "otm1",
            "visibility": "PROJECT",
            "access_policy_id": "missing_policy",
        },
        headers=admin_header,
    )
    cross_project_policy = client.post(
        "/api/v1/platform/artifacts",
        json={
            "source_module": "rates",
            "artifact_type": "rates_csv_zip",
            "file_path": str(artifact_path),
            "file_name": "cross-project-policy.zip",
            "content_type": "application/zip",
            "project_id": project["id"],
            "domain_name": "otm1",
            "visibility": "PROJECT",
            "access_policy_id": policy.id,
        },
        headers=admin_header,
    )

    assert missing_policy.status_code == 400
    assert missing_policy.json()["code"] == "ACCESS_POLICY_NOT_FOUND"
    assert cross_project_policy.status_code == 400
    assert cross_project_policy.json()["code"] == "ACCESS_POLICY_SCOPE_MISMATCH"


def test_platform_records_reject_mismatched_profile_and_environment_scope(client, admin_header):
    artifact_path = get_settings().artifact_root / "test-artifacts" / "mismatched-scope-platform-artifact.txt"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("synthetic scoped artifact", encoding="utf-8")
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Record Scope Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Record Scope Project"},
        headers=admin_header,
    ).json()
    other_project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Other Record Scope Project"},
        headers=admin_header,
    ).json()
    other_profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": other_project["id"], "name": "Other Default"},
        headers=admin_header,
    ).json()
    other_environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": other_project["id"], "name": "Other DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()

    mismatched_artifact = client.post(
        "/api/v1/platform/artifacts",
        json={
            "source_module": "rates",
            "artifact_type": "rates_csv_zip",
            "file_path": str(artifact_path),
            "file_name": "mismatched-scope.zip",
            "content_type": "application/zip",
            "project_id": project["id"],
            "profile_id": other_profile["id"],
            "environment_id": other_environment["id"],
            "domain_name": "otm1",
            "visibility": "PROJECT",
        },
        headers=admin_header,
    )
    mismatched_manifest = client.post(
        "/api/v1/platform/manifests",
        json={
            "source_module": "rates",
            "status": "CREATED",
            "manifest_json": '{"status":"ok"}',
            "project_id": project["id"],
            "profile_id": other_profile["id"],
            "domain_name": "otm1",
            "visibility": "PROJECT",
        },
        headers=admin_header,
    )
    missing_project_evidence = client.post(
        "/api/v1/platform/evidence",
        json={
            "source_module": "rates",
            "evidence_type": "rates_csv_export",
            "summary_json": '{"status":"ok"}',
            "profile_id": other_profile["id"],
            "domain_name": "otm1",
            "visibility": "PROJECT",
        },
        headers=admin_header,
    )

    assert mismatched_artifact.status_code == 400
    assert mismatched_artifact.json()["code"] == "OPERATIONAL_SCOPE_PROFILE_PROJECT_MISMATCH"
    assert mismatched_manifest.status_code == 400
    assert mismatched_manifest.json()["code"] == "OPERATIONAL_SCOPE_PROFILE_PROJECT_MISMATCH"
    assert missing_project_evidence.status_code == 400
    assert missing_project_evidence.json()["code"] == "OPERATIONAL_SCOPE_PROJECT_REQUIRED"


def test_platform_public_artifact_makes_public_scope_explicit(client, admin_header):
    artifact_path = get_settings().artifact_root / "test-artifacts" / "public-platform-artifact.txt"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("synthetic public artifact", encoding="utf-8")

    artifact = client.post(
        "/api/v1/platform/artifacts",
        json={
            "source_module": "platform",
            "artifact_type": "public_fixture",
            "file_path": str(artifact_path),
            "file_name": "public-platform-artifact.txt",
            "content_type": "text/plain",
            "sensitivity_level": "client_safe",
            "visibility": "PUBLIC",
        },
        headers=admin_header,
    )
    evidence = client.post(
        "/api/v1/platform/evidence",
        json={
            "source_module": "platform",
            "evidence_type": "public_fixture",
            "summary_json": '{"status":"ok"}',
            "artifact_id": artifact.json()["id"],
        },
        headers=admin_header,
    )

    assert artifact.status_code == 200
    assert evidence.status_code == 200
    assert artifact.json()["project_id"] is None
    assert artifact.json()["environment_id"] is None
    assert artifact.json()["domain_name"] == "PUBLIC"
    assert artifact.json()["visibility"] == "PUBLIC"
    assert evidence.json()["project_id"] is None
    assert evidence.json()["environment_id"] is None
    assert evidence.json()["domain_name"] == "PUBLIC"
    assert evidence.json()["visibility"] == "PUBLIC"


def test_platform_public_evidence_without_artifact_makes_public_scope_explicit(client, admin_header):
    response = client.post(
        "/api/v1/platform/evidence",
        json={
            "source_module": "platform",
            "evidence_type": "public_note",
            "summary_json": '{"status":"ok"}',
            "visibility": "PUBLIC",
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["project_id"] is None
    assert response.json()["environment_id"] is None
    assert response.json()["domain_name"] == "PUBLIC"
    assert response.json()["visibility"] == "PUBLIC"


def test_create_job_rejects_large_input_payload(client, admin_header):
    response = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "CATALOG_IMPORT_DATA_DICTIONARY",
            "source_module": "catalog",
            "input": {"blob": "x" * 17000},
        },
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "JOB_INVALID"
    assert "payload" in response.json()["message"].lower()


def test_create_job_rejects_mismatched_operational_scope(client, admin_header):
    project, _profile, environment = create_platform_scope(client, admin_header, prefix="Job Scope")
    _other_project, other_profile, _other_environment = create_platform_scope(
        client,
        admin_header,
        prefix="Other Job Scope",
    )

    missing_project = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "CATALOG_IMPORT_DATA_DICTIONARY",
            "source_module": "catalog",
            "environment_id": environment["id"],
            "domain_name": "OTM1",
        },
        headers=admin_header,
    )
    mismatched_profile = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "CATALOG_IMPORT_DATA_DICTIONARY",
            "source_module": "catalog",
            "project_id": project["id"],
            "profile_id": other_profile["id"],
            "environment_id": environment["id"],
            "domain_name": "OTM1",
        },
        headers=admin_header,
    )

    assert missing_project.status_code == 400
    assert missing_project.json()["code"] == "OPERATIONAL_SCOPE_PROJECT_REQUIRED"
    assert mismatched_profile.status_code == 400
    assert mismatched_profile.json()["code"] == "OPERATIONAL_SCOPE_PROFILE_PROJECT_MISMATCH"


def test_run_job_fails_safely_when_result_payload_is_large(client, admin_header):
    created = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "input": {"blob": "x" * 16370},
        },
        headers=admin_header,
    ).json()

    response = client.post(f"/api/v1/platform/jobs/{created['id']}/run", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "FAILED"
    assert payload["error"]["code"] == "JOB_RESULT_TOO_LARGE"
    assert payload["result"] == {}
    assert "x" * 100 not in str(payload["result"])
    assert "x" * 100 not in str(payload["error"])


def test_list_and_detail_jobs_return_client_safe_payload(client, admin_header):
    project, profile, environment = create_platform_scope(client, admin_header, prefix="Job Detail")
    created = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "CATALOG_IMPORT_DATA_DICTIONARY",
            "source_module": "catalog",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
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
    project, _profile, environment = create_platform_scope(client, admin_header, prefix="Job Filter DEV")
    second_project, _second_profile, second_environment = create_platform_scope(
        client,
        admin_header,
        prefix="Job Filter TEST",
    )
    first = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "CATALOG_IMPORT_DATA_DICTIONARY",
            "source_module": "catalog",
            "project_id": project["id"],
            "environment_id": environment["id"],
            "domain_name": "OTM1",
        },
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "CATALOG_IMPORT_DATA_DICTIONARY",
            "source_module": "catalog",
            "project_id": second_project["id"],
            "environment_id": second_environment["id"],
            "domain_name": "OTM2",
        },
        headers=admin_header,
    )

    response = client.get(
        f"/api/v1/platform/jobs?source_module=catalog&environment_id={environment['id']}&domain_name=otm1",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == first["id"]
    assert response.json()["items"][0]["environment_id"] == environment["id"]
    assert response.json()["items"][0]["domain_name"] == "OTM1"


def test_jobs_are_limited_to_active_context_for_non_admin(client, admin_header, auth_header, db_session):
    project, profile, environment = create_platform_scope(client, admin_header, prefix="Visible Job")
    hidden_project, _hidden_profile, hidden_environment = create_platform_scope(
        client,
        admin_header,
        prefix="Hidden Job",
    )
    visible_job = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "OTM1",
            "input": {"value": "visible"},
            "execute_now": True,
        },
        headers=admin_header,
    ).json()
    hidden_job = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "project_id": hidden_project["id"],
            "environment_id": hidden_environment["id"],
            "domain_name": "OTM1",
            "input": {"value": "hidden"},
            "execute_now": True,
        },
        headers=admin_header,
    ).json()
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Job Viewer")
    capability = Capability(name="platform.jobs.view")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    db_session.add(
        UserProjectRole(
            user_id=user_id,
            project_id=project["id"],
            environment_id=environment["id"],
            domain_name="OTM1",
            role_id=role.id,
        )
    )
    db_session.commit()
    client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
        },
        headers=auth_header,
    )

    listed = client.get("/api/v1/platform/jobs?source_module=platform", headers=auth_header)
    visible_detail = client.get(f"/api/v1/platform/jobs/{visible_job['id']}", headers=auth_header)
    hidden_detail = client.get(f"/api/v1/platform/jobs/{hidden_job['id']}", headers=auth_header)
    hidden_events = client.get(f"/api/v1/platform/jobs/{hidden_job['id']}/events", headers=auth_header)
    hidden_run = client.post(f"/api/v1/platform/jobs/{hidden_job['id']}/run", headers=auth_header)
    hidden_cancel = client.post(f"/api/v1/platform/jobs/{hidden_job['id']}/cancel", headers=auth_header)

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == visible_job["id"]
    assert visible_detail.status_code == 200
    assert visible_detail.json()["id"] == visible_job["id"]
    assert hidden_detail.status_code == 403
    assert hidden_detail.json()["code"] == "JOB_FORBIDDEN"
    assert hidden_events.status_code == 403
    assert hidden_events.json()["code"] == "JOB_FORBIDDEN"
    assert hidden_run.status_code == 403
    assert hidden_run.json()["code"] == "JOB_FORBIDDEN"
    assert hidden_cancel.status_code == 403
    assert hidden_cancel.json()["code"] == "JOB_FORBIDDEN"


def test_non_admin_can_create_jobs_only_inside_active_context(client, admin_header, auth_header, db_session):
    project, profile, environment = create_platform_scope(client, admin_header, prefix="Create Visible Job")
    hidden_project, _hidden_profile, hidden_environment = create_platform_scope(
        client,
        admin_header,
        prefix="Create Hidden Job",
    )
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Job Creator")
    capability = Capability(name="platform.jobs.create")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    db_session.add(
        UserProjectRole(
            user_id=user_id,
            project_id=project["id"],
            environment_id=environment["id"],
            domain_name="OTM1",
            role_id=role.id,
        )
    )
    db_session.commit()
    client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
        },
        headers=auth_header,
    )

    visible = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "OTM1",
            "input": {"value": "visible"},
        },
        headers=auth_header,
    )
    hidden = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "project_id": hidden_project["id"],
            "environment_id": hidden_environment["id"],
            "domain_name": "OTM1",
            "input": {"value": "hidden"},
        },
        headers=auth_header,
    )
    cross_domain = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "OTM2",
            "input": {"value": "cross-domain"},
        },
        headers=auth_header,
    )
    unscoped = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "input": {"value": "unscoped"},
        },
        headers=auth_header,
    )

    assert visible.status_code == 200
    assert visible.json()["project_id"] == project["id"]
    assert hidden.status_code == 403
    assert hidden.json()["code"] == "JOB_FORBIDDEN"
    assert cross_domain.status_code == 403
    assert cross_domain.json()["code"] == "JOB_FORBIDDEN"
    assert unscoped.status_code == 403
    assert unscoped.json()["code"] == "JOB_FORBIDDEN"


def test_cancel_pending_job_records_event_and_audit(client, admin_header, db_session):
    project, _profile, environment = create_platform_scope(client, admin_header, prefix="Job Cancel")
    created = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "CATALOG_IMPORT_DATA_DICTIONARY",
            "source_module": "catalog",
            "project_id": project["id"],
            "environment_id": environment["id"],
            "domain_name": "OTM1",
        },
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
    event_payload = json.loads(event.payload_json)
    assert event_payload["environment_id"] == environment["id"]
    assert event_payload["domain_name"] == "OTM1"
    audit = db_session.query(AuditLog).filter(AuditLog.action == "job.cancel").one()
    assert audit.target_id == created["id"]
    audit_metadata = json.loads(audit.metadata_json)
    assert audit_metadata["environment_id"] == environment["id"]
    assert audit_metadata["domain_name"] == "OTM1"


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


def test_run_pending_job_endpoint_executes_registered_handler(client, admin_header, db_session):
    created = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "input": {"value": "synthetic"},
        },
        headers=admin_header,
    ).json()

    response = client.post(f"/api/v1/platform/jobs/{created['id']}/run", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "SUCCEEDED"
    assert payload["progress"] == 100
    assert payload["result"] == {"echo": {"value": "synthetic"}}
    events = db_session.query(JobEvent).filter(JobEvent.job_id == payload["id"]).order_by(JobEvent.created_at).all()
    assert [event.event_type for event in events] == ["JOB_CREATED", "JOB_STARTED", "JOB_SUCCEEDED"]


def test_run_completed_job_is_rejected(client, admin_header):
    created = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "input": {"value": "synthetic"},
            "execute_now": True,
        },
        headers=admin_header,
    ).json()

    response = client.post(f"/api/v1/platform/jobs/{created['id']}/run", headers=admin_header)

    assert response.status_code == 400
    assert "pending" in response.json()["message"].lower()


def test_list_job_events_filters_by_type_and_status(client, admin_header):
    job = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "input": {"value": "synthetic"},
            "execute_now": True,
        },
        headers=admin_header,
    ).json()

    response = client.get(
        f"/api/v1/platform/jobs/{job['id']}/events?event_type=job_succeeded&status_after=succeeded",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["event_type"] == "JOB_SUCCEEDED"
    assert response.json()["items"][0]["status_after"] == "SUCCEEDED"


def test_missing_job_handler_fails_safely(client, admin_header, db_session):
    project, _profile, environment = create_platform_scope(client, admin_header, prefix="Missing Handler")
    response = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "UNKNOWN_HANDLER",
            "source_module": "platform",
            "project_id": project["id"],
            "environment_id": environment["id"],
            "domain_name": "OTM1",
            "execute_now": True,
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "FAILED"
    assert payload["error"]["code"] == "JOB_HANDLER_NOT_REGISTERED"
    assert "UNKNOWN_HANDLER" not in payload["error"]["message"]
    event = db_session.query(JobEvent).filter(JobEvent.job_id == payload["id"], JobEvent.event_type == "JOB_FAILED").one()
    event_payload = json.loads(event.payload_json)
    assert event_payload["error_code"] == "JOB_HANDLER_NOT_REGISTERED"
    assert event_payload["environment_id"] == environment["id"]
    assert event_payload["domain_name"] == "OTM1"


def test_artifact_hash_metadata_and_evidence_are_client_safe(client, admin_header):
    artifact_dir = get_settings().artifact_root / "test-artifacts"
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


def test_list_feature_flags_returns_admin_safe_payload(client, admin_header):
    client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=admin_header,
    )

    response = client.get("/api/v1/platform/feature-flags", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["name"] == "dev_tools"
    assert payload["items"][0]["enabled"] is True
    assert payload["items"][0]["scope"] == "global"
