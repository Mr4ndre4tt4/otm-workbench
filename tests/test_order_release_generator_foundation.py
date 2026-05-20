from sqlalchemy import inspect


def test_order_release_generator_health_requires_authentication(client):
    response = client.get("/api/v1/modules/order-release-generator/health")

    assert response.status_code == 401


def test_order_release_generator_health(client, admin_header):
    response = client.get("/api/v1/modules/order-release-generator/health", headers=admin_header)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "module": "order_release_generator"}


def test_order_release_templates_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "order_release_templates" in table_names


def test_list_order_release_templates_seeds_synthetic_tl_template(client, admin_header):
    response = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    template = payload["items"][0]
    assert template["code"] == "TL_ORDER_RELEASE_MVP0"
    assert template["name"] == "Synthetic TL Order Release"
    assert template["version"] == 1
    assert template["status"] == "ACTIVE"
    assert template["macro_object_code"] == "ORDER_RELEASE"
    assert "release_gid" in template["required_columns"]


def test_modules_endpoint_returns_order_release_generator_module(client, admin_header):
    response = client.get("/api/v1/platform/modules", headers=admin_header)

    assert response.status_code == 200
    module_ids = [item["id"] for item in response.json()["items"]]
    assert "order_release_generator" in module_ids
