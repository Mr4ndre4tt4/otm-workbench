from pathlib import Path

from otm_workbench.models import Artifact, IntegrationMapping, Job
from tests.test_integration_mapping_definitions import create_project_with_environments, set_active_context
from tests.test_integration_mapping_enrichment import create_intermediate_document, enrichment_payload
from tests.test_integration_mapping_mappings import create_source_and_target_documents, mapping_payload
from tests.test_integration_mapping_response_handlers import (
    create_documents_with_response_status,
    response_handler_payload,
)
from tests.test_integration_mapping_validation import create_full_valid_definition


def test_generate_integration_spec_creates_markdown_artifact_and_job(client, admin_header, db_session):
    project_id, environment_id, _dev_id = create_project_with_environments(client, admin_header)
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )
    definition, _source, _target = create_full_valid_definition(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/generate-spec",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["definition_id"] == definition["id"]
    assert payload["status"] == "SUCCEEDED"
    assert payload["validation"]["is_valid"] is True
    assert payload["spec"]["format"] == "MARKDOWN"
    assert payload["spec"]["sections"] == [
        "Identification",
        "Schema Documents",
        "Mappings",
        "Loops",
        "Joins",
        "Enrichment Pipeline",
        "Lookups",
        "Response Handling",
        "Synthetic Test Cases",
    ]

    job = db_session.get(Job, payload["job_id"])
    artifact = db_session.get(Artifact, payload["artifact_id"])
    assert job is not None
    assert job.job_type == "INTEGRATION_MAPPING_GENERATE_SPEC"
    assert job.source_module == "integration_mapping"
    assert job.status == "SUCCEEDED"
    assert artifact is not None
    assert artifact.artifact_type == "integration_markdown_spec"
    assert artifact.content_type == "text/markdown"
    assert artifact.project_id == project_id
    assert artifact.environment_id == environment_id
    assert artifact.domain_name == "OTM1"
    assert artifact.visibility == "PROJECT"

    markdown = Path(artifact.file_path).read_text(encoding="utf-8")
    assert "# Integration Mapping Spec" in markdown
    assert "## Identification" in markdown
    assert "## Schema Documents" in markdown
    assert "## Mappings" in markdown
    assert "## Enrichment Pipeline" in markdown
    assert "## Synthetic Test Cases" in markdown
    assert "/Transmission/Shipment/ShipmentGid" in markdown
    assert "external calls are not executed" in markdown
    assert "SYNTHETIC" not in markdown
    assert "<Transmission>" not in markdown


def test_generate_integration_spec_rejects_invalid_metadata(client, admin_header, db_session):
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
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/generate-spec",
        headers=admin_header,
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["code"] == "INTEGRATION_SPEC_VALIDATION_FAILED"
    assert payload["details"]["issue_count"] == 1
    assert db_session.query(Job).filter(Job.job_type == "INTEGRATION_MAPPING_GENERATE_SPEC").count() == 0


def test_generate_integration_spec_allows_spec_ready_transform_config_gap(client, admin_header, db_session):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    db_session.add(
        IntegrationMapping(
            definition_id=definition["id"],
            source_schema_document_id=source["id"],
            target_schema_document_id=target["id"],
            source_path="/Transmission/Shipment/ShipmentGid",
            target_path="$.header.shipmentId",
            transform_type="DATE_FORMAT",
            description="Synthetic date format mapping without config.",
            sequence_index=1,
            status="ACTIVE",
            created_by="qa@example.test",
        )
    )
    db_session.commit()

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/generate-spec",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["validation"]["is_valid"] is False
    assert payload["validation"]["readiness"]["specification_ready"] is True
    assert payload["validation"]["readiness"]["preview_executable"] is False
    assert payload["status"] == "SUCCEEDED"


def test_generate_integration_spec_includes_persisted_transform_config(client, admin_header, db_session):
    definition, source, target = create_source_and_target_documents(client, admin_header)
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/mappings",
        json=mapping_payload(
            source,
            target,
            transform_type="DATE_FORMAT",
            transform_config={
                "source_format": "OTM_GLOGDATE",
                "target_format": "ISO8601",
            },
        ),
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/generate-spec",
        headers=admin_header,
    )

    assert response.status_code == 200
    artifact = db_session.get(Artifact, response.json()["artifact_id"])
    markdown = Path(artifact.file_path).read_text(encoding="utf-8")
    assert "config `source_format=OTM_GLOGDATE; target_format=ISO8601`" in markdown


def test_generate_integration_spec_includes_response_handlers(client, admin_header, db_session):
    definition, _source, target = create_documents_with_response_status(client, admin_header)
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/response-handlers",
        json=response_handler_payload(target),
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/generate-spec",
        headers=admin_header,
    )

    assert response.status_code == 200
    artifact = db_session.get(Artifact, response.json()["artifact_id"])
    markdown = Path(artifact.file_path).read_text(encoding="utf-8")
    assert "`1` `SUCCESS`: `$.status` `EQUALS` `ACCEPTED`." in markdown


def test_generate_integration_spec_includes_enrichment_pipeline_provenance(client, admin_header, db_session):
    definition, source, _target = create_source_and_target_documents(client, admin_header)
    intermediate = create_intermediate_document(client, admin_header, definition["id"])
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/enrichment-steps",
        json=enrichment_payload(source, intermediate),
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/generate-spec",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert "Enrichment Pipeline" in payload["spec"]["sections"]
    artifact = db_session.get(Artifact, payload["artifact_id"])
    markdown = Path(artifact.file_path).read_text(encoding="utf-8")
    assert "## Enrichment Pipeline" in markdown
    assert "`30` `SINGLE`: `Synthetic carrier enrichment`" in markdown
    assert "`/Transmission/Shipment/ShipmentGid`" in markdown
    assert "`carrier_name_enriched` <- `$.location.locationName`" in markdown
    assert "External enrichment calls are not executed" in markdown


def test_generate_integration_spec_rejects_missing_definition(client, admin_header):
    response = client.post(
        "/api/v1/modules/integration-mapping/definitions/missing-definition/generate-spec",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
