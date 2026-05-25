import json
from pathlib import Path

from otm_workbench.models import Artifact, IntegrationMapping, Job
from tests.test_integration_mapping_loops import loop_payload
from tests.test_integration_mapping_lookups import lookup_payload
from tests.test_integration_mapping_joins import join_payload
from tests.test_integration_mapping_mappings import (
    create_definition,
    create_schema_document,
    create_source_and_target_documents,
)
from tests.test_integration_mapping_validation import create_full_valid_definition


def test_preview_integration_definition_creates_job_and_artifact(client, admin_header, db_session):
    definition, _source, _target = create_full_valid_definition(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["definition_id"] == definition["id"]
    assert payload["status"] == "SUCCEEDED"
    assert payload["validation"]["is_valid"] is True
    assert payload["preview"]["mode"] == "synthetic_metadata_only"
    assert payload["preview"]["external_calls_executed"] is False
    assert payload["preview"]["entity_counts"] == {
        "mappings": 1,
        "loops": 1,
        "joins": 1,
        "lookups": 1,
    }

    job = db_session.get(Job, payload["job_id"])
    artifact = db_session.get(Artifact, payload["artifact_id"])
    assert job is not None
    assert job.job_type == "INTEGRATION_MAPPING_PREVIEW"
    assert job.source_module == "integration_mapping"
    assert job.status == "SUCCEEDED"
    assert job.progress == 100
    assert "SYNTHETIC" not in job.result_json
    assert artifact is not None
    assert artifact.source_module == "integration_mapping"
    assert artifact.artifact_type == "integration_preview"
    assert artifact.content_type == "application/json"

    artifact_payload = json.loads(Path(artifact.file_path).read_text(encoding="utf-8"))
    assert artifact_payload["definition_id"] == definition["id"]
    assert artifact_payload["preview"]["external_calls_executed"] is False
    assert "SYNTHETIC" not in json.dumps(artifact_payload)


def test_preview_integration_definition_materializes_direct_json_with_provenance(
    client,
    admin_header,
    db_session,
):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json={
            "source_schema_document_id": source["id"],
            "target_schema_document_id": target["id"],
            "source_path": "/Transmission/Shipment/ShipmentGid",
            "target_path": "$.header.shipmentId",
            "transform_type": "DIRECT",
            "description": "Executable direct preview mapping.",
            "sequence_index": 1,
        },
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview"]["mode"] == "synthetic_executable_json"
    assert payload["preview"]["target_json"] == {"header": {"shipmentId": "OTM1.SYNTHETIC"}}
    assert payload["preview"]["field_provenance"] == [
        {
            "mapping_id": created.json()["id"],
            "source_path": "/Transmission/Shipment/ShipmentGid",
            "target_path": "$.header.shipmentId",
            "transform_type": "DIRECT",
            "value_policy": "copied_from_synthetic_source",
        }
    ]
    artifact = db_session.get(Artifact, payload["artifact_id"])
    artifact_payload = json.loads(Path(artifact.file_path).read_text(encoding="utf-8"))
    assert artifact_payload["preview"]["target_json"] == {"header": {"shipmentId": "OTM1.SYNTHETIC"}}
    assert artifact_payload["preview"]["field_provenance"][0]["mapping_id"] == created.json()["id"]


def test_preview_integration_definition_materializes_constant_transform_with_provenance(
    client,
    admin_header,
):
    definition = create_definition(client, admin_header)
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content=(
            "<Transmission>"
            "<Shipment><ShipmentGid>OTM1.SYNTHETIC</ShipmentGid></Shipment>"
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
        content='{"header":{"sourceSystem":""}}',
    )
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json={
            "source_schema_document_id": source["id"],
            "target_schema_document_id": target["id"],
            "source_path": "/Transmission/Shipment/ShipmentGid",
            "target_path": "$.header.sourceSystem",
            "transform_type": "CONSTANT",
            "transform_config": {"value": "OTM"},
            "description": "Fixed source system mapping.",
            "sequence_index": 1,
        },
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview"]["mode"] == "synthetic_executable_json"
    assert payload["preview"]["target_json"] == {"header": {"sourceSystem": "OTM"}}
    assert payload["preview"]["field_provenance"] == [
        {
            "mapping_id": created.json()["id"],
            "source_path": "/Transmission/Shipment/ShipmentGid",
            "target_path": "$.header.sourceSystem",
            "transform_type": "CONSTANT",
            "value_policy": "constant_from_transform_config",
        }
    ]


def test_preview_integration_definition_materializes_otm_glogdate_as_iso8601(
    client,
    admin_header,
):
    definition = create_definition(client, admin_header)
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content=(
            "<Transmission>"
            "<Shipment>"
            "<StartDt><GLogDate>20260525113045</GLogDate></StartDt>"
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
        content='{"header":{"emissionDate":""}}',
    )
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json={
            "source_schema_document_id": source["id"],
            "target_schema_document_id": target["id"],
            "source_path": "/Transmission/Shipment/StartDt/GLogDate",
            "target_path": "$.header.emissionDate",
            "transform_type": "DATE_FORMAT",
            "transform_config": {
                "source_format": "OTM_GLOGDATE",
                "target_format": "ISO8601",
                "timezone_offset": "-03:00",
            },
            "description": "Format OTM GLogDate as ISO 8601.",
            "sequence_index": 1,
        },
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview"]["mode"] == "synthetic_executable_json"
    assert payload["preview"]["target_json"] == {
        "header": {"emissionDate": "2026-05-25T11:30:45-03:00"}
    }
    assert payload["preview"]["field_provenance"] == [
        {
            "mapping_id": created.json()["id"],
            "source_path": "/Transmission/Shipment/StartDt/GLogDate",
            "target_path": "$.header.emissionDate",
            "transform_type": "DATE_FORMAT",
            "value_policy": "date_format_from_transform_config",
        }
    ]


def test_preview_integration_definition_materializes_concat_transform_with_provenance(
    client,
    admin_header,
):
    definition = create_definition(client, admin_header)
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content=(
            "<Transmission>"
            "<Shipment>"
            "<SourceLocation><Xid>ORIGIN</Xid></SourceLocation>"
            "<DestinationLocation><Xid>DEST</Xid></DestinationLocation>"
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
        content='{"header":{"lane":""}}',
    )
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json={
            "source_schema_document_id": source["id"],
            "target_schema_document_id": target["id"],
            "source_path": "/Transmission/Shipment/SourceLocation/Xid",
            "target_path": "$.header.lane",
            "transform_type": "CONCAT",
            "transform_config": {
                "parts": [
                    {"type": "source_path", "path": "/Transmission/Shipment/SourceLocation/Xid"},
                    {"type": "literal", "value": " -> "},
                    {"type": "source_path", "path": "/Transmission/Shipment/DestinationLocation/Xid"},
                ]
            },
            "description": "Build synthetic lane label.",
            "sequence_index": 1,
        },
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview"]["mode"] == "synthetic_executable_json"
    assert payload["preview"]["target_json"] == {"header": {"lane": "ORIGIN -> DEST"}}
    assert payload["preview"]["field_provenance"] == [
        {
            "mapping_id": created.json()["id"],
            "source_path": "/Transmission/Shipment/SourceLocation/Xid",
            "target_path": "$.header.lane",
            "transform_type": "CONCAT",
            "value_policy": "concat_from_transform_config",
        }
    ]


def test_preview_integration_definition_materializes_mock_lookup_with_provenance(
    client,
    admin_header,
):
    definition = create_definition(client, admin_header)
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content=(
            "<Transmission>"
            "<Shipment><ShipmentGid>OTM1.SHIPMENT_001</ShipmentGid></Shipment>"
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
        content='{"header":{"carrierName":""}}',
    )
    lookup = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/lookups",
        json=lookup_payload(
            source,
            target,
            output_path="$.header.carrierName",
            mock_response_json='{"carrierName":"Synthetic Carrier"}',
        ),
        headers=admin_header,
    )
    assert lookup.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview"]["mode"] == "synthetic_executable_json"
    assert payload["preview"]["target_json"] == {"header": {"carrierName": "Synthetic Carrier"}}
    assert payload["preview"]["field_provenance"] == [
        {
            "lookup_id": lookup.json()["id"],
            "input_path": "/Transmission/Shipment/ShipmentGid",
            "output_path": "$.header.carrierName",
            "lookup_type": "MOCK",
            "value_policy": "mock_lookup_response",
        }
    ]


def test_preview_integration_definition_materializes_scalar_mapping_and_mock_lookup_together(
    client,
    admin_header,
):
    definition = create_definition(client, admin_header)
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content=(
            "<Transmission>"
            "<Shipment><ShipmentGid>OTM1.SHIPMENT_001</ShipmentGid></Shipment>"
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
        content='{"header":{"shipmentId":"","carrierName":""}}',
    )
    mapping = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json={
            "source_schema_document_id": source["id"],
            "target_schema_document_id": target["id"],
            "source_path": "/Transmission/Shipment/ShipmentGid",
            "target_path": "$.header.shipmentId",
            "transform_type": "DIRECT",
            "description": "Direct shipment mapping.",
            "sequence_index": 1,
        },
        headers=admin_header,
    )
    lookup = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/lookups",
        json=lookup_payload(
            source,
            target,
            output_path="$.header.carrierName",
            mock_response_json='{"carrierName":"Synthetic Carrier"}',
            sequence_index=2,
        ),
        headers=admin_header,
    )
    assert mapping.status_code == 200
    assert lookup.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview"]["mode"] == "synthetic_executable_json"
    assert payload["preview"]["target_json"] == {
        "header": {
            "shipmentId": "OTM1.SHIPMENT_001",
            "carrierName": "Synthetic Carrier",
        }
    }
    assert payload["preview"]["field_provenance"] == [
        {
            "mapping_id": mapping.json()["id"],
            "source_path": "/Transmission/Shipment/ShipmentGid",
            "target_path": "$.header.shipmentId",
            "transform_type": "DIRECT",
            "value_policy": "copied_from_synthetic_source",
        },
        {
            "lookup_id": lookup.json()["id"],
            "input_path": "/Transmission/Shipment/ShipmentGid",
            "output_path": "$.header.carrierName",
            "lookup_type": "MOCK",
            "value_policy": "mock_lookup_response",
        },
    ]


def test_preview_integration_definition_allows_scalar_join_guard_with_provenance(
    client,
    admin_header,
):
    definition = create_definition(client, admin_header)
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content=(
            "<Transmission>"
            "<Shipment>"
            "<ShipmentGid>OTM1.SHIPMENT_001</ShipmentGid>"
            "<ShipmentRef>OTM1.SHIPMENT_001</ShipmentRef>"
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
            "description": "Direct shipment mapping guarded by join.",
            "sequence_index": 1,
        },
        headers=admin_header,
    )
    join = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/joins",
        json=join_payload(
            source,
            left_path="/Transmission/Shipment/ShipmentGid",
            right_path="/Transmission/Shipment/ShipmentRef",
            operator="EQ",
            sequence_index=2,
        ),
        headers=admin_header,
    )
    assert mapping.status_code == 200
    assert join.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview"]["mode"] == "synthetic_executable_json"
    assert payload["preview"]["target_json"] == {"header": {"shipmentId": "OTM1.SHIPMENT_001"}}
    assert payload["preview"]["join_provenance"] == [
        {
            "join_id": join.json()["id"],
            "left_path": "/Transmission/Shipment/ShipmentGid",
            "right_path": "/Transmission/Shipment/ShipmentRef",
            "operator": "EQ",
            "result": True,
        }
    ]


def test_preview_integration_definition_materializes_loop_mock_lookup_with_provenance(
    client,
    admin_header,
):
    definition = create_definition(client, admin_header)
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content=(
            "<Transmission>"
            "<Shipment>"
            "<ShipmentStop><StopSequence>1</StopSequence><StopType>D</StopType></ShipmentStop>"
            "<ShipmentStop><StopSequence>2</StopSequence><StopType>D</StopType></ShipmentStop>"
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
        content='{"deliveries":[{"sequence":"","carrierName":""}]}',
    )
    loop = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/loops",
        json=loop_payload(source, target),
        headers=admin_header,
    )
    lookup = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/lookups",
        json=lookup_payload(
            source,
            target,
            input_path="/Transmission/Shipment/ShipmentStop/StopSequence",
            output_path="$.deliveries[].carrierName",
            mock_response_json='{"carrierName":"Synthetic Carrier"}',
        ),
        headers=admin_header,
    )
    assert loop.status_code == 200
    assert lookup.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview"]["mode"] == "synthetic_executable_json"
    assert payload["preview"]["target_json"] == {
        "deliveries": [
            {"carrierName": "Synthetic Carrier"},
            {"carrierName": "Synthetic Carrier"},
        ]
    }
    assert payload["preview"]["field_provenance"] == [
        {
            "loop_id": loop.json()["id"],
            "lookup_id": lookup.json()["id"],
            "input_path": "/Transmission/Shipment/ShipmentStop/StopSequence",
            "source_item_path": "/Transmission/Shipment/ShipmentStop[1]/StopSequence",
            "output_path": "$.deliveries[].carrierName",
            "target_item_path": "$.deliveries[0].carrierName",
            "lookup_type": "MOCK",
            "value_policy": "mock_lookup_response",
        },
        {
            "loop_id": loop.json()["id"],
            "lookup_id": lookup.json()["id"],
            "input_path": "/Transmission/Shipment/ShipmentStop/StopSequence",
            "source_item_path": "/Transmission/Shipment/ShipmentStop[2]/StopSequence",
            "output_path": "$.deliveries[].carrierName",
            "target_item_path": "$.deliveries[1].carrierName",
            "lookup_type": "MOCK",
            "value_policy": "mock_lookup_response",
        },
    ]


def test_preview_integration_definition_materializes_loop_json_array_with_provenance(
    client,
    admin_header,
):
    definition = create_definition(client, admin_header)
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content=(
            "<Transmission>"
            "<Shipment>"
            "<ShipmentStop><StopSequence>1</StopSequence><StopType>D</StopType></ShipmentStop>"
            "<ShipmentStop><StopSequence>2</StopSequence><StopType>D</StopType></ShipmentStop>"
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
        content='{"deliveries":[{"sequence":"","type":""}]}',
    )
    loop = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/loops",
        json=loop_payload(source, target),
        headers=admin_header,
    )
    mapping = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json={
            "source_schema_document_id": source["id"],
            "target_schema_document_id": target["id"],
            "source_path": "/Transmission/Shipment/ShipmentStop/StopSequence",
            "target_path": "$.deliveries[].sequence",
            "transform_type": "DIRECT",
            "description": "Loop-scoped stop sequence mapping.",
            "sequence_index": 1,
        },
        headers=admin_header,
    )
    assert loop.status_code == 200
    assert mapping.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview"]["mode"] == "synthetic_executable_json"
    assert payload["preview"]["target_json"] == {
        "deliveries": [
            {"sequence": "1"},
            {"sequence": "2"},
        ]
    }
    assert payload["preview"]["field_provenance"] == [
        {
            "loop_id": loop.json()["id"],
            "mapping_id": mapping.json()["id"],
            "source_path": "/Transmission/Shipment/ShipmentStop/StopSequence",
            "source_item_path": "/Transmission/Shipment/ShipmentStop[1]/StopSequence",
            "target_path": "$.deliveries[].sequence",
            "target_item_path": "$.deliveries[0].sequence",
            "transform_type": "DIRECT",
            "value_policy": "copied_from_synthetic_loop_item",
        },
        {
            "loop_id": loop.json()["id"],
            "mapping_id": mapping.json()["id"],
            "source_path": "/Transmission/Shipment/ShipmentStop/StopSequence",
            "source_item_path": "/Transmission/Shipment/ShipmentStop[2]/StopSequence",
            "target_path": "$.deliveries[].sequence",
            "target_item_path": "$.deliveries[1].sequence",
            "transform_type": "DIRECT",
            "value_policy": "copied_from_synthetic_loop_item",
        },
    ]


def test_preview_integration_definition_allows_loop_scoped_join_guard_with_provenance(
    client,
    admin_header,
):
    definition = create_definition(client, admin_header)
    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        content=(
            "<Transmission>"
            "<Shipment>"
            "<ShipmentStop><StopSequence>1</StopSequence><StopRef>1</StopRef></ShipmentStop>"
            "<ShipmentStop><StopSequence>2</StopSequence><StopRef>2</StopRef></ShipmentStop>"
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
        content='{"deliveries":[{"sequence":""}]}',
    )
    loop = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/loops",
        json=loop_payload(source, target),
        headers=admin_header,
    )
    mapping = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json={
            "source_schema_document_id": source["id"],
            "target_schema_document_id": target["id"],
            "source_path": "/Transmission/Shipment/ShipmentStop/StopSequence",
            "target_path": "$.deliveries[].sequence",
            "transform_type": "DIRECT",
            "description": "Loop-scoped stop sequence mapping guarded by join.",
            "sequence_index": 1,
        },
        headers=admin_header,
    )
    join = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/joins",
        json=join_payload(
            source,
            left_path="/Transmission/Shipment/ShipmentStop/StopSequence",
            right_path="/Transmission/Shipment/ShipmentStop/StopRef",
            operator="EQ",
            sequence_index=2,
        ),
        headers=admin_header,
    )
    assert loop.status_code == 200
    assert mapping.status_code == 200
    assert join.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview"]["mode"] == "synthetic_executable_json"
    assert payload["preview"]["target_json"] == {
        "deliveries": [
            {"sequence": "1"},
            {"sequence": "2"},
        ]
    }
    assert payload["preview"]["join_provenance"] == [
        {
            "loop_id": loop.json()["id"],
            "join_id": join.json()["id"],
            "left_path": "/Transmission/Shipment/ShipmentStop/StopSequence",
            "right_path": "/Transmission/Shipment/ShipmentStop/StopRef",
            "left_item_path": "/Transmission/Shipment/ShipmentStop[1]/StopSequence",
            "right_item_path": "/Transmission/Shipment/ShipmentStop[1]/StopRef",
            "operator": "EQ",
            "result": True,
        },
        {
            "loop_id": loop.json()["id"],
            "join_id": join.json()["id"],
            "left_path": "/Transmission/Shipment/ShipmentStop/StopSequence",
            "right_path": "/Transmission/Shipment/ShipmentStop/StopRef",
            "left_item_path": "/Transmission/Shipment/ShipmentStop[2]/StopSequence",
            "right_item_path": "/Transmission/Shipment/ShipmentStop[2]/StopRef",
            "operator": "EQ",
            "result": True,
        },
    ]


def test_preview_integration_definition_rejects_invalid_metadata(client, admin_header, db_session):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    db_session.add(
        IntegrationMapping(
            definition_id=definition["id"],
            source_schema_document_id=source["id"],
            target_schema_document_id=target["id"],
            source_path="/Transmission/Missing",
            target_path="$.header.shipmentId",
            transform_type="DIRECT",
            description="Invalid synthetic mapping.",
            sequence_index=1,
            status="ACTIVE",
            created_by="qa@example.test",
        )
    )
    db_session.commit()

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["code"] == "INTEGRATION_PREVIEW_VALIDATION_FAILED"
    assert payload["details"]["issue_count"] == 1
    assert db_session.query(Job).filter(Job.source_module == "integration_mapping").count() == 0


def test_preview_integration_definition_rejects_missing_definition(client, admin_header):
    response = client.post(
        "/api/v1/modules/integration-mapping/definitions/missing-definition/preview",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
