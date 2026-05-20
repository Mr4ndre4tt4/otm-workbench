from sqlalchemy import inspect

from otm_workbench.models import IntegrationEndpoint, IntegrationSystem


def system_payload(**overrides):
    payload = {
        "code": "EXT_SYSTEM",
        "name": "External Delivery API",
        "system_type": "EXTERNAL_API",
        "base_url": "https://api.example.test",
        "description": "Synthetic external system for backend tests.",
    }
    payload.update(overrides)
    return payload


def endpoint_payload(system_id: str, **overrides):
    payload = {
        "system_id": system_id,
        "code": "CREATE_DELIVERY",
        "name": "Create Delivery",
        "path": "/deliveries",
        "method": "POST",
        "payload_format": "JSON",
        "description": "Synthetic endpoint metadata.",
    }
    payload.update(overrides)
    return payload


def create_system(client, admin_header, **overrides):
    response = client.post(
        "/api/v1/modules/integration-mapping/systems",
        json=system_payload(**overrides),
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def test_integration_systems_tables_exist_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "integration_systems" in table_names
    assert "integration_endpoints" in table_names


def test_create_integration_system_stores_non_secret_metadata(client, admin_header, db_session):
    response = client.post(
        "/api/v1/modules/integration-mapping/systems",
        json=system_payload(),
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    system = db_session.get(IntegrationSystem, payload["id"])
    assert system is not None
    assert payload["code"] == "EXT_SYSTEM"
    assert payload["system_type"] == "EXTERNAL_API"
    assert payload["base_url"] == "https://api.example.test"
    assert payload["status"] == "ACTIVE"
    assert "password" not in payload
    assert "secret" not in payload


def test_list_integration_systems(client, admin_header):
    create_system(client, admin_header, code="CARRIER_API")

    response = client.get("/api/v1/modules/integration-mapping/systems", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["code"] == "CARRIER_API"


def test_create_integration_endpoint_for_system(client, admin_header, db_session):
    system = create_system(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/systems/{system['id']}/endpoints",
        json=endpoint_payload(system["id"]),
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    endpoint = db_session.get(IntegrationEndpoint, payload["id"])
    assert endpoint is not None
    assert payload["system_id"] == system["id"]
    assert payload["code"] == "CREATE_DELIVERY"
    assert payload["method"] == "POST"
    assert payload["payload_format"] == "JSON"
    assert "token" not in payload
    assert "secret" not in payload


def test_list_integration_endpoints_for_system(client, admin_header):
    system = create_system(client, admin_header)
    created = client.post(
        f"/api/v1/modules/integration-mapping/systems/{system['id']}/endpoints",
        json=endpoint_payload(system["id"], code="GET_LOCATION", method="GET", path="/locations/{id}"),
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.get(
        f"/api/v1/modules/integration-mapping/systems/{system['id']}/endpoints",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["code"] == "GET_LOCATION"
    assert payload["items"][0]["method"] == "GET"


def test_create_integration_system_rejects_secret_like_payload(client, admin_header):
    response = client.post(
        "/api/v1/modules/integration-mapping/systems",
        json=system_payload(api_token="sk-test-secret"),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_SECRET_RISK"


def test_create_integration_endpoint_rejects_missing_system(client, admin_header):
    response = client.post(
        "/api/v1/modules/integration-mapping/systems/missing-system/endpoints",
        json=endpoint_payload("missing-system"),
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_SYSTEM_NOT_FOUND"
