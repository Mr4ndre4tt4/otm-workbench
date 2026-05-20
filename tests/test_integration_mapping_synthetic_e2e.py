import json
from pathlib import Path

from otm_workbench.models import Artifact, AuditLog, DomainEvent, Job
from tests.test_integration_mapping_definitions import definition_payload
from tests.test_integration_mapping_joins import join_payload
from tests.test_integration_mapping_lookups import lookup_payload
from tests.test_integration_mapping_loops import loop_payload
from tests.test_integration_mapping_mappings import create_schema_document, mapping_payload


def test_planned_shipment_to_external_delivery_metadata_only_scenario(client, admin_header, db_session):
    definition_response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="PS_TO_EXTERNAL_DELIVERY_E2E"),
        headers=admin_header,
    )
    assert definition_response.status_code == 200
    definition = definition_response.json()

    source = create_schema_document(
        client,
        admin_header,
        definition["id"],
        file_name="planned_shipment_demo.xml",
        content=(
            "<Transmission>"
            "<Shipment>"
            "<ShipmentGid>DEMO.SHIPMENT_001</ShipmentGid>"
            "<ShipmentStop><StopSequence>1</StopSequence><StopType>D</StopType></ShipmentStop>"
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
        file_name="external_delivery_demo.json",
        content='{"header":{"shipmentId":"DEMO"},"deliveries":[{"sequence":1,"type":"D"}]}',
    )

    mapping_response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json=mapping_payload(source, target, description="Demo direct shipment id mapping."),
        headers=admin_header,
    )
    loop_response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/loops",
        json=loop_payload(source, target, description="Demo delivery stop loop."),
        headers=admin_header,
    )
    join_response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/joins",
        json=join_payload(source, description="Demo shipment-stop relation."),
        headers=admin_header,
    )
    lookup_response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/lookups",
        json=lookup_payload(source, target, mock_response_json='{"carrierName":"Demo Carrier"}'),
        headers=admin_header,
    )
    assert mapping_response.status_code == 200
    assert loop_response.status_code == 200
    assert join_response.status_code == 200
    assert lookup_response.status_code == 200

    validation_response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/validate",
        headers=admin_header,
    )
    preview_response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )
    spec_response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/generate-spec",
        headers=admin_header,
    )
    assert validation_response.status_code == 200
    assert preview_response.status_code == 200
    assert spec_response.status_code == 200

    validation = validation_response.json()
    preview = preview_response.json()
    spec = spec_response.json()
    assert validation["is_valid"] is True
    assert preview["validation"]["is_valid"] is True
    assert preview["preview"]["scenario"]["code"] == "planned_shipment_to_external_delivery"
    assert preview["preview"]["scenario"]["source_object"] == "OTM PlannedShipment"
    assert preview["preview"]["scenario"]["target_object"] == "External Delivery JSON"
    assert preview["preview"]["entity_counts"] == {
        "mappings": 1,
        "loops": 1,
        "joins": 1,
        "lookups": 1,
    }

    preview_artifact = db_session.get(Artifact, preview["artifact_id"])
    spec_artifact = db_session.get(Artifact, spec["artifact_id"])
    preview_job = db_session.get(Job, preview["job_id"])
    spec_job = db_session.get(Job, spec["job_id"])
    assert preview_artifact is not None
    assert spec_artifact is not None
    assert preview_job.status == "SUCCEEDED"
    assert spec_job.status == "SUCCEEDED"
    preview_artifact_payload = json.loads(Path(preview_artifact.file_path).read_text(encoding="utf-8"))
    spec_markdown = Path(spec_artifact.file_path).read_text(encoding="utf-8")
    assert preview_artifact_payload["preview"]["scenario"]["code"] == "planned_shipment_to_external_delivery"
    assert "## Synthetic Test Cases" in spec_markdown
    assert "DEMO.SHIPMENT_001" not in spec_markdown

    audit_actions = {
        row.action
        for row in db_session.query(AuditLog).filter(AuditLog.target_id == definition["id"]).all()
    }
    event_types = {
        row.event_type
        for row in db_session.query(DomainEvent).filter(DomainEvent.aggregate_id == definition["id"]).all()
    }
    assert {
        "integration_mapping.definition.create",
        "integration_mapping.definition.validate",
        "integration_mapping.definition.preview",
        "integration_mapping.definition.generate_spec",
    }.issubset(audit_actions)
    assert {
        "integration_mapping.definition.created",
        "integration_mapping.definition.validated",
        "integration_mapping.definition.previewed",
        "integration_mapping.definition.spec_generated",
    }.issubset(event_types)
