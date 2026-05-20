import json
from pathlib import Path

from otm_workbench.models import Artifact, IntegrationMapping, Job
from tests.test_integration_mapping_mappings import create_source_and_target_documents
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
