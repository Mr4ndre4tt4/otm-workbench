from otm_workbench.models import Artifact, Evidence


def create_context(client, admin_header):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Local"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Synthetic Rollout"},
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
    active_context = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
        },
        headers=admin_header,
    )
    assert active_context.status_code == 200
    return project, profile, environment


def action_by_key(payload, key):
    return next(action for action in payload["available_actions"] if action["key"] == key)


def test_project_cockpit_summary_requires_authentication(client):
    response = client.get("/api/v1/platform/project-cockpit/summary")

    assert response.status_code == 401


def test_project_cockpit_summary_returns_empty_shell_contract(client, admin_header):
    response = client.get("/api/v1/platform/project-cockpit/summary", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["module_id"] == "home"
    assert payload["title"] == "Project Cockpit"
    assert payload["status"] == "needs_context"
    assert payload["active_context"]["project_id"] is None
    assert payload["setup_status"] is None
    assert payload["counts"]["recent_jobs"] == 0
    assert payload["counts"]["recent_artifacts"] == 0
    assert payload["counts"]["recent_evidence"] == 0
    assert payload["recent_jobs"] == []
    assert payload["recent_artifacts"] == []
    assert payload["recent_evidence"] == []
    assert payload["module_summary"]["total"] >= 1
    assert any(item["id"] == "home" for item in payload["module_summary"]["items"])
    assert action_by_key(payload, "set_active_context")["disabled"] is False


def test_project_cockpit_summary_reports_active_project_without_raw_payloads(
    client,
    admin_header,
    db_session,
):
    project, profile, environment = create_context(client, admin_header)
    job = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
            "input": {"raw_reference": "SYNTHETIC_RATE_ROW_001"},
        },
        headers=admin_header,
    ).json()
    artifact = Artifact(
        project_id=project["id"],
        source_module="rates",
        artifact_type="rates_csv_zip",
        file_path="var/test-artifacts/synthetic-rates.zip",
        file_name="synthetic-rates.zip",
        content_type="application/zip",
        sha256="1" * 64,
        size_bytes=128,
        sensitivity_level="internal",
    )
    db_session.add(artifact)
    db_session.flush()
    evidence = Evidence(
        project_id=project["id"],
        source_module="rates",
        evidence_type="rates_csv_export",
        summary_json='{"status":"ok","raw_reference":"SYNTHETIC_RATE_ROW_001"}',
        artifact_id=artifact.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db_session.add(evidence)
    db_session.commit()

    response = client.get("/api/v1/platform/project-cockpit/summary", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["active_context"]["project_id"] == project["id"]
    assert payload["active_context"]["profile_id"] == profile["id"]
    assert payload["active_context"]["environment_id"] == environment["id"]
    assert payload["active_context"]["domain_name"] == "OTM1"
    assert payload["setup_status"]["status"] == "READY"
    assert payload["counts"]["recent_jobs"] == 1
    assert payload["counts"]["recent_artifacts"] == 1
    assert payload["counts"]["recent_evidence"] == 1
    assert payload["recent_jobs"][0]["id"] == job["id"]
    assert payload["recent_jobs"][0]["input_present"] is True
    assert "input" not in payload["recent_jobs"][0]
    assert payload["recent_artifacts"][0]["id"] == artifact.id
    assert "file_path" not in payload["recent_artifacts"][0]
    assert payload["recent_evidence"][0]["id"] == evidence.id
    assert payload["recent_evidence"][0]["summary"] == {"status": "ok"}
    assert "SYNTHETIC_RATE_ROW_001" not in str(payload)
