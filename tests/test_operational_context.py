from otm_workbench.models import Capability, Role, RoleCapability, SessionToken, UserProjectRole


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


def test_active_context_selector_lists_projects_profiles_and_environments(client, admin_header):
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

    projects = client.get(
        "/api/v1/platform/projects",
        params={"workspace_id": workspace["id"]},
        headers=admin_header,
    )
    profiles = client.get(
        "/api/v1/platform/profiles",
        params={"project_id": project["id"]},
        headers=admin_header,
    )
    environments = client.get(
        "/api/v1/platform/environments",
        params={"project_id": project["id"]},
        headers=admin_header,
    )

    assert projects.status_code == 200
    assert projects.json()["items"] == [{"id": project["id"], "name": "Synthetic Rollout"}]
    assert profiles.status_code == 200
    assert profiles.json()["items"] == [{"id": profile["id"], "name": "Default"}]
    assert environments.status_code == 200
    assert environments.json()["items"] == [{"id": environment["id"], "name": "DEV"}]


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


def test_active_context_capabilities_return_roles_and_capabilities_for_project(
    client,
    admin_header,
    auth_header,
    db_session,
):
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
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Catalog Steward")
    capability = Capability(name="catalog.reference.validate")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add_all(
        [
            RoleCapability(role_id=role.id, capability_id=capability.id),
            UserProjectRole(user_id=user_id, project_id=project["id"], role_id=role.id),
        ]
    )
    db_session.commit()
    active_context = client.post(
        "/api/v1/platform/active-context",
        json={"project_id": project["id"], "domain_name": "otm1"},
        headers=auth_header,
    )

    response = client.get("/api/v1/platform/active-context/capabilities", headers=auth_header)

    assert active_context.status_code == 200
    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == project["id"]
    assert payload["is_admin"] is False
    assert payload["roles"] == ["Catalog Steward"]
    assert payload["capabilities"] == ["catalog.reference.validate"]


def test_active_context_capabilities_return_admin_wildcard(client, admin_header):
    response = client.get("/api/v1/platform/active-context/capabilities", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] is None
    assert payload["is_admin"] is True
    assert payload["roles"] == ["ADMIN"]
    assert payload["capabilities"] == ["*"]
