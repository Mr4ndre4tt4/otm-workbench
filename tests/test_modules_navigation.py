from otm_workbench.models import Capability, Role, RoleCapability, SessionToken, UserProjectRole


def test_modules_endpoint_returns_registered_master_data(client, admin_header):
    response = client.get("/api/v1/platform/modules", headers=admin_header)

    assert response.status_code == 200
    master_data = next(item for item in response.json()["items"] if item["id"] == "master_data")
    assert master_data["id"] == "master_data"
    assert master_data["status"] == "ACTIVE"
    assert master_data["group_key"] == "build"
    assert master_data["group_label"] == "Build"
    assert master_data["icon_key"] == "database"
    assert master_data["sort_order"] == 210
    assert master_data["surface_type"] == "module"
    assert master_data["description"] == "Create and validate reusable OTM master data load templates."
    assert master_data["is_primary"] is True


def test_navigation_returns_backend_owned_group_icon_and_order_metadata(client, admin_header):
    response = client.get("/api/v1/platform/navigation", headers=admin_header)

    assert response.status_code == 200
    items = response.json()["items"]
    home = next(item for item in items if item["id"] == "home")
    rates = next(item for item in items if item["id"] == "rates")
    assert home["group_key"] == "cockpit"
    assert home["group_label"] == "Cockpit"
    assert home["icon_key"] == "layout-dashboard"
    assert home["sort_order"] == 100
    assert home["surface_type"] == "workspace"
    assert home["description"] == "Project cockpit and operational overview."
    assert home["is_primary"] is True
    assert rates["group_key"] == "build"
    assert rates["sort_order"] == 220


def test_navigation_hides_dev_only_when_flag_is_disabled(client, admin_header):
    response = client.get("/api/v1/platform/navigation", headers=admin_header)

    assert response.status_code == 200
    module_ids = [item["id"] for item in response.json()["items"]]
    assert "dev_tools" not in module_ids


def test_feature_flag_can_enable_dev_module_for_admin(client, admin_header):
    flag = client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=admin_header,
    )
    assert flag.status_code == 200

    response = client.get("/api/v1/platform/navigation", headers=admin_header)
    module_ids = [item["id"] for item in response.json()["items"]]
    assert "dev_tools" in module_ids


def test_modules_endpoint_returns_rates_module(client, admin_header):
    response = client.get("/api/v1/platform/modules", headers=admin_header)

    assert response.status_code == 200
    module_ids = [item["id"] for item in response.json()["items"]]
    assert "rates" in module_ids


def test_modules_endpoint_returns_catalog_core_module(client, admin_header):
    response = client.get("/api/v1/platform/modules", headers=admin_header)

    assert response.status_code == 200
    module_ids = [item["id"] for item in response.json()["items"]]
    assert "catalog" in module_ids


def test_navigation_filters_required_capability_by_active_project(client, admin_header, auth_header, db_session):
    hidden = client.get("/api/v1/platform/navigation", headers=auth_header)
    assert hidden.status_code == 200
    assert "rates" not in [item["id"] for item in hidden.json()["items"]]

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
    role = Role(name="Rates Viewer")
    capability = Capability(name="rates.reference.view")
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
    visible = client.get("/api/v1/platform/navigation", headers=auth_header)

    assert active_context.status_code == 200
    assert visible.status_code == 200
    assert "rates" in [item["id"] for item in visible.json()["items"]]
