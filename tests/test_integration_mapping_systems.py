from sqlalchemy import inspect

from otm_workbench.models import IntegrationEndpoint, IntegrationSystem
from tests.test_integration_mapping_definitions import create_project_with_environments, set_active_context


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


def test_integration_systems_and_endpoints_follow_active_context_scope(client, admin_header):
    project_id, uat_id, dev_id = create_project_with_environments(client, admin_header)
    other_project_id, other_uat_id, _ = create_project_with_environments(client, admin_header, name_suffix=" Other")
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
    )
    visible = create_system(client, admin_header, code="VISIBLE_CARRIER_API")
    endpoint = client.post(
        f"/api/v1/modules/integration-mapping/systems/{visible['id']}/endpoints",
        json=endpoint_payload(visible["id"], code="VISIBLE_CREATE_DELIVERY"),
        headers=admin_header,
    ).json()
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM2",
    )
    hidden_domain = create_system(client, admin_header, code="HIDDEN_DOMAIN_API")
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=dev_id,
        domain_name="OTM1",
    )
    create_system(client, admin_header, code="HIDDEN_ENV_API")
    set_active_context(
        client,
        admin_header,
        project_id=other_project_id,
        environment_id=other_uat_id,
        domain_name="OTM1",
    )
    hidden_project = create_system(client, admin_header, code="HIDDEN_PROJECT_API")
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
    )

    listing = client.get("/api/v1/modules/integration-mapping/systems", headers=admin_header)
    hidden_endpoint_create = client.post(
        f"/api/v1/modules/integration-mapping/systems/{hidden_domain['id']}/endpoints",
        json=endpoint_payload(hidden_domain["id"], code="SHOULD_NOT_CREATE"),
        headers=admin_header,
    )
    hidden_endpoint_list = client.get(
        f"/api/v1/modules/integration-mapping/systems/{hidden_domain['id']}/endpoints",
        headers=admin_header,
    )
    hidden_project_endpoint_create = client.post(
        f"/api/v1/modules/integration-mapping/systems/{hidden_project['id']}/endpoints",
        json=endpoint_payload(hidden_project["id"], code="SHOULD_NOT_CREATE_PROJECT"),
        headers=admin_header,
    )
    hidden_project_endpoint_list = client.get(
        f"/api/v1/modules/integration-mapping/systems/{hidden_project['id']}/endpoints",
        headers=admin_header,
    )
    visible_endpoint_list = client.get(
        f"/api/v1/modules/integration-mapping/systems/{visible['id']}/endpoints",
        headers=admin_header,
    )

    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["items"]] == [visible["id"]]
    assert listing.json()["items"][0]["project_id"] == project_id
    assert listing.json()["items"][0]["environment_id"] == uat_id
    assert listing.json()["items"][0]["domain_name"] == "OTM1"
    assert hidden_endpoint_create.status_code == 404
    assert hidden_endpoint_list.status_code == 404
    assert hidden_project_endpoint_create.status_code == 404
    assert hidden_project_endpoint_list.status_code == 404
    assert visible_endpoint_list.status_code == 200
    assert visible_endpoint_list.json()["items"][0]["id"] == endpoint["id"]


def test_integration_systems_require_active_context_for_non_admin_access_and_create(
    client,
    admin_header,
    auth_header,
):
    created = create_system(client, admin_header, code="NO_CONTEXT_SYSTEM")

    listed = client.get("/api/v1/modules/integration-mapping/systems", headers=auth_header)
    endpoints = client.get(
        f"/api/v1/modules/integration-mapping/systems/{created['id']}/endpoints",
        headers=auth_header,
    )
    create_endpoint = client.post(
        f"/api/v1/modules/integration-mapping/systems/{created['id']}/endpoints",
        json=endpoint_payload(created["id"], code="NO_CONTEXT_ENDPOINT"),
        headers=auth_header,
    )
    create_system_response = client.post(
        "/api/v1/modules/integration-mapping/systems",
        json=system_payload(code="NO_CONTEXT_USER_SYSTEM"),
        headers=auth_header,
    )

    assert listed.status_code == 200
    assert listed.json()["items"] == []
    assert listed.json()["total"] == 0
    assert endpoints.status_code == 404
    assert endpoints.json()["code"] == "INTEGRATION_SYSTEM_NOT_FOUND"
    assert create_endpoint.status_code == 404
    assert create_system_response.status_code == 403
    assert create_system_response.json()["code"] == "ACTIVE_CONTEXT_REQUIRED"


def test_integration_system_dba_context_can_see_all_domains_in_active_environment(client, admin_header):
    project_id, uat_id, dev_id = create_project_with_environments(client, admin_header)
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
    )
    otm1 = create_system(client, admin_header, code="DBA_SYSTEM_OTM1")
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM2",
    )
    otm2 = create_system(client, admin_header, code="DBA_SYSTEM_OTM2")
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=dev_id,
        domain_name="OTM1",
    )
    create_system(client, admin_header, code="DBA_SYSTEM_OTHER_ENV")
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
        can_view_all_domains=True,
    )

    listing = client.get("/api/v1/modules/integration-mapping/systems", headers=admin_header)

    assert listing.status_code == 200
    assert {item["id"] for item in listing.json()["items"]} == {otm1["id"], otm2["id"]}


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
