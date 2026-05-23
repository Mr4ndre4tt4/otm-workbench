def create_shell_context(client, admin_header):
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
    return project, profile, environment


def test_gui_shell_backend_contracts_support_login_context_preferences_and_cockpit(client, admin_header):
    login = client.post(
        "/api/v1/platform/session/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    assert login.status_code == 200
    session_header = {"Authorization": f"Bearer {login.json()['access_token']}"}

    me = client.get("/api/v1/platform/session/me", headers=session_header)
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"
    assert me.json()["is_admin"] is True

    project, profile, environment = create_shell_context(client, session_header)
    active_context = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
        },
        headers=session_header,
    )
    assert active_context.status_code == 200
    assert active_context.json()["domain_name"] == "OTM1"

    preferences = client.put(
        "/api/v1/platform/user-preferences",
        json={
            "theme_mode": "system",
            "follow_system_theme": True,
            "density": "compact",
            "sidebar_mode": "collapsed",
        },
        headers=session_header,
    )
    assert preferences.status_code == 200
    assert preferences.json()["theme_mode"] == "system"
    assert preferences.json()["follow_system_theme"] is True

    navigation = client.get("/api/v1/platform/navigation", headers=session_header)
    assert navigation.status_code == 200
    nav_items = navigation.json()["items"]
    home = next(item for item in nav_items if item["id"] == "home")
    assert home["label"] == "Project Cockpit"
    assert home["label_key"] == "module.home.label"
    assert home["icon_key"] == "home"
    assert home["icon_family"] == "iconly"
    assert home["icon_light_ref"]["figma_page"] == "Library | Light"
    assert home["icon_dark_ref"]["figma_page"] == "Library | Dark"

    cockpit = client.get("/api/v1/platform/project-cockpit/summary", headers=session_header)
    assert cockpit.status_code == 200
    cockpit_payload = cockpit.json()
    assert cockpit_payload["module_id"] == "home"
    assert cockpit_payload["status"] == "ready"
    assert cockpit_payload["active_context"]["project_id"] == project["id"]
    assert cockpit_payload["active_context"]["profile_id"] == profile["id"]
    assert cockpit_payload["active_context"]["environment_id"] == environment["id"]
    assert cockpit_payload["active_context"]["domain_name"] == "OTM1"
    assert cockpit_payload["setup_status"]["status"] == "READY"
    assert any(item["id"] == "home" for item in cockpit_payload["module_summary"]["items"])
    assert any(action["key"] == "set_active_context" for action in cockpit_payload["available_actions"])

    persisted_context = client.get("/api/v1/platform/active-context", headers=session_header)
    persisted_preferences = client.get("/api/v1/platform/user-preferences", headers=session_header)
    capabilities = client.get("/api/v1/platform/active-context/capabilities", headers=session_header)
    assert persisted_context.status_code == 200
    assert persisted_context.json()["project_id"] == project["id"]
    assert persisted_preferences.status_code == 200
    assert persisted_preferences.json()["sidebar_mode"] == "collapsed"
    assert capabilities.status_code == 200
    assert capabilities.json()["is_admin"] is True
    assert capabilities.json()["capabilities"] == ["*"]


def test_gui_shell_backend_contracts_reject_unauthenticated_shell_reads(client):
    protected_paths = [
        "/api/v1/platform/session/me",
        "/api/v1/platform/navigation",
        "/api/v1/platform/active-context",
        "/api/v1/platform/user-preferences",
        "/api/v1/platform/project-cockpit/summary",
    ]

    for path in protected_paths:
        response = client.get(path)
        assert response.status_code == 401
