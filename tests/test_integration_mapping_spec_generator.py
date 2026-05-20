from pathlib import Path

from otm_workbench.models import Artifact, IntegrationMapping, Job
from tests.test_integration_mapping_mappings import create_source_and_target_documents
from tests.test_integration_mapping_validation import create_full_valid_definition


def test_generate_integration_spec_creates_markdown_artifact_and_job(client, admin_header, db_session):
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

    markdown = Path(artifact.file_path).read_text(encoding="utf-8")
    assert "# Integration Mapping Spec" in markdown
    assert "## Identification" in markdown
    assert "## Schema Documents" in markdown
    assert "## Mappings" in markdown
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


def test_generate_integration_spec_rejects_missing_definition(client, admin_header):
    response = client.post(
        "/api/v1/modules/integration-mapping/definitions/missing-definition/generate-spec",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
