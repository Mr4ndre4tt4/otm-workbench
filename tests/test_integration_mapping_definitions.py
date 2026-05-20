from sqlalchemy import inspect

from otm_workbench.models import IntegrationDefinition


def definition_payload(**overrides):
    payload = {
        "code": "PS_TO_EXT_DELIVERY",
        "name": "Planned Shipment to External Delivery",
        "description": "Synthetic mapping definition for backend tests.",
        "source_system": "OTM",
        "target_system": "EXT_SYSTEM",
        "source_format": "XML",
        "target_format": "JSON",
        "status": "ACTIVE",
    }
    payload.update(overrides)
    return payload


def test_integration_definitions_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "integration_definitions" in table_names


def test_create_integration_definition_starts_as_draft(client, admin_header, db_session):
    response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(),
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    definition = db_session.get(IntegrationDefinition, payload["id"])
    assert definition is not None
    assert payload["code"] == "PS_TO_EXT_DELIVERY"
    assert payload["status"] == "DRAFT"
    assert payload["source_format"] == "XML"
    assert payload["target_format"] == "JSON"
    assert payload["created_by"]
    assert definition.status == "DRAFT"


def test_list_integration_definitions(client, admin_header):
    create_response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="PS_TO_EXT_DELIVERY_LIST"),
        headers=admin_header,
    )
    assert create_response.status_code == 200

    response = client.get("/api/v1/modules/integration-mapping/definitions", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["code"] == "PS_TO_EXT_DELIVERY_LIST"
    assert payload["items"][0]["status"] == "DRAFT"


def test_get_integration_definition(client, admin_header):
    create_response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="PS_TO_EXT_DELIVERY_GET"),
        headers=admin_header,
    )
    definition_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition_id}",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["id"] == definition_id
    assert response.json()["code"] == "PS_TO_EXT_DELIVERY_GET"


def test_get_integration_definition_rejects_missing_id(client, admin_header):
    response = client.get(
        "/api/v1/modules/integration-mapping/definitions/missing-definition",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
