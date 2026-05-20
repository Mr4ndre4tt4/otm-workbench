import json

from otm_workbench.models import AuditLog, DomainEvent
from tests.test_integration_mapping_definitions import definition_payload
from tests.test_integration_mapping_validation import create_full_valid_definition


def test_create_definition_records_audit_and_domain_event(client, admin_header, db_session):
    response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="IM_AUDIT_CREATE"),
        headers=admin_header,
    )

    assert response.status_code == 200
    definition = response.json()
    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "integration_mapping.definition.create")
        .one()
    )
    event = (
        db_session.query(DomainEvent)
        .filter(DomainEvent.event_type == "integration_mapping.definition.created")
        .one()
    )

    audit_metadata = json.loads(audit.metadata_json)
    event_payload = json.loads(event.payload_json)
    assert audit.target_type == "integration_definition"
    assert audit.target_id == definition["id"]
    assert audit_metadata["definition_id"] == definition["id"]
    assert audit_metadata["code"] == "IM_AUDIT_CREATE"
    assert event.source_module == "integration_mapping"
    assert event.aggregate_type == "integration_definition"
    assert event.aggregate_id == definition["id"]
    assert event_payload["definition_id"] == definition["id"]


def test_validate_definition_records_client_safe_audit_and_event(client, admin_header, db_session):
    definition, _source, _target = create_full_valid_definition(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/validate",
        headers=admin_header,
    )

    assert response.status_code == 200
    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "integration_mapping.definition.validate")
        .one()
    )
    event = (
        db_session.query(DomainEvent)
        .filter(DomainEvent.event_type == "integration_mapping.definition.validated")
        .one()
    )
    audit_metadata = json.loads(audit.metadata_json)
    event_payload = json.loads(event.payload_json)
    assert audit.target_id == definition["id"]
    assert audit_metadata["is_valid"] is True
    assert audit_metadata["issue_count"] == 0
    assert event_payload["definition_id"] == definition["id"]
    assert event_payload["is_valid"] is True
    combined = "\n".join([audit.metadata_json, event.payload_json])
    assert "<Transmission>" not in combined
    assert "DEMO-SHIPMENT" not in combined


def test_preview_and_generate_spec_record_audit_and_events(client, admin_header, db_session):
    definition, _source, _target = create_full_valid_definition(client, admin_header)

    preview_response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/preview",
        headers=admin_header,
    )
    spec_response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/generate-spec",
        headers=admin_header,
    )

    assert preview_response.status_code == 200
    assert spec_response.status_code == 200
    preview = preview_response.json()
    spec = spec_response.json()
    preview_audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "integration_mapping.definition.preview")
        .one()
    )
    spec_audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "integration_mapping.definition.generate_spec")
        .one()
    )
    preview_event = (
        db_session.query(DomainEvent)
        .filter(DomainEvent.event_type == "integration_mapping.definition.previewed")
        .one()
    )
    spec_event = (
        db_session.query(DomainEvent)
        .filter(DomainEvent.event_type == "integration_mapping.definition.spec_generated")
        .one()
    )

    preview_metadata = json.loads(preview_audit.metadata_json)
    spec_metadata = json.loads(spec_audit.metadata_json)
    assert preview_metadata["artifact_id"] == preview["artifact_id"]
    assert preview_metadata["job_id"] == preview["job_id"]
    assert spec_metadata["artifact_id"] == spec["artifact_id"]
    assert spec_metadata["job_id"] == spec["job_id"]
    assert preview_event.aggregate_id == definition["id"]
    assert spec_event.aggregate_id == definition["id"]
    combined = "\n".join(
        [
            preview_audit.metadata_json,
            spec_audit.metadata_json,
            preview_event.payload_json,
            spec_event.payload_json,
        ]
    )
    assert "<Transmission>" not in combined
    assert "DEMO-SHIPMENT" not in combined
