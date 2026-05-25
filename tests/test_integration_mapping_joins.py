from sqlalchemy import inspect

from otm_workbench.models import IntegrationJoinRule
from tests.test_integration_mapping_mappings import create_source_and_target_documents


def join_payload(source, **overrides):
    payload = {
        "source_schema_document_id": source["id"],
        "left_path": "/Transmission/Shipment/ShipmentGid",
        "right_path": "/Transmission/Shipment/ShipmentStop/StopSequence",
        "operator": "EQ",
        "name": "Synthetic shipment stop join",
        "description": "Metadata-only join declaration for synthetic payload paths.",
        "sequence_index": 30,
    }
    payload.update(overrides)
    return payload


def test_integration_join_rules_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "integration_join_rules" in table_names


def test_create_integration_join_rule_validates_source_paths(client, admin_header, db_session):
    definition, source, _target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/joins",
        json=join_payload(source),
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    join_rule = db_session.get(IntegrationJoinRule, payload["id"])
    assert join_rule is not None
    assert payload["definition_id"] == definition["id"]
    assert payload["left_path"] == "/Transmission/Shipment/ShipmentGid"
    assert payload["right_path"] == "/Transmission/Shipment/ShipmentStop/StopSequence"
    assert payload["operator"] == "EQ"
    assert payload["status"] == "ACTIVE"
    assert "SYNTHETIC" not in str(payload)


def test_list_and_get_integration_join_rules(client, admin_header):
    definition, source, _target = create_source_and_target_documents(client, admin_header)
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/joins",
        json=join_payload(source, sequence_index=7),
        headers=admin_header,
    )
    assert created.status_code == 200

    listing = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/joins",
        headers=admin_header,
    )
    detail = client.get(
        f"/api/v1/modules/integration-mapping/joins/{created.json()['id']}",
        headers=admin_header,
    )

    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == created.json()["id"]
    assert detail.status_code == 200
    assert detail.json()["id"] == created.json()["id"]


def test_create_integration_join_rule_rejects_unknown_source_path(client, admin_header):
    definition, source, _target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/joins",
        json=join_payload(source, right_path="/Transmission/Missing"),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_JOIN_PATH_INVALID"


def test_create_integration_join_rule_rejects_unknown_operator(client, admin_header):
    definition, source, _target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/joins",
        json=join_payload(source, operator="CONTAINS_SCRIPT"),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_JOIN_OPERATOR_INVALID"


def test_create_integration_join_rule_rejects_same_source_path_pair(client, admin_header):
    definition, source, _target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/joins",
        json=join_payload(source, right_path="/Transmission/Shipment/ShipmentGid"),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_JOIN_SAME_PATH"


def test_create_integration_join_rule_rejects_missing_definition(client, admin_header):
    _definition, source, _target = create_source_and_target_documents(client, admin_header)

    response = client.post(
        "/api/v1/modules/integration-mapping/definitions/missing-definition/joins",
        json=join_payload(source),
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
