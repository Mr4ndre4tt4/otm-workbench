import json
from pathlib import Path

from otm_workbench.models import Artifact, AuditLog
from tests.test_integration_mapping_definitions import definition_payload
from tests.test_integration_mapping_validation import create_full_valid_definition


def create_preview_and_spec(client, admin_header, definition_id):
    preview = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition_id}/preview",
        headers=admin_header,
    )
    spec = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{definition_id}/generate-spec",
        headers=admin_header,
    )
    assert preview.status_code == 200
    assert spec.status_code == 200
    return preview.json(), spec.json()


def test_list_integration_mapping_definition_artifacts_returns_safe_download_metadata(
    client,
    admin_header,
):
    definition, _source, _target = create_full_valid_definition(client, admin_header)
    preview, spec = create_preview_and_spec(client, admin_header, definition["id"])

    response = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/artifacts",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    artifact_ids = {item["id"] for item in payload["items"]}
    assert payload["definition_id"] == definition["id"]
    assert preview["artifact_id"] in artifact_ids
    assert spec["artifact_id"] in artifact_ids
    assert payload["total"] == 2
    for item in payload["items"]:
        assert item["source_module"] == "integration_mapping"
        assert item["download_url"].endswith(f"/artifacts/{item['id']}/download")
    assert "file_path" not in str(payload)


def test_download_integration_mapping_artifact_returns_file_and_audits(
    client,
    admin_header,
    db_session,
):
    definition, _source, _target = create_full_valid_definition(client, admin_header)
    preview, _spec = create_preview_and_spec(client, admin_header, definition["id"])
    artifact = db_session.get(Artifact, preview["artifact_id"])

    response = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/artifacts/{artifact.id}/download",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["definition_id"] == definition["id"]
    assert response.headers["content-type"] == "application/json"
    assert artifact.file_name in response.headers["content-disposition"]
    assert response.headers["x-artifact-sha256"] == artifact.sha256
    audit = db_session.query(AuditLog).filter_by(action="integration_mapping.artifact.download").one()
    assert audit.target_type == "artifact"
    assert audit.target_id == artifact.id
    audit_metadata = json.loads(audit.metadata_json)
    assert audit_metadata["definition_id"] == definition["id"]
    assert audit_metadata["artifact_id"] == artifact.id
    assert artifact.file_path not in audit.metadata_json


def test_download_integration_mapping_artifact_rejects_artifact_from_another_definition_without_path(
    client,
    admin_header,
):
    first_definition, _source, _target = create_full_valid_definition(client, admin_header)
    preview, _spec = create_preview_and_spec(client, admin_header, first_definition["id"])
    second_definition = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="PS_ARTIFACT_OTHER"),
        headers=admin_header,
    ).json()

    response = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{second_definition['id']}/artifacts/{preview['artifact_id']}/download",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert "file_path" not in str(response.json())


def test_download_integration_mapping_artifact_rejects_hash_mismatch_without_path(
    client,
    admin_header,
    db_session,
):
    definition, _source, _target = create_full_valid_definition(client, admin_header)
    preview, _spec = create_preview_and_spec(client, admin_header, definition["id"])
    artifact = db_session.get(Artifact, preview["artifact_id"])
    Path(artifact.file_path).write_text("changed synthetic preview", encoding="utf-8")

    response = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition['id']}/artifacts/{artifact.id}/download",
        headers=admin_header,
    )

    assert response.status_code == 409
    assert artifact.file_path not in str(response.json())
