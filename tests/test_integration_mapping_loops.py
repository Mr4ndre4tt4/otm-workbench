from sqlalchemy import inspect

from otm_workbench.models import IntegrationLoopDefinition
from tests.test_integration_mapping_mappings import create_source_and_target_documents


def loop_payload(source, target, **overrides):
    payload = {
        "source_schema_document_id": source["id"],
        "target_schema_document_id": target["id"],
        "source_collection_path": "/Transmission/Shipment/ShipmentStop",
        "target_collection_path": "$.deliveries[]",
        "name": "Synthetic delivery loop",
        "description": "Metadata-only loop declaration for synthetic payloads.",
        "sequence_index": 20,
    }
    payload.update(overrides)
    return payload


def test_integration_loop_definitions_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "integration_loop_definitions" in table_names


def test_create_integration_loop_definition_validates_collection_paths(client, admin_header, db_session):
    definition, source, target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/loops",
        json=loop_payload(source, target),
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    loop = db_session.get(IntegrationLoopDefinition, payload["id"])
    assert loop is not None
    assert payload["definition_id"] == definition["id"]
    assert payload["source_collection_path"] == "/Transmission/Shipment/ShipmentStop"
    assert payload["target_collection_path"] == "$.deliveries[]"
    assert payload["status"] == "ACTIVE"
    assert "SYNTHETIC" not in str(payload)


def test_list_and_get_integration_loop_definitions(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/loops",
        json=loop_payload(source, target, sequence_index=5),
        headers=admin_header,
    )
    assert created.status_code == 200

    listing = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/loops",
        headers=admin_header,
    )
    detail = client.get(
        f"/api/v1/modules/integration-mapping/loops/{created.json()['id']}",
        headers=admin_header,
    )

    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == created.json()["id"]
    assert detail.status_code == 200
    assert detail.json()["id"] == created.json()["id"]


def test_create_integration_loop_definition_rejects_unknown_collection_path(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/loops",
        json=loop_payload(source, target, source_collection_path="/Transmission/Missing"),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_LOOP_PATH_INVALID"


def test_create_integration_loop_definition_rejects_missing_definition(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        "/api/v1/modules/integration-mapping/definitions/missing-definition/loops",
        json=loop_payload(source, target),
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
