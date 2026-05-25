from tests.test_integration_mapping_definitions import definition_payload
from tests.test_integration_mapping_mappings import create_schema_document, create_source_and_target_documents


def test_suggest_integration_mappings_returns_backend_owned_semantic_matches(client, admin_header):
    definition, source, target = create_source_and_target_documents(client, admin_header)

    response = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mapping-suggestions",
        params={
            "source_schema_document_id": source["id"],
            "target_schema_document_id": target["id"],
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    first = payload["items"][0]
    assert first == {
        "id": f"{source['id']}:/Transmission/Shipment/ShipmentGid->{target['id']}:$.header.shipmentId",
        "definition_id": definition["id"],
        "source_schema_document_id": source["id"],
        "target_schema_document_id": target["id"],
        "source_path": "/Transmission/Shipment/ShipmentGid",
        "target_path": "$.header.shipmentId",
        "transform_type": "DIRECT",
        "confidence": 0.9,
        "reason": "Normalized schema leaf names match: shipmentid",
    }


def test_suggest_integration_mappings_rejects_schema_outside_definition(client, admin_header):
    definition, source, _target = create_source_and_target_documents(client, admin_header)
    created = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="PS_MAPPING_SUGGESTIONS_OTHER"),
        headers=admin_header,
    )
    assert created.status_code == 200
    other_definition = created.json()
    other_target = create_schema_document(
        client,
        admin_header,
        other_definition["id"],
        payload_role="TARGET_SAMPLE",
        payload_format="JSON",
        file_name="other.json",
        content='{"header":{"shipmentId":"SYNTHETIC"}}',
    )

    response = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mapping-suggestions",
        params={
            "source_schema_document_id": source["id"],
            "target_schema_document_id": other_target["id"],
        },
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_MAPPING_SUGGESTION_SCHEMA_DOCUMENT_INVALID"
