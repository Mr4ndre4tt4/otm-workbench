from sqlalchemy import inspect

from otm_workbench.models import IntegrationMapping
from tests.test_integration_mapping_definitions import definition_payload
from tests.test_integration_mapping_payload_artifacts import payload_import


def create_definition(client, admin_header):
    response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="PS_MAPPING_CRUD"),
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def create_schema_document(client, admin_header, definition_id, **payload_overrides):
    artifact = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition_id}/payload-artifacts",
        json=payload_import(**payload_overrides),
        headers=admin_header,
    )
    assert artifact.status_code == 200
    document = client.post(
        f"/api/v1/modules/integration-mapping/payload-artifacts/{artifact.json()['id']}/schema-documents",
        headers=admin_header,
    )
    assert document.status_code == 200
    return document.json()


def create_source_and_target_documents(client, admin_header):
    definition = create_definition(client, admin_header)
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content=(
            "<Transmission>"
            "<Shipment><ShipmentGid>OTM1.SYNTHETIC</ShipmentGid>"
            "<ShipmentStop><StopSequence>1</StopSequence></ShipmentStop>"
            "</Shipment>"
            "</Transmission>"
        ),
    )
    target = create_schema_document(
        client,
        admin_header,
        definition["id"],
        payload_role="TARGET_SAMPLE",
        payload_format="JSON",
        file_name="delivery.json",
        content='{"header":{"shipmentId":"SYNTHETIC"},"deliveries":[{"sequence":1}]}',
    )
    return definition, source, target


def mapping_payload(source, target, **overrides):
    payload = {
        "source_schema_document_id": source["id"],
        "target_schema_document_id": target["id"],
        "source_path": "/Transmission/Shipment/ShipmentGid",
        "target_path": "$.header.shipmentId",
        "transform_type": "DIRECT",
        "description": "Synthetic direct mapping.",
        "sequence_index": 10,
    }
    payload.update(overrides)
    return payload


def test_integration_mappings_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "integration_mappings" in table_names


def test_create_integration_mapping_validates_schema_paths(client, admin_header, db_session):
    definition, source, target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json=mapping_payload(source, target),
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    mapping = db_session.get(IntegrationMapping, payload["id"])
    assert mapping is not None
    assert payload["definition_id"] == definition["id"]
    assert payload["source_path"] == "/Transmission/Shipment/ShipmentGid"
    assert payload["target_path"] == "$.header.shipmentId"
    assert payload["transform_type"] == "DIRECT"
    assert "SYNTHETIC" not in str(payload)


def test_list_and_get_integration_mappings(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json=mapping_payload(source, target, sequence_index=2),
        headers=admin_header,
    )
    assert created.status_code == 200

    listing = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        headers=admin_header,
    )
    detail = client.get(
        f"/api/v1/modules/integration-mapping/mappings/{created.json()['id']}",
        headers=admin_header,
    )

    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == created.json()["id"]
    assert detail.status_code == 200
    assert detail.json()["id"] == created.json()["id"]


def test_create_integration_mapping_rejects_unknown_source_path(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json=mapping_payload(source, target, source_path="/Transmission/Missing"),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_MAPPING_PATH_INVALID"


def test_create_integration_mapping_rejects_missing_definition(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        "/api/v1/modules/integration-mapping/definitions/missing-definition/mappings",
        json=mapping_payload(source, target),
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
