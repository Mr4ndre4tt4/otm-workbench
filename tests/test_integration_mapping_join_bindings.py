from sqlalchemy import inspect

from otm_workbench.models import IntegrationJoinBinding, IntegrationJoinBindingHop
from tests.test_integration_mapping_mappings import create_definition, create_schema_document


def planned_shipment_source_document(client, admin_header, definition_id: str):
    return create_schema_document(
        client,
        admin_header,
        definition_id,
        content=(
            "<Transmission>"
            "<Shipment>"
            "<ShipmentGid>OTM1.SHIPMENT_001</ShipmentGid>"
            "<ShipmentStop>"
            "<StopSequence>1</StopSequence>"
            "<ShipmentStopDetail><ShipUnitGid><Gid><Xid>SU-001</Xid></Gid></ShipUnitGid></ShipmentStopDetail>"
            "</ShipmentStop>"
            "<ShipUnit>"
            "<ShipUnitGid><Gid><Xid>SU-001</Xid></Gid></ShipUnitGid>"
            "<ShipUnitContent><ReleaseGid><Gid><Xid>REL-001</Xid></Gid></ReleaseGid></ShipUnitContent>"
            "</ShipUnit>"
            "<Release>"
            "<ReleaseGid><Gid><Xid>REL-001</Xid></Gid></ReleaseGid>"
            "<ReleaseRefnum>"
            "<ReleaseRefnumQualifierGid><Gid><Xid>RFN_CHAVE_ACESSO</Xid></Gid></ReleaseRefnumQualifierGid>"
            "<ReleaseRefnumValue>KEY-001</ReleaseRefnumValue>"
            "</ReleaseRefnum>"
            "</Release>"
            "</Shipment>"
            "</Transmission>"
        ),
    )


def join_binding_payload(source, **overrides):
    payload = {
        "source_schema_document_id": source["id"],
        "name": "Stop to release binding",
        "description": "Synthetic two-hop PlannedShipment join binding.",
        "root_collection_path": "/Transmission/Shipment/ShipmentStop",
        "target_collection_path": "/Transmission/Shipment/Release",
        "hops": [
            {
                "hop_sequence": 1,
                "left_collection_path": "/Transmission/Shipment/ShipmentStop",
                "left_value_path": "ShipmentStopDetail/ShipUnitGid/Gid/Xid",
                "right_collection_path": "/Transmission/Shipment/ShipUnit",
                "right_value_path": "ShipUnitGid/Gid/Xid",
                "operator": "EQ",
                "result_alias": "stop_ship_unit",
            },
            {
                "hop_sequence": 2,
                "left_collection_path": "/Transmission/Shipment/ShipUnit",
                "left_value_path": "ShipUnitContent/ReleaseGid/Gid/Xid",
                "right_collection_path": "/Transmission/Shipment/Release",
                "right_value_path": "ReleaseGid/Gid/Xid",
                "operator": "EQ",
                "result_alias": "ship_unit_release",
            },
        ],
        "sequence_index": 10,
    }
    payload.update(overrides)
    return payload


def test_integration_join_binding_tables_exist_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "integration_join_bindings" in table_names
    assert "integration_join_binding_hops" in table_names


def test_create_list_and_get_integration_join_binding(client, admin_header, db_session):
    definition = create_definition(client, admin_header)
    source = planned_shipment_source_document(client, admin_header, definition["id"])

    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/join-bindings",
        json=join_binding_payload(source),
        headers=admin_header,
    )

    assert created.status_code == 200
    payload = created.json()
    binding = db_session.get(IntegrationJoinBinding, payload["id"])
    hops = db_session.query(IntegrationJoinBindingHop).filter_by(binding_id=payload["id"]).all()
    assert binding is not None
    assert len(hops) == 2
    assert payload["definition_id"] == definition["id"]
    assert payload["root_collection_path"] == "/Transmission/Shipment/ShipmentStop"
    assert payload["target_collection_path"] == "/Transmission/Shipment/Release"
    assert [hop["result_alias"] for hop in payload["hops"]] == ["stop_ship_unit", "ship_unit_release"]
    assert "SYNTHETIC" not in str(payload)

    listing = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/join-bindings",
        headers=admin_header,
    )
    detail = client.get(
        f"/api/v1/modules/integration-mapping/join-bindings/{payload['id']}",
        headers=admin_header,
    )

    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert detail.status_code == 200
    assert detail.json()["id"] == payload["id"]


def test_create_integration_join_binding_rejects_duplicate_alias(client, admin_header):
    definition = create_definition(client, admin_header)
    source = planned_shipment_source_document(client, admin_header, definition["id"])
    payload = join_binding_payload(source)
    payload["hops"][1]["result_alias"] = "stop_ship_unit"

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/join-bindings",
        json=payload,
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_JOIN_BINDING_ALIAS_INVALID"


def test_preview_integration_definition_emits_multi_hop_join_binding_provenance(client, admin_header):
    definition = create_definition(client, admin_header)
    source = planned_shipment_source_document(client, admin_header, definition["id"])
    target = create_schema_document(
        client,
        admin_header,
        definition["id"],
        payload_role="TARGET_SAMPLE",
        payload_format="JSON",
        file_name="delivery.json",
        content='{"header":{"shipmentId":""}}',
    )
    mapping = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json={
            "source_schema_document_id": source["id"],
            "target_schema_document_id": target["id"],
            "source_path": "/Transmission/Shipment/ShipmentGid",
            "target_path": "$.header.shipmentId",
            "transform_type": "DIRECT",
            "description": "Scalar mapping with multi-hop binding provenance.",
            "sequence_index": 1,
        },
        headers=admin_header,
    )
    binding = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/join-bindings",
        json=join_binding_payload(source),
        headers=admin_header,
    )
    assert mapping.status_code == 200
    assert binding.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview"]["mode"] == "synthetic_executable_json"
    assert payload["preview"]["target_json"] == {"header": {"shipmentId": "OTM1.SHIPMENT_001"}}
    assert payload["preview"]["multi_hop_join_provenance"] == [
        {
            "binding_id": binding.json()["id"],
            "hop_sequence": 1,
            "result_alias": "stop_ship_unit",
            "left_collection_path": "/Transmission/Shipment/ShipmentStop",
            "right_collection_path": "/Transmission/Shipment/ShipUnit",
            "left_item_path": "/Transmission/Shipment/ShipmentStop[1]/ShipmentStopDetail/ShipUnitGid/Gid/Xid",
            "right_item_path": "/Transmission/Shipment/ShipUnit[1]/ShipUnitGid/Gid/Xid",
            "operator": "EQ",
            "result": True,
        },
        {
            "binding_id": binding.json()["id"],
            "hop_sequence": 2,
            "result_alias": "ship_unit_release",
            "left_collection_path": "/Transmission/Shipment/ShipUnit",
            "right_collection_path": "/Transmission/Shipment/Release",
            "left_item_path": "/Transmission/Shipment/ShipUnit[1]/ShipUnitContent/ReleaseGid/Gid/Xid",
            "right_item_path": "/Transmission/Shipment/Release[1]/ReleaseGid/Gid/Xid",
            "operator": "EQ",
            "result": True,
        },
    ]
