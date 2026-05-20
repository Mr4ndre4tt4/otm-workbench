def test_integration_mapping_health_requires_authentication(client):
    response = client.get("/api/v1/modules/integration-mapping/health")

    assert response.status_code == 401


def test_integration_mapping_health(client, admin_header):
    response = client.get("/api/v1/modules/integration-mapping/health", headers=admin_header)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "integration_mapping",
        "mode": "specification_first",
    }


def test_modules_endpoint_returns_integration_mapping_module(client, admin_header):
    response = client.get("/api/v1/platform/modules", headers=admin_header)

    assert response.status_code == 200
    module_ids = [item["id"] for item in response.json()["items"]]
    assert "integration_mapping" in module_ids


def test_navigation_returns_integration_mapping_for_admin(client, admin_header):
    response = client.get("/api/v1/platform/navigation", headers=admin_header)

    assert response.status_code == 200
    items = response.json()["items"]
    integration_mapping = next(item for item in items if item["id"] == "integration_mapping")
    assert integration_mapping == {
        "id": "integration_mapping",
        "label": "Integration Mapping Studio",
        "path": "/integration-mapping",
        "status": "ACTIVE",
    }
