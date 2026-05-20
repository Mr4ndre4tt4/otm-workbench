from sqlalchemy import inspect

from otm_workbench.models import IntegrationLookupDefinition
from tests.test_integration_mapping_mappings import create_source_and_target_documents


def lookup_payload(source, target, **overrides):
    payload = {
        "source_schema_document_id": source["id"],
        "target_schema_document_id": target["id"],
        "input_path": "/Transmission/Shipment/ShipmentGid",
        "output_path": "$.header.shipmentId",
        "lookup_type": "MOCK",
        "name": "Synthetic carrier lookup",
        "description": "Metadata-only mock lookup for synthetic payload paths.",
        "mock_response_json": '{"shipmentId":"DEMO-SHIPMENT"}',
        "sequence_index": 40,
    }
    payload.update(overrides)
    return payload


def test_integration_lookup_definitions_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "integration_lookup_definitions" in table_names


def test_create_integration_lookup_definition_validates_paths_and_mock(client, admin_header, db_session):
    definition, source, target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/lookups",
        json=lookup_payload(source, target),
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    lookup = db_session.get(IntegrationLookupDefinition, payload["id"])
    assert lookup is not None
    assert payload["definition_id"] == definition["id"]
    assert payload["input_path"] == "/Transmission/Shipment/ShipmentGid"
    assert payload["output_path"] == "$.header.shipmentId"
    assert payload["lookup_type"] == "MOCK"
    assert payload["mock_response_json"] == '{"shipmentId":"DEMO-SHIPMENT"}'
    assert payload["status"] == "ACTIVE"
    assert "SYNTHETIC" not in str(payload)


def test_list_and_get_integration_lookup_definitions(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/lookups",
        json=lookup_payload(source, target, sequence_index=8),
        headers=admin_header,
    )
    assert created.status_code == 200

    listing = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/lookups",
        headers=admin_header,
    )
    detail = client.get(
        f"/api/v1/modules/integration-mapping/lookups/{created.json()['id']}",
        headers=admin_header,
    )

    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == created.json()["id"]
    assert detail.status_code == 200
    assert detail.json()["id"] == created.json()["id"]


def test_create_integration_lookup_definition_rejects_unknown_path(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/lookups",
        json=lookup_payload(source, target, input_path="/Transmission/Missing"),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_LOOKUP_PATH_INVALID"


def test_create_integration_lookup_definition_rejects_non_mock_type(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/lookups",
        json=lookup_payload(source, target, lookup_type="REST"),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_LOOKUP_TYPE_INVALID"


def test_create_integration_lookup_definition_rejects_secret_like_mock(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/lookups",
        json=lookup_payload(source, target, mock_response_json='{"api_token":"sk-test-secret"}'),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_SECRET_RISK"


def test_create_integration_lookup_definition_rejects_missing_definition(client, admin_header):
    _definition, source, target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        "/api/v1/modules/integration-mapping/definitions/missing-definition/lookups",
        json=lookup_payload(source, target),
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
