from otm_workbench.models import Capability, Role, RoleCapability, SessionToken, User, UserProjectRole


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


def test_setup_selectors_are_limited_to_granted_projects_for_non_admin(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Scoped Workspace"},
        headers=admin_header,
    ).json()
    visible_project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Visible Project"},
        headers=admin_header,
    ).json()
    hidden_project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Hidden Project"},
        headers=admin_header,
    ).json()
    visible_profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": visible_project["id"], "name": "Visible Profile"},
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/platform/profiles",
        json={"project_id": hidden_project["id"], "name": "Hidden Profile"},
        headers=admin_header,
    )
    visible_environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": visible_project["id"], "name": "Visible DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/platform/environments",
        json={"project_id": hidden_project["id"], "name": "Hidden DEV", "environment_type": "DEV"},
        headers=admin_header,
    )
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Scoped Project Reader")
    capability = Capability(name="settings.project.manage")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    db_session.add(UserProjectRole(user_id=user_id, project_id=visible_project["id"], role_id=role.id))
    db_session.commit()

    workspaces = client.get("/api/v1/platform/workspaces", headers=auth_header)
    projects = client.get("/api/v1/platform/projects", headers=auth_header)
    visible_profiles = client.get(
        "/api/v1/platform/profiles",
        params={"project_id": visible_project["id"]},
        headers=auth_header,
    )
    hidden_profiles = client.get(
        "/api/v1/platform/profiles",
        params={"project_id": hidden_project["id"]},
        headers=auth_header,
    )
    visible_environments = client.get(
        "/api/v1/platform/environments",
        params={"project_id": visible_project["id"]},
        headers=auth_header,
    )
    hidden_environments = client.get(
        "/api/v1/platform/environments",
        params={"project_id": hidden_project["id"]},
        headers=auth_header,
    )

    assert workspaces.status_code == 200
    assert workspaces.json() == [{"id": workspace["id"], "name": "Scoped Workspace"}]
    assert projects.status_code == 200
    assert projects.json()["items"] == [{"id": visible_project["id"], "name": "Visible Project"}]
    assert visible_profiles.status_code == 200
    assert visible_profiles.json()["items"] == [{"id": visible_profile["id"], "name": "Visible Profile"}]
    assert hidden_profiles.status_code == 200
    assert hidden_profiles.json()["items"] == []
    assert visible_environments.status_code == 200
    assert visible_environments.json()["items"] == [{"id": visible_environment["id"], "name": "Visible DEV"}]
    assert hidden_environments.status_code == 200
    assert hidden_environments.json()["items"] == []


def test_access_model_is_limited_for_non_setup_users(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Access Model Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Access Model Project"},
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
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    target_user = User(email="hidden.target@example.test", password_hash="synthetic", is_admin=False)
    own_role = Role(name="Operational Viewer")
    hidden_role = Role(name="Hidden Setup Role")
    own_capability = Capability(name="rates.batch.view")
    hidden_capability = Capability(name="settings.users.manage")
    db_session.add_all([target_user, own_role, hidden_role, own_capability, hidden_capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=own_role.id, capability_id=own_capability.id))
    db_session.add(RoleCapability(role_id=hidden_role.id, capability_id=hidden_capability.id))
    db_session.add(UserProjectRole(user_id=user_id, project_id=project["id"], role_id=own_role.id))
    db_session.add(UserProjectRole(user_id=target_user.id, project_id=project["id"], role_id=hidden_role.id))
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

    access_model = client.get("/api/v1/platform/settings/access-model", headers=auth_header)

    assert access_model.status_code == 200
    payload = access_model.json()
    assert payload["users"] == [
        {"id": user_id, "email": "user@example.com", "is_active": True, "is_admin": False}
    ]
    assert payload["roles"] == [{"id": own_role.id, "name": "Operational Viewer", "capability_names": ["rates.batch.view"]}]
    assert payload["capability_names"] == []
    assert len(payload["grants"]) == 1
    assert payload["grants"][0]["project_id"] == project["id"]
    assert payload["grants"][0]["project_name"] == "Access Model Project"
    assert payload["grants"][0]["user_id"] == user_id
    assert payload["grants"][0]["user_email"] == "user@example.com"
    assert payload["grants"][0]["role_id"] == own_role.id
    assert payload["grants"][0]["role_name"] == "Operational Viewer"
    assert payload["access_policies"] == []


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


def test_active_context_requires_granted_project_for_non_admin(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Context Scope Workspace"},
        headers=admin_header,
    ).json()
    visible_project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Visible Context Project"},
        headers=admin_header,
    ).json()
    hidden_project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Hidden Context Project"},
        headers=admin_header,
    ).json()
    visible_profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": visible_project["id"], "name": "Visible Default"},
        headers=admin_header,
    ).json()
    hidden_profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": hidden_project["id"], "name": "Hidden Default"},
        headers=admin_header,
    ).json()
    visible_environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": visible_project["id"], "name": "Visible DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    hidden_environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": hidden_project["id"], "name": "Hidden DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Context Reader")
    capability = Capability(name="rates.batch.view")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    db_session.add(UserProjectRole(user_id=user_id, project_id=visible_project["id"], role_id=role.id))
    db_session.commit()

    hidden_context = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": hidden_project["id"],
            "profile_id": hidden_profile["id"],
            "environment_id": hidden_environment["id"],
            "domain_name": "otm2",
        },
        headers=auth_header,
    )
    mismatched_profile = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": visible_project["id"],
            "profile_id": hidden_profile["id"],
            "environment_id": visible_environment["id"],
            "domain_name": "otm1",
        },
        headers=auth_header,
    )
    mismatched_environment = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": visible_project["id"],
            "profile_id": visible_profile["id"],
            "environment_id": hidden_environment["id"],
            "domain_name": "otm1",
        },
        headers=auth_header,
    )
    visible_context = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": visible_project["id"],
            "profile_id": visible_profile["id"],
            "environment_id": visible_environment["id"],
            "domain_name": "otm1",
        },
        headers=auth_header,
    )

    assert hidden_context.status_code == 403
    assert hidden_context.json()["code"] == "ACTIVE_CONTEXT_PROJECT_FORBIDDEN"
    assert mismatched_profile.status_code == 400
    assert mismatched_profile.json()["code"] == "ACTIVE_CONTEXT_PROFILE_PROJECT_MISMATCH"
    assert mismatched_environment.status_code == 400
    assert mismatched_environment.json()["code"] == "ACTIVE_CONTEXT_ENVIRONMENT_PROJECT_MISMATCH"
    assert visible_context.status_code == 200
    assert visible_context.json()["project_id"] == visible_project["id"]
    assert visible_context.json()["profile_id"] == visible_profile["id"]
    assert visible_context.json()["environment_id"] == visible_environment["id"]


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


def test_project_setup_status_requires_visible_project_for_non_admin(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Setup Status Scope Workspace"},
        headers=admin_header,
    ).json()
    visible_project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Visible Setup Status"},
        headers=admin_header,
    ).json()
    hidden_project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Hidden Setup Status"},
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/platform/profiles",
        json={"project_id": visible_project["id"], "name": "Visible Default"},
        headers=admin_header,
    )
    client.post(
        "/api/v1/platform/profiles",
        json={"project_id": hidden_project["id"], "name": "Hidden Default"},
        headers=admin_header,
    )
    client.post(
        "/api/v1/platform/environments",
        json={"project_id": visible_project["id"], "name": "Visible DEV", "environment_type": "DEV"},
        headers=admin_header,
    )
    client.post(
        "/api/v1/platform/environments",
        json={"project_id": hidden_project["id"], "name": "Hidden DEV", "environment_type": "DEV"},
        headers=admin_header,
    )
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Setup Status Reader")
    capability = Capability(name="rates.batch.view")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    db_session.add(UserProjectRole(user_id=user_id, project_id=visible_project["id"], role_id=role.id))
    db_session.commit()

    visible_status = client.get(
        f"/api/v1/platform/projects/{visible_project['id']}/setup-status",
        headers=auth_header,
    )
    hidden_status = client.get(
        f"/api/v1/platform/projects/{hidden_project['id']}/setup-status",
        headers=auth_header,
    )

    assert visible_status.status_code == 200
    assert visible_status.json()["project_id"] == visible_project["id"]
    assert hidden_status.status_code == 403
    assert hidden_status.json()["code"] == "PROJECT_SETUP_STATUS_FORBIDDEN"


def test_settings_scope_authority_returns_backend_owned_actions_and_blockers(client, admin_header):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Settings Authority Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Settings Authority Project"},
        headers=admin_header,
    ).json()

    incomplete = client.get("/api/v1/platform/settings/scope-authority", headers=admin_header)

    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Default"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "UAT", "environment_type": "UAT"},
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
    ready = client.get("/api/v1/platform/settings/scope-authority", headers=admin_header)

    assert incomplete.status_code == 200
    incomplete_payload = incomplete.json()
    assert incomplete_payload["module"] == "settings"
    assert incomplete_payload["label"] == "Settings"
    assert incomplete_payload["status"] == "INCOMPLETE"
    assert "ACTIVE_CONTEXT" in incomplete_payload["blocked_reasons"]
    assert incomplete_payload["available_actions"][0]["key"] == "create_workspace"
    assert any(action["key"] == "set_active_context" and action["disabled"] for action in incomplete_payload["available_actions"])
    assert incomplete_payload["setup_counts"]["projects"] == 1

    assert ready.status_code == 200
    ready_payload = ready.json()
    assert ready_payload["status"] == "READY"
    assert ready_payload["active_context"]["project_id"] == project["id"]
    assert ready_payload["active_context"]["environment_id"] == environment["id"]
    assert ready_payload["active_context"]["domain_name"] == "OTM1"
    assert ready_payload["blocked_reasons"] == []
    assert any(action["key"] == "set_active_context" and not action["disabled"] for action in ready_payload["available_actions"])
    assert ready_payload["setup_counts"] == {
        "workspaces": 1,
        "projects": 1,
        "profiles": 1,
        "environments": 1,
    }
    assert ready_payload["setup_visibility"]["level"] == "GLOBAL"
    assert ready_payload["setup_visibility"]["can_manage_workspaces"] is True
    assert ready_payload["setup_visibility"]["can_manage_roles"] is True


def test_settings_scope_authority_limits_normal_user_setup_visibility(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Settings Visibility Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Settings Visibility Project"},
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
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Scoped Settings Viewer")
    capability = Capability(name="rates.batch.view")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    db_session.add(UserProjectRole(user_id=user_id, project_id=project["id"], role_id=role.id))
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

    response = client.get("/api/v1/platform/settings/scope-authority", headers=auth_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["setup_visibility"] == {
        "level": "SCOPED",
        "can_manage_users": False,
        "can_manage_workspaces": False,
        "can_manage_projects": False,
        "can_manage_profiles": False,
        "can_manage_environments": False,
        "can_manage_roles": False,
        "can_manage_grants": False,
        "can_manage_access_policies": False,
    }
    assert payload["setup_counts"] == {
        "workspaces": 0,
        "projects": 1,
        "profiles": 1,
        "environments": 1,
    }
    assert any(
        action["key"] == "create_workspace" and action["disabled"] and action["disabled_reason"] == "DBA_REQUIRED"
        for action in payload["available_actions"]
    )
    assert any(
        action["key"] == "assign_grant" and action["disabled"] and action["disabled_reason"] == "PROJECT_ADMIN_REQUIRED"
        for action in payload["available_actions"]
    )


def test_settings_scope_authority_allows_project_admin_setup_visibility(
    client,
    admin_header,
    auth_header,
    db_session,
):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Project Admin Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Project Admin Project"},
        headers=admin_header,
    ).json()
    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Default"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "UAT", "environment_type": "UAT"},
        headers=admin_header,
    ).json()
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Project Setup Admin")
    capabilities = [
        Capability(name="settings.project.manage"),
        Capability(name="settings.users.manage"),
        Capability(name="settings.roles.manage"),
        Capability(name="settings.grants.manage"),
        Capability(name="settings.access_policies.manage"),
    ]
    db_session.add(role)
    db_session.add_all(capabilities)
    db_session.flush()
    db_session.add_all([RoleCapability(role_id=role.id, capability_id=capability.id) for capability in capabilities])
    db_session.add(UserProjectRole(user_id=user_id, project_id=project["id"], role_id=role.id))
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

    response = client.get("/api/v1/platform/settings/scope-authority", headers=auth_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["setup_visibility"] == {
        "level": "PROJECT",
        "can_manage_users": True,
        "can_manage_workspaces": False,
        "can_manage_projects": False,
        "can_manage_profiles": True,
        "can_manage_environments": True,
        "can_manage_roles": True,
        "can_manage_grants": True,
        "can_manage_access_policies": True,
    }
    assert any(
        action["key"] == "create_profile" and not action["disabled"] for action in payload["available_actions"]
    )
    assert any(action["key"] == "create_user" and not action["disabled"] for action in payload["available_actions"])
    assert any(action["key"] == "assign_grant" and not action["disabled"] for action in payload["available_actions"])


def test_settings_role_and_grant_authoring_requires_setup_authority(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Role Authoring Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Role Authoring Project"},
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

    denied_role = client.post(
        "/api/v1/platform/roles",
        json={"name": "Denied Role", "capability_names": ["rates.batch.view"]},
        headers=auth_header,
    )

    created_role = client.post(
        "/api/v1/platform/roles",
        json={"name": "Rates Operator", "capability_names": ["rates.batch.view"]},
        headers=admin_header,
    )
    target_user_id = db_session.query(User).filter(User.email == "user@example.com").one().id
    denied_grant = client.post(
        "/api/v1/platform/grants",
        json={"project_id": project["id"], "user_id": target_user_id, "role_id": created_role.json()["id"]},
        headers=auth_header,
    )
    created_grant = client.post(
        "/api/v1/platform/grants",
        json={
            "project_id": project["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
            "user_id": target_user_id,
            "role_id": created_role.json()["id"],
        },
        headers=admin_header,
    )

    assert denied_role.status_code == 403
    assert denied_role.json()["code"] == "SETTINGS_ROLE_AUTHORITY_REQUIRED"
    assert created_role.status_code == 200
    assert created_role.json()["capability_names"] == ["rates.batch.view"]
    assert denied_grant.status_code == 403
    assert denied_grant.json()["code"] == "SETTINGS_GRANT_AUTHORITY_REQUIRED"
    assert created_grant.status_code == 200
    assert created_grant.json()["project_id"] == project["id"]
    assert created_grant.json()["environment_id"] == environment["id"]
    assert created_grant.json()["domain_name"] == "OTM1"
    assert created_grant.json()["user_id"] == target_user_id
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
    capabilities = client.get("/api/v1/platform/active-context/capabilities", headers=auth_header)
    client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm2",
        },
        headers=auth_header,
    )
    cross_domain_capabilities = client.get("/api/v1/platform/active-context/capabilities", headers=auth_header)
    assert capabilities.status_code == 200
    assert capabilities.json()["roles"] == ["Rates Operator"]
    assert capabilities.json()["capabilities"] == ["rates.batch.view"]
    assert cross_domain_capabilities.status_code == 200
    assert cross_domain_capabilities.json()["roles"] == []
    assert cross_domain_capabilities.json()["capabilities"] == []


def test_settings_user_authoring_requires_user_setup_authority(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "User Authoring Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "User Authoring Project"},
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
        headers=auth_header,
    )

    denied = client.post(
        "/api/v1/platform/users",
        json={"email": "denied.user@example.test", "password": "SyntheticPass123!", "is_active": True},
        headers=auth_header,
    )
    created = client.post(
        "/api/v1/platform/users",
        json={"email": "operator.user@example.test", "password": "SyntheticPass123!", "is_active": True},
        headers=admin_header,
    )
    access_model = client.get("/api/v1/platform/settings/access-model", headers=admin_header)

    assert denied.status_code == 403
    assert denied.json()["code"] == "SETTINGS_USER_AUTHORITY_REQUIRED"
    assert created.status_code == 200
    assert created.json()["email"] == "operator.user@example.test"
    assert "password" not in created.json()
    assert "password_hash" not in created.json()
    assert access_model.status_code == 200
    assert any(item["email"] == "operator.user@example.test" for item in access_model.json()["users"])


def test_legacy_project_grants_without_domain_still_apply_inside_project(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Legacy Grant Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Legacy Grant Project"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "UAT", "environment_type": "UAT"},
        headers=admin_header,
    ).json()
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Legacy Project Viewer")
    capability = Capability(name="settings.legacy.view")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    db_session.add(UserProjectRole(user_id=user_id, project_id=project["id"], role_id=role.id))
    db_session.commit()
    client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "environment_id": environment["id"],
            "domain_name": "otm2",
        },
        headers=auth_header,
    )

    response = client.get("/api/v1/platform/active-context/capabilities", headers=auth_header)

    assert response.status_code == 200
    assert response.json()["roles"] == ["Legacy Project Viewer"]
    assert response.json()["capabilities"] == ["settings.legacy.view"]


def test_project_setup_admin_profile_environment_authoring_follows_grant_scope(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Scoped Project Setup Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Scoped Project Setup"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Scoped Project Setup Admin")
    capability = Capability(name="settings.project.manage")
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
        json={"project_id": project["id"], "environment_id": environment["id"], "domain_name": "otm1"},
        headers=auth_header,
    )

    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Scoped profile"},
        headers=auth_header,
    )
    delegated_environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "UAT", "environment_type": "UAT"},
        headers=auth_header,
    )
    client.post(
        "/api/v1/platform/active-context",
        json={"project_id": project["id"], "environment_id": environment["id"], "domain_name": "otm2"},
        headers=auth_header,
    )
    denied_profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Cross domain profile"},
        headers=auth_header,
    )

    assert profile.status_code == 200
    assert profile.json()["name"] == "Scoped profile"
    assert delegated_environment.status_code == 200
    assert delegated_environment.json()["name"] == "UAT"
    assert denied_profile.status_code == 403
    assert denied_profile.json()["code"] == "SETTINGS_PROJECT_AUTHORITY_REQUIRED"


def test_project_setup_admin_can_author_roles_and_grants(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Delegated Setup Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Delegated Setup Project"},
        headers=admin_header,
    ).json()
    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Default"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "UAT", "environment_type": "UAT"},
        headers=admin_header,
    ).json()
    setup_user_token = auth_header["Authorization"].split(" ", 1)[1]
    setup_user_id = db_session.get(SessionToken, setup_user_token).user_id
    target_user = User(email="target@example.com", password_hash="synthetic", is_admin=False)
    role = Role(name="Delegated Setup Admin")
    capabilities = [Capability(name="settings.roles.manage"), Capability(name="settings.grants.manage")]
    db_session.add(target_user)
    db_session.add(role)
    db_session.add_all(capabilities)
    db_session.flush()
    db_session.add_all([RoleCapability(role_id=role.id, capability_id=capability.id) for capability in capabilities])
    db_session.add(UserProjectRole(user_id=setup_user_id, project_id=project["id"], role_id=role.id))
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

    created_role = client.post(
        "/api/v1/platform/roles",
        json={"name": "Delegated Rates Viewer", "capability_names": ["rates.reference.view"]},
        headers=auth_header,
    )
    created_grant = client.post(
        "/api/v1/platform/grants",
        json={"project_id": project["id"], "user_id": target_user.id, "role_id": created_role.json()["id"]},
        headers=auth_header,
    )
    access_model = client.get("/api/v1/platform/settings/access-model", headers=auth_header)

    assert created_role.status_code == 200
    assert created_grant.status_code == 200
    assert access_model.status_code == 200
    assert any(item["name"] == "Delegated Rates Viewer" for item in access_model.json()["roles"])
    grant_payload = next(item for item in access_model.json()["grants"] if item["role_name"] == "Delegated Rates Viewer")
    assert grant_payload["binding_scope_label"] == "Delegated Setup Project / Any environment / Project"
    assert grant_payload["binding_requirements"] == [
        "User: target@example.com",
        "Role: Delegated Rates Viewer",
        "Project: Delegated Setup Project",
        "Environment: Any environment",
        "Domain: Project",
    ]
    assert grant_payload["active_context_match"] is True
    assert grant_payload["active_context_disabled_reason"] is None


def test_settings_access_policy_authoring_requires_policy_authority(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Policy Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Policy Project"},
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
        headers=auth_header,
    )

    denied = client.post(
        "/api/v1/platform/access-policies",
        json={
            "project_id": project["id"],
            "name": "Denied policy",
            "visibility": "PRIVATE",
            "domain_name": "otm1",
            "rule_json": "{\"mode\":\"allow_list\"}",
        },
        headers=auth_header,
    )
    created = client.post(
        "/api/v1/platform/access-policies",
        json={
            "project_id": project["id"],
            "name": "Project private policy",
            "visibility": "PRIVATE",
            "domain_name": "otm1",
            "rule_json": "{\"mode\":\"allow_list\"}",
        },
        headers=admin_header,
    )
    access_model = client.get("/api/v1/platform/settings/access-model", headers=admin_header)

    assert denied.status_code == 403
    assert denied.json()["code"] == "SETTINGS_ACCESS_POLICY_AUTHORITY_REQUIRED"
    assert created.status_code == 200
    assert created.json()["project_id"] == project["id"]
    assert created.json()["domain_name"] == "OTM1"
    assert created.json()["visibility"] == "PRIVATE"
    assert access_model.status_code == 200
    policy_payload = next(item for item in access_model.json()["access_policies"] if item["name"] == "Project private policy")
    assert policy_payload["binding_scope_label"] == "Policy Project / PRIVATE / OTM1"
    assert policy_payload["binding_requirements"] == [
        "Project: Policy Project",
        "Visibility: PRIVATE",
        "Domain: OTM1",
    ]
    assert policy_payload["active_context_match"] is False
    assert policy_payload["active_context_disabled_reason"] == "ACTIVE_CONTEXT_REQUIRED"


def test_project_setup_admin_can_author_access_policy_only_for_active_project(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Delegated Policy Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Delegated Policy Project"},
        headers=admin_header,
    ).json()
    other_project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Other Policy Project"},
        headers=admin_header,
    ).json()
    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Default"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "UAT", "environment_type": "UAT"},
        headers=admin_header,
    ).json()
    setup_user_token = auth_header["Authorization"].split(" ", 1)[1]
    setup_user_id = db_session.get(SessionToken, setup_user_token).user_id
    role = Role(name="Policy Setup Admin")
    capability = Capability(name="settings.access_policies.manage")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    db_session.add(UserProjectRole(user_id=setup_user_id, project_id=project["id"], role_id=role.id))
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

    created = client.post(
        "/api/v1/platform/access-policies",
        json={
            "project_id": project["id"],
            "name": "Delegated private policy",
            "visibility": "PRIVATE",
            "domain_name": "otm1",
            "rule_json": "{\"mode\":\"domain_role\"}",
        },
        headers=auth_header,
    )
    denied_cross_project = client.post(
        "/api/v1/platform/access-policies",
        json={
            "project_id": other_project["id"],
            "name": "Cross project policy",
            "visibility": "PRIVATE",
            "domain_name": "otm2",
            "rule_json": "{\"mode\":\"domain_role\"}",
        },
        headers=auth_header,
    )
    access_model = client.get("/api/v1/platform/settings/access-model", headers=auth_header)

    assert created.status_code == 200
    assert created.json()["project_id"] == project["id"]
    assert denied_cross_project.status_code == 403
    assert denied_cross_project.json()["code"] == "SETTINGS_ACCESS_POLICY_AUTHORITY_REQUIRED"
    assert access_model.status_code == 200
    delegated_policy = next(item for item in access_model.json()["access_policies"] if item["name"] == "Delegated private policy")
    assert delegated_policy["binding_scope_label"] == "Delegated Policy Project / PRIVATE / OTM1"
    assert delegated_policy["active_context_match"] is True
    assert delegated_policy["active_context_disabled_reason"] is None
    assert all(item["project_id"] == project["id"] for item in access_model.json()["access_policies"])


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


def test_user_preferences_default_to_light_mode(client, auth_header):
    response = client.get("/api/v1/platform/user-preferences", headers=auth_header)

    assert response.status_code == 200
    assert response.json() == {
        "theme_mode": "light",
        "follow_system_theme": False,
        "density": "comfortable",
        "sidebar_mode": "expanded",
    }


def test_user_preferences_can_be_updated_and_read(client, auth_header):
    updated = client.put(
        "/api/v1/platform/user-preferences",
        json={
            "theme_mode": "system",
            "follow_system_theme": True,
            "density": "compact",
            "sidebar_mode": "collapsed",
        },
        headers=auth_header,
    )
    current = client.get("/api/v1/platform/user-preferences", headers=auth_header)

    assert updated.status_code == 200
    assert current.status_code == 200
    assert current.json() == {
        "theme_mode": "system",
        "follow_system_theme": True,
        "density": "compact",
        "sidebar_mode": "collapsed",
    }


def test_user_preferences_reject_inconsistent_system_theme_state(client, auth_header):
    follow_without_system = client.put(
        "/api/v1/platform/user-preferences",
        json={
            "theme_mode": "light",
            "follow_system_theme": True,
            "density": "comfortable",
            "sidebar_mode": "expanded",
        },
        headers=auth_header,
    )
    system_without_follow = client.put(
        "/api/v1/platform/user-preferences",
        json={
            "theme_mode": "system",
            "follow_system_theme": False,
            "density": "comfortable",
            "sidebar_mode": "expanded",
        },
        headers=auth_header,
    )
    current = client.get("/api/v1/platform/user-preferences", headers=auth_header)

    assert follow_without_system.status_code == 422
    assert system_without_follow.status_code == 422
    assert follow_without_system.json()["code"] == "VALIDATION_ERROR"
    assert "follow_system_theme requires theme_mode=system" in str(follow_without_system.json())
    assert "theme_mode=system requires follow_system_theme=true" in str(system_without_follow.json())
    assert current.status_code == 200
    assert current.json() == {
        "theme_mode": "light",
        "follow_system_theme": False,
        "density": "comfortable",
        "sidebar_mode": "expanded",
    }
