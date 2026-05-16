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
