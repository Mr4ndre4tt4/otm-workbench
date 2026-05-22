from sqlalchemy.exc import IntegrityError

from otm_workbench.models import Capability, Role, RoleCapability, SessionToken, UserProjectRole
from otm_workbench.platform.navigation import seed_modules


def test_modules_endpoint_returns_registered_master_data(client, admin_header):
    response = client.get("/api/v1/platform/modules", headers=admin_header)

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "master_data"
    assert response.json()["items"][0]["status"] == "ACTIVE"


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


def test_seed_modules_tolerates_concurrent_unique_insert_race():
    class RaceSession:
        rolled_back = False

        def get(self, model, identifier):
            return None

        def add(self, module):
            return None

        def commit(self):
            raise IntegrityError("insert modules", {}, Exception("duplicate module id"))

        def rollback(self):
            self.rolled_back = True

    db = RaceSession()

    seed_modules(db)

    assert db.rolled_back is True
