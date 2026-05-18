def test_modules_endpoint_returns_registered_master_data(client, admin_header):
    response = client.get("/api/v1/platform/modules", headers=admin_header)

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "master_data"
    assert response.json()["items"][0]["status"] == "PLANNED"


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
