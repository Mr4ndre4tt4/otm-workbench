def test_create_workspace_project_profile_environment(client, admin_header):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Local"},
        headers=admin_header,
    )
    assert workspace.status_code == 200

    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace.json()["id"], "name": "OTM Rollout"},
        headers=admin_header,
    )
    assert project.status_code == 200

    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project.json()["id"], "name": "Default"},
        headers=admin_header,
    )
    assert profile.status_code == 200

    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project.json()["id"], "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    )
    assert environment.status_code == 200


def test_workspace_list_requires_authentication(client):
    response = client.get("/api/v1/platform/workspaces")

    assert response.status_code == 401


def test_active_context_defaults_to_public_domain_without_selection(client, admin_header):
    response = client.get("/api/v1/platform/active-context", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] is None
    assert payload["profile_id"] is None
    assert payload["environment_id"] is None
    assert payload["domain_name"] is None
    assert payload["allowed_domains"] == ["PUBLIC"]
    assert payload["can_view_all_domains"] is False


def test_active_context_can_be_set_and_read_with_allowed_domains(client, admin_header):
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

    updated = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
        },
        headers=admin_header,
    )
    current = client.get("/api/v1/platform/active-context", headers=admin_header)

    assert updated.status_code == 200
    assert current.status_code == 200
    payload = current.json()
    assert payload["project_id"] == project["id"]
    assert payload["profile_id"] == profile["id"]
    assert payload["environment_id"] == environment["id"]
    assert payload["domain_name"] == "OTM1"
    assert payload["allowed_domains"] == ["PUBLIC", "OTM1"]
    assert payload["can_view_all_domains"] is False


def test_project_setup_status_reports_ready_when_context_profile_and_environment_exist(client, admin_header):
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
    client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
        },
        headers=admin_header,
    )

    response = client.get(f"/api/v1/platform/projects/{project['id']}/setup-status", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == project["id"]
    assert payload["status"] == "READY"
    assert payload["profile_count"] == 1
    assert payload["environment_count"] == 1
    assert payload["active_context_selected"] is True
    assert payload["missing_requirements"] == []


def test_project_setup_status_reports_missing_requirements(client, admin_header):
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

    response = client.get(f"/api/v1/platform/projects/{project['id']}/setup-status", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == project["id"]
    assert payload["status"] == "INCOMPLETE"
    assert payload["profile_count"] == 0
    assert payload["environment_count"] == 0
    assert payload["active_context_selected"] is False
    assert payload["missing_requirements"] == ["PROFILE", "ENVIRONMENT", "ACTIVE_CONTEXT"]
