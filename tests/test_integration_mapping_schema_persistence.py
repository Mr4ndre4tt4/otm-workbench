from sqlalchemy import inspect

from otm_workbench.models import IntegrationSchemaDocument, IntegrationSchemaNode
from tests.test_integration_mapping_definitions import definition_payload
from tests.test_integration_mapping_payload_artifacts import payload_import


def create_definition(client, admin_header, code="PS_SCHEMA_DOC"):
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


def test_integration_schema_tables_exist_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "integration_schema_documents" in table_names
    assert "integration_schema_nodes" in table_names


def test_create_schema_document_persists_nodes_from_payload_artifact(client, admin_header, db_session):
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
        f"/api/v1/modules/integration-mapping/payload-artifacts/{payload_artifact['id']}/schema-documents",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    document = db_session.get(IntegrationSchemaDocument, payload["id"])
    nodes = (
        db_session.query(IntegrationSchemaNode)
        .filter(IntegrationSchemaNode.schema_document_id == payload["id"])
        .order_by(IntegrationSchemaNode.sequence_index)
        .all()
    )
    paths = [node.path for node in nodes]
    assert document is not None
    assert payload["definition_id"] == definition["id"]
    assert payload["payload_artifact_id"] == payload_artifact["id"]
    assert payload["payload_format"] == "XML"
    assert payload["node_count"] == len(nodes)
    assert "/Transmission/Shipment/ShipmentGid" in paths
    assert "/Transmission/Shipment/ShipmentStop/StopSequence" in paths
    assert "OTM1.SYNTHETIC" not in str(payload)


def test_list_schema_documents_and_nodes(client, admin_header):
    definition = create_definition(client, admin_header, code="JSON_SCHEMA_DOC")
    payload_artifact = create_payload_artifact(
        client,
        admin_header,
        definition["id"],
        payload_format="JSON",
        file_name="delivery.json",
        content='{"header":{"id":"SYNTHETIC"},"deliveries":[{"number":"N1","weight":10}]}',
    )
    created = client.post(
        f"/api/v1/modules/integration-mapping/payload-artifacts/{payload_artifact['id']}/schema-documents",
        headers=admin_header,
    )
    assert created.status_code == 200
    schema_document_id = created.json()["id"]

    documents = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/schema-documents",
        headers=admin_header,
    )
    nodes = client.get(
        f"/api/v1/modules/integration-mapping/schema-documents/{schema_document_id}/nodes",
        headers=admin_header,
    )

    assert documents.status_code == 200
    assert documents.json()["total"] == 1
    assert nodes.status_code == 200
    node_paths = [node["path"] for node in nodes.json()["items"]]
    assert "$.header.id" in node_paths
    assert "$.deliveries[].weight" in node_paths
    assert "SYNTHETIC" not in str(nodes.json())


def test_create_schema_document_rejects_missing_payload_artifact(client, admin_header):
    response = client.post(
        "/api/v1/modules/integration-mapping/payload-artifacts/missing-artifact/schema-documents",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_PAYLOAD_ARTIFACT_NOT_FOUND"
