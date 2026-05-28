from pathlib import Path

from otm_workbench.models import Artifact, IntegrationPayloadArtifact
from tests.test_integration_mapping_definitions import (
    create_project_with_environments,
    definition_payload,
    set_active_context,
)


def create_definition(client, admin_header):
    response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="PS_PAYLOAD_IMPORT"),
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def payload_import(**overrides):
    payload = {
        "payload_role": "SOURCE_SAMPLE",
        "payload_format": "XML",
        "file_name": "planned_shipment_sample.xml",
        "content": "<Transmission><Shipment><ShipmentGid>OTM1.SYNTHETIC</ShipmentGid></Shipment></Transmission>",
        "description": "Synthetic OTM PlannedShipment sample.",
    }
    payload.update(overrides)
    return payload


def test_import_integration_payload_creates_internal_artifact(client, admin_header, db_session):
    project_id, environment_id, _dev_id = create_project_with_environments(client, admin_header)
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )
    definition = create_definition(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/payload-artifacts",
        json=payload_import(),
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    artifact = db_session.get(Artifact, payload["artifact_id"])
    payload_artifact = db_session.get(IntegrationPayloadArtifact, payload["id"])
    assert payload["definition_id"] == definition["id"]
    assert payload["payload_role"] == "SOURCE_SAMPLE"
    assert payload["payload_format"] == "XML"
    assert payload["file_name"] == "planned_shipment_sample.xml"
    assert payload["content_type"] == "application/xml"
    assert payload["size_bytes"] > 0
    assert "content" not in payload
    assert artifact is not None
    assert artifact.source_module == "integration_mapping"
    assert artifact.artifact_type == "integration_payload_sample"
    assert artifact.file_name == "planned_shipment_sample.xml"
    assert artifact.project_id == project_id
    assert artifact.environment_id == environment_id
    assert artifact.domain_name == "OTM1"
    assert artifact.visibility == "PROJECT"
    assert payload_artifact is not None
    assert payload_artifact.artifact_id == artifact.id
    assert Path(artifact.file_path).exists()
    assert Path(artifact.file_path).read_text(encoding="utf-8").startswith("<Transmission>")


def test_list_integration_payload_artifacts(client, admin_header):
    definition = create_definition(client, admin_header)
    created = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/payload-artifacts",
        json=payload_import(payload_format="JSON", file_name="delivery.json", content='{"id":"SYNTHETIC"}'),
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/payload-artifacts",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["payload_format"] == "JSON"
    assert payload["items"][0]["content_type"] == "application/json"
    assert "content" not in payload["items"][0]


def test_import_integration_payload_rejects_secret_like_content(client, admin_header):
    definition = create_definition(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/payload-artifacts",
        json=payload_import(content='{"api_token":"sk-test-secret"}', payload_format="JSON"),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_SECRET_RISK"


def test_import_integration_payload_rejects_unsupported_format(client, admin_header):
    definition = create_definition(client, admin_header)

    response = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/payload-artifacts",
        json=payload_import(payload_format="CSV"),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_PAYLOAD_FORMAT_UNSUPPORTED"


def test_import_integration_payload_rejects_missing_definition(client, admin_header):
    response = client.post(
        "/api/v1/modules/integration-mapping/definitions/missing-definition/payload-artifacts",
        json=payload_import(),
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
