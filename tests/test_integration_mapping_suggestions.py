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
        "reason": "EXACT_NAME: normalized schema leaf names match: shipmentid",
    }


def test_suggest_integration_mappings_ranks_otm_context_synonyms(client, admin_header):
    definition = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="PS_MAPPING_SUGGESTIONS_CONTEXT"),
        headers=admin_header,
    ).json()
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content=(
            "<Transmission>"
            "<Shipment>"
            "<ShipmentStop><StopSequence>7</StopSequence></ShipmentStop>"
            "<Release><ReleaseRefnum><ReleaseRefnumValue>KEY-001</ReleaseRefnumValue></ReleaseRefnum></Release>"
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
        file_name="delivery_context.json",
        content='{"header":{"accessKey":""},"deliveries":[{"sequence":0}]}',
    )

    response = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mapping-suggestions",
        params={
            "source_schema_document_id": source["id"],
            "target_schema_document_id": target["id"],
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    suggestions = response.json()["items"]
    assert {
        "source_path": "/Transmission/Shipment/ShipmentStop/StopSequence",
        "target_path": "$.deliveries[].sequence",
        "transform_type": "DIRECT",
        "confidence": 0.82,
        "reason": "OTM_CONTEXT_SYNONYM: ShipmentStop StopSequence maps to delivery sequence",
    }.items() <= suggestions[0].items()
    assert any(
        item["source_path"] == "/Transmission/Shipment/Release/ReleaseRefnum/ReleaseRefnumValue"
        and item["target_path"] == "$.header.accessKey"
        and item["confidence"] == 0.78
        and item["reason"] == "OTM_REFNUM_ACCESS_KEY: ReleaseRefnumValue can populate accessKey"
        for item in suggestions
    )


def test_suggest_integration_mappings_marks_ambiguous_exact_matches(client, admin_header):
    definition = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="PS_MAPPING_SUGGESTIONS_AMBIGUOUS"),
        headers=admin_header,
    ).json()
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content="<Transmission><Shipment><ShipmentGid>OTM1.SYNTHETIC</ShipmentGid></Shipment></Transmission>",
    )
    target = create_schema_document(
        client,
        admin_header,
        definition["id"],
        payload_role="TARGET_SAMPLE",
        payload_format="JSON",
        file_name="ambiguous_delivery.json",
        content='{"header":{"shipmentId":"","shipment_id":""}}',
    )

    response = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mapping-suggestions",
        params={
            "source_schema_document_id": source["id"],
            "target_schema_document_id": target["id"],
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    first = response.json()["items"][0]
    assert first["source_path"] == "/Transmission/Shipment/ShipmentGid"
    assert first["target_path"] == "$.header.shipmentId"
    assert first["confidence"] == 0.75
    assert first["reason"] == "AMBIGUOUS_EXACT_NAME: 2 target nodes normalize to shipmentid"


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
