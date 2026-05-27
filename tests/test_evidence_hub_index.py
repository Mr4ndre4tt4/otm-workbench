import json
from pathlib import Path
import zipfile

from otm_workbench.models import (
    Artifact,
    AuditLog,
    Capability,
    DomainEvent,
    Evidence,
    Role,
    RoleCapability,
    SessionToken,
    UserProjectRole,
)
from otm_workbench.config import get_settings


def test_evidence_hub_list_requires_authentication(client):
    response = client.get("/api/v1/evidence-hub/evidence")

    assert response.status_code == 401


def test_evidence_hub_list_returns_empty_page(client, admin_header):
    response = client.get("/api/v1/evidence-hub/evidence", headers=admin_header)

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def create_platform_evidence(client, admin_header):
    artifact_dir = get_settings().artifact_root / "test-artifacts" / "evidence-hub"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_file = artifact_dir / "demo.txt"
    artifact_file.write_text("OTM1.ACC_COST_001 should not be exposed", encoding="utf-8")
    artifact = client.post(
        "/api/v1/platform/artifacts",
        json={
            "source_module": "rates",
            "artifact_type": "rates_csv_zip",
            "file_path": str(artifact_file),
            "file_name": "demo.zip",
            "content_type": "application/zip",
            "sensitivity_level": "internal",
        },
        headers=admin_header,
    )
    assert artifact.status_code == 200
    manifest = client.post(
        "/api/v1/platform/manifests",
        json={
            "source_module": "rates",
            "status": "CREATED",
            "manifest_json": json.dumps(
                {
                    "schema_version": "rates-csv-export-manifest/v1",
                    "manifest_type": "rates_csv_export",
                    "raw_value": "OTM1.ACC_COST_001",
                },
                sort_keys=True,
            ),
        },
        headers=admin_header,
    )
    assert manifest.status_code == 200
    evidence = client.post(
        "/api/v1/platform/evidence",
        json={
            "source_module": "rates",
            "evidence_type": "rates_csv_export",
            "summary_json": json.dumps({"status": "ok", "note_present": True}, sort_keys=True),
            "artifact_id": artifact.json()["id"],
            "manifest_id": manifest.json()["id"],
        },
        headers=admin_header,
    )
    assert evidence.status_code == 200
    return evidence.json()["id"], artifact.json()["id"], manifest.json()["id"]


def create_scoped_platform_evidence(client, admin_header, *, prefix: str, domain_name: str = "otm1"):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": f"{prefix} Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": f"{prefix} Project"},
        headers=admin_header,
    ).json()
    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Default"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    artifact_dir = get_settings().artifact_root / "test-artifacts" / "evidence-hub"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_file = artifact_dir / f"{prefix.lower().replace(' ', '-')}.txt"
    artifact_file.write_text(f"{prefix} scoped artifact", encoding="utf-8")
    artifact = client.post(
        "/api/v1/platform/artifacts",
        json={
            "source_module": "rates",
            "artifact_type": "rates_csv_zip",
            "file_path": str(artifact_file),
            "file_name": f"{prefix.lower().replace(' ', '-')}.zip",
            "content_type": "application/zip",
            "sensitivity_level": "internal",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": domain_name,
            "visibility": "PROJECT",
        },
        headers=admin_header,
    )
    manifest = client.post(
        "/api/v1/platform/manifests",
        json={
            "source_module": "rates",
            "status": "CREATED",
            "manifest_json": json.dumps({"schema_version": "test/v1", "manifest_type": "rates_csv_export"}),
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": domain_name,
            "visibility": "PROJECT",
        },
        headers=admin_header,
    )
    evidence = client.post(
        "/api/v1/platform/evidence",
        json={
            "source_module": "rates",
            "evidence_type": "rates_csv_export",
            "summary_json": json.dumps({"status": "ok", "prefix": prefix}, sort_keys=True),
            "artifact_id": artifact.json()["id"],
            "manifest_id": manifest.json()["id"],
        },
        headers=admin_header,
    )
    assert artifact.status_code == 200
    assert manifest.status_code == 200
    assert evidence.status_code == 200
    return {
        "project": project,
        "profile": profile,
        "environment": environment,
        "artifact_id": artifact.json()["id"],
        "manifest_id": manifest.json()["id"],
        "evidence_id": evidence.json()["id"],
    }


def test_evidence_hub_detail_returns_linked_summaries_without_sensitive_fields(client, admin_header):
    evidence_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)

    response = client.get(f"/api/v1/evidence-hub/evidence/{evidence_id}", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == evidence_id
    assert payload["summary"] == {"note_present": True, "status": "ok"}
    assert payload["artifact"]["id"] == artifact_id
    assert payload["artifact"]["file_name"] == "demo.zip"
    assert "file_path" not in payload["artifact"]
    assert payload["manifest"]["id"] == manifest_id
    assert payload["manifest"]["manifest_type"] == "rates_csv_export"
    assert payload["manifest"]["schema_version"] == "rates-csv-export-manifest/v1"
    assert "manifest_json" not in payload["manifest"]
    assert "OTM1.ACC_COST_001" not in str(payload)


def test_evidence_hub_detail_rejects_missing_evidence(client, admin_header):
    response = client.get("/api/v1/evidence-hub/evidence/missing_evidence", headers=admin_header)

    assert response.status_code == 404


def test_evidence_hub_list_filters_by_metadata(client, admin_header):
    evidence_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)

    response = client.get(
        "/api/v1/evidence-hub/evidence",
        params={
            "source_module": "rates",
            "evidence_type": "rates_csv_export",
            "status": "CREATED",
            "sensitivity_level": "client_safe",
            "artifact_id": artifact_id,
            "manifest_id": manifest_id,
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == evidence_id


def test_evidence_hub_records_are_limited_to_active_context_for_non_admin(
    client,
    admin_header,
    auth_header,
    db_session,
):
    visible = create_scoped_platform_evidence(client, admin_header, prefix="Visible Evidence")
    hidden = create_scoped_platform_evidence(client, admin_header, prefix="Hidden Evidence")
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Evidence Viewer")
    capability = Capability(name="evidence.view")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    db_session.add(
        UserProjectRole(
            user_id=user_id,
            project_id=visible["project"]["id"],
            environment_id=visible["environment"]["id"],
            domain_name="OTM1",
            role_id=role.id,
        )
    )
    db_session.commit()
    client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": visible["project"]["id"],
            "profile_id": visible["profile"]["id"],
            "environment_id": visible["environment"]["id"],
            "domain_name": "otm1",
        },
        headers=auth_header,
    )

    listed = client.get("/api/v1/evidence-hub/evidence", headers=auth_header)
    visible_detail = client.get(f"/api/v1/evidence-hub/evidence/{visible['evidence_id']}", headers=auth_header)
    hidden_detail = client.get(f"/api/v1/evidence-hub/evidence/{hidden['evidence_id']}", headers=auth_header)
    visible_download = client.get(f"/api/v1/evidence-hub/artifacts/{visible['artifact_id']}/download", headers=auth_header)
    hidden_download = client.get(f"/api/v1/evidence-hub/artifacts/{hidden['artifact_id']}/download", headers=auth_header)

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == visible["evidence_id"]
    assert visible_detail.status_code == 200
    assert visible_detail.json()["id"] == visible["evidence_id"]
    assert hidden_detail.status_code == 403
    assert hidden_detail.json()["code"] == "EVIDENCE_FORBIDDEN"
    assert visible_download.status_code == 200
    assert hidden_download.status_code == 403
    assert hidden_download.json()["code"] == "ARTIFACT_FORBIDDEN"


def test_evidence_hub_list_defaults_to_client_safe_only(client, admin_header, db_session):
    safe_id, artifact_id, manifest_id = create_platform_evidence(client, admin_header)
    unsafe = Evidence(
        source_module="rates",
        evidence_type="rates_csv_export",
        summary_json='{"status":"unsafe"}',
        artifact_id=artifact_id,
        manifest_id=manifest_id,
        client_safe=False,
        sensitivity_level="internal",
    )
    db_session.add(unsafe)
    db_session.commit()

    default_response = client.get("/api/v1/evidence-hub/evidence", headers=admin_header)
    unsafe_response = client.get(
        "/api/v1/evidence-hub/evidence",
        params={"client_safe": "false"},
        headers=admin_header,
    )

    assert default_response.status_code == 200
    assert [item["id"] for item in default_response.json()["items"]] == [safe_id]
    assert unsafe_response.status_code == 200
    assert unsafe_response.json()["items"][0]["id"] == unsafe.id


def test_evidence_hub_artifact_download_requires_authentication(client, admin_header):
    _evidence_id, artifact_id, _manifest_id = create_platform_evidence(client, admin_header)

    response = client.get(f"/api/v1/evidence-hub/artifacts/{artifact_id}/download")

    assert response.status_code == 401


def test_evidence_hub_artifact_download_rejects_missing_artifact(client, admin_header):
    response = client.get(
        "/api/v1/evidence-hub/artifacts/missing_artifact/download",
        headers=admin_header,
    )

    assert response.status_code == 404


def test_evidence_hub_artifact_download_rejects_artifact_without_client_safe_evidence(
    client,
    admin_header,
    db_session,
):
    artifact_path = get_settings().artifact_root / "test-artifacts" / "evidence-hub" / "no-safe-evidence.txt"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("synthetic internal artifact", encoding="utf-8")
    artifact = Artifact(
        source_module="rates",
        artifact_type="rates_csv_zip",
        file_path=str(artifact_path),
        file_name="no-safe-evidence.zip",
        content_type="application/zip",
        sha256="0" * 64,
        size_bytes=artifact_path.stat().st_size,
        sensitivity_level="internal",
    )
    db_session.add(artifact)
    db_session.commit()

    response = client.get(
        f"/api/v1/evidence-hub/artifacts/{artifact.id}/download",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert str(artifact_path) not in str(response.json())


def test_platform_artifact_create_rejects_file_outside_artifact_root(client, admin_header):
    outside_path = Path("var/outside-artifact-root.txt")
    outside_path.parent.mkdir(parents=True, exist_ok=True)
    outside_path.write_text("synthetic outside artifact root", encoding="utf-8")

    response = client.post(
        "/api/v1/platform/artifacts",
        json={
            "source_module": "platform",
            "artifact_type": "unsafe_path",
            "file_path": str(outside_path),
            "file_name": "outside.txt",
            "content_type": "text/plain",
            "sensitivity_level": "internal",
        },
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "ARTIFACT_PATH_OUTSIDE_ROOT"
    assert str(outside_path) not in str(response.json())


def test_evidence_hub_download_rejects_stored_artifact_path_outside_root(
    client,
    admin_header,
    db_session,
):
    outside_path = Path("var/outside-evidence-download.txt")
    outside_path.parent.mkdir(parents=True, exist_ok=True)
    outside_path.write_text("synthetic outside evidence download", encoding="utf-8")
    artifact = Artifact(
        source_module="platform",
        artifact_type="unsafe_path",
        file_path=str(outside_path),
        file_name="outside.txt",
        content_type="text/plain",
        sha256="0" * 64,
        size_bytes=outside_path.stat().st_size,
        sensitivity_level="internal",
    )
    db_session.add(artifact)
    db_session.flush()
    evidence = Evidence(
        source_module="platform",
        evidence_type="unsafe_path",
        summary_json='{"status":"unsafe"}',
        artifact_id=artifact.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db_session.add(evidence)
    db_session.commit()

    response = client.get(
        f"/api/v1/evidence-hub/artifacts/{artifact.id}/download",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert str(outside_path) not in str(response.json())


def test_evidence_hub_artifact_download_returns_file_and_audit(client, admin_header, db_session):
    evidence_id, artifact_id, _manifest_id = create_platform_evidence(client, admin_header)

    response = client.get(
        f"/api/v1/evidence-hub/artifacts/{artifact_id}/download",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.content == b"OTM1.ACC_COST_001 should not be exposed"
    assert response.headers["content-type"] == "application/zip"
    assert "demo.zip" in response.headers["content-disposition"]
    assert len(response.headers["x-artifact-sha256"]) == 64
    audit = db_session.query(AuditLog).filter_by(action="evidence_hub.artifact.download").one()
    assert audit.target_type == "artifact"
    assert audit.target_id == artifact_id
    assert artifact_id in audit.metadata_json
    assert evidence_id in audit.metadata_json
    assert "demo.txt" not in audit.metadata_json
    assert "OTM1.ACC_COST_001" not in audit.metadata_json


def test_evidence_hub_artifact_download_rejects_missing_file_without_path(
    client,
    admin_header,
    db_session,
):
    _evidence_id, artifact_id, _manifest_id = create_platform_evidence(client, admin_header)
    artifact = db_session.query(Artifact).filter_by(id=artifact_id).one()
    artifact_path = Path(artifact.file_path)
    artifact_path.unlink()
    db_session.commit()

    response = client.get(
        f"/api/v1/evidence-hub/artifacts/{artifact_id}/download",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert str(artifact_path) not in str(response.json())


def test_evidence_hub_artifact_download_rejects_hash_mismatch_without_path(
    client,
    admin_header,
    db_session,
):
    _evidence_id, artifact_id, _manifest_id = create_platform_evidence(client, admin_header)
    artifact = db_session.query(Artifact).filter_by(id=artifact_id).one()
    artifact_path = Path(artifact.file_path)
    artifact_path.write_text("changed synthetic artifact", encoding="utf-8")

    response = client.get(
        f"/api/v1/evidence-hub/artifacts/{artifact_id}/download",
        headers=admin_header,
    )

    assert response.status_code == 409
    assert str(artifact_path) not in str(response.json())


def test_evidence_hub_archive_package_rejects_no_matching_evidence(client, admin_header):
    response = client.post(
        "/api/v1/evidence-hub/archive-packages",
        json={"source_module": "missing_module"},
        headers=admin_header,
    )

    assert response.status_code == 400


def test_evidence_hub_archive_package_rejects_mixed_project_scope(client, admin_header):
    create_scoped_platform_evidence(client, admin_header, prefix="Archive Scope One")
    create_scoped_platform_evidence(client, admin_header, prefix="Archive Scope Two")

    response = client.post(
        "/api/v1/evidence-hub/archive-packages",
        json={
            "source_module": "rates",
            "evidence_type": "rates_csv_export",
            "status": "CREATED",
            "sensitivity_level": "client_safe",
        },
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "EVIDENCE_ARCHIVE_SCOPE_MISMATCH"


def test_evidence_hub_archive_package_creates_metadata_zip_and_records(
    client,
    admin_header,
    db_session,
):
    scoped = create_scoped_platform_evidence(client, admin_header, prefix="Archive Evidence")
    evidence_id = scoped["evidence_id"]
    artifact_id = scoped["artifact_id"]
    manifest_id = scoped["manifest_id"]

    response = client.post(
        "/api/v1/evidence-hub/archive-packages",
        json={
            "source_module": "rates",
            "evidence_type": "rates_csv_export",
            "status": "CREATED",
            "project_id": scoped["project"]["id"],
            "sensitivity_level": "client_safe",
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["artifact_id"]
    assert payload["manifest_id"]
    assert payload["evidence_id"]
    assert len(payload["sha256"]) == 64
    assert payload["summary"]["evidence_count"] == 1
    assert payload["summary"]["artifact_ref_count"] == 1
    assert payload["summary"]["manifest_ref_count"] == 1

    archive_artifact = db_session.query(Artifact).filter_by(id=payload["artifact_id"]).one()
    archive_evidence = db_session.query(Evidence).filter_by(id=payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter_by(action="evidence_hub.archive_package.create").one()
    event = db_session.query(DomainEvent).filter_by(event_type="evidence_hub.archive_package.created").one()

    assert archive_artifact.artifact_type == "evidence_hub_archive_zip"
    assert archive_evidence.evidence_type == "evidence_hub_archive"
    assert archive_evidence.client_safe is True
    assert archive_artifact.project_id == scoped["project"]["id"]
    assert archive_artifact.profile_id == scoped["profile"]["id"]
    assert archive_artifact.environment_id == scoped["environment"]["id"]
    assert archive_artifact.domain_name == "OTM1"
    assert archive_artifact.visibility == "PROJECT"
    assert archive_evidence.project_id == scoped["project"]["id"]
    assert archive_evidence.profile_id == scoped["profile"]["id"]
    assert archive_evidence.environment_id == scoped["environment"]["id"]
    assert archive_evidence.domain_name == "OTM1"
    assert archive_evidence.visibility == "PROJECT"
    assert audit.target_id == archive_artifact.id
    assert event.aggregate_id == archive_artifact.id
    assert event.project_id == scoped["project"]["id"]

    with zipfile.ZipFile(archive_artifact.file_path) as archive:
        assert sorted(archive.namelist()) == [
            "archive_manifest.json",
            "artifact_index.json",
            "evidence_index.json",
            "manifest_index.json",
        ]
        archive_manifest = json.loads(archive.read("archive_manifest.json"))
        evidence_index = json.loads(archive.read("evidence_index.json"))
        artifact_index = json.loads(archive.read("artifact_index.json"))
        manifest_index = json.loads(archive.read("manifest_index.json"))

    assert archive_manifest["schema_version"] == "evidence-hub-archive-manifest/v1"
    assert archive_manifest["manifest_type"] == "evidence_hub_archive"
    assert archive_manifest["evidence_count"] == 1
    assert evidence_index[0]["id"] == evidence_id
    assert artifact_index[0]["id"] == artifact_id
    assert manifest_index[0]["id"] == manifest_id
    combined = json.dumps(
        {
            "archive_manifest": archive_manifest,
            "evidence_index": evidence_index,
            "artifact_index": artifact_index,
            "manifest_index": manifest_index,
            "archive_evidence": archive_evidence.summary_json,
            "audit": audit.metadata_json,
            "event": event.payload_json,
        },
        sort_keys=True,
    )
    assert "file_path" not in combined
    assert "manifest_json" not in combined
    assert "OTM1.ACC_COST_001" not in combined

    download = client.get(
        f"/api/v1/evidence-hub/artifacts/{payload['artifact_id']}/download",
        headers=admin_header,
    )
    assert download.status_code == 200
    assert download.content.startswith(b"PK")
