from tests.test_integration_mapping_definitions import definition_payload
from tests.test_integration_mapping_payload_artifacts import payload_import


def create_definition(client, admin_header, code="PS_SCHEMA_TREE"):
    response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code=code),
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def create_payload_artifact(client, admin_header, definition_id, **overrides):
    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition_id}/payload-artifacts",
        json=payload_import(**overrides),
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def paths_from_tree(node):
    paths = [node["path"]]
    for child in node.get("children", []):
        paths.extend(paths_from_tree(child))
    return paths


def test_parse_xml_payload_artifact_returns_schema_tree(client, admin_header):
    definition = create_definition(client, admin_header)
    payload_artifact = create_payload_artifact(
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

    response = client.post(
        f"/api/v1/modules/integration-mapping/payload-artifacts/{payload_artifact['id']}/parse-schema-tree",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    tree = payload["tree"]
    paths = paths_from_tree(tree)
    assert payload["payload_artifact_id"] == payload_artifact["id"]
    assert payload["payload_format"] == "XML"
    assert tree["name"] == "Transmission"
    assert tree["node_type"] == "object"
    assert "/Transmission/Shipment/ShipmentGid" in paths
    assert "/Transmission/Shipment/ShipmentStop/StopSequence" in paths
    assert "OTM1.SYNTHETIC" not in str(payload)


def test_parse_json_payload_artifact_returns_schema_tree(client, admin_header):
    definition = create_definition(client, admin_header, code="JSON_SCHEMA_TREE")
    payload_artifact = create_payload_artifact(
        client,
        admin_header,
        definition["id"],
        payload_format="JSON",
        file_name="delivery.json",
        content='{"header":{"id":"SYNTHETIC"},"deliveries":[{"number":"N1","weight":10}]}',
    )

    response = client.post(
        f"/api/v1/modules/integration-mapping/payload-artifacts/{payload_artifact['id']}/parse-schema-tree",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    tree = payload["tree"]
    paths = paths_from_tree(tree)
    assert payload["payload_format"] == "JSON"
    assert tree["name"] == "$"
    assert tree["node_type"] == "object"
    assert "$.header.id" in paths
    assert "$.deliveries[]" in paths
    assert "$.deliveries[].weight" in paths
    assert "SYNTHETIC" not in str(payload)


def test_parse_schema_tree_rejects_missing_payload_artifact(client, admin_header):
    response = client.post(
        "/api/v1/modules/integration-mapping/payload-artifacts/missing-artifact/parse-schema-tree",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_PAYLOAD_ARTIFACT_NOT_FOUND"
