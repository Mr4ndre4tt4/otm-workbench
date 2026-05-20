import hashlib
import json
from pathlib import Path

from sqlalchemy import inspect

from otm_workbench.models import Asset, AuditLog, DomainEvent
from tests.test_assets_library_assets import draft_asset_payload


def create_asset(client, admin_header):
    response = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def test_asset_versions_table_exists_after_metadata_reset(db_session):
    columns = {column["name"] for column in inspect(db_session.bind).get_columns("assets")}
    table_names = inspect(db_session.bind).get_table_names()

    assert "asset_versions" in table_names
    assert "current_version_id" in columns


def test_upload_first_asset_version_records_file_hash_and_current_version(
    client,
    admin_header,
    db_session,
):
    asset = create_asset(client, admin_header)
    content = b"synthetic asset payload for otm workbench\n"

    response = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/versions",
        files={"file": ("synthetic_spec.md", content, "text/markdown")},
        headers=admin_header,
    )

    assert response.status_code == 200
    version = response.json()
    refreshed_asset = db_session.query(Asset).filter(Asset.id == asset["id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "assets.asset_version.upload").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "assets.asset_version.uploaded").one()

    assert version["asset_id"] == asset["id"]
    assert version["version_number"] == 1
    assert version["file_name"] == "synthetic_spec.md"
    assert version["content_type"] == "text/markdown"
    assert version["sha256"] == hashlib.sha256(content).hexdigest()
    assert version["size_bytes"] == len(content)
    assert refreshed_asset.current_version_id == version["id"]
    assert Path(version["storage_path"]).exists()
    assert json.loads(audit.metadata_json)["asset_version_id"] == version["id"]
    assert json.loads(event.payload_json)["asset_id"] == asset["id"]

    combined = "\n".join([json.dumps(version, sort_keys=True), audit.metadata_json, event.payload_json])
    assert "customer" not in combined.lower()
    assert "cliente" not in combined.lower()


def test_list_asset_versions(client, admin_header):
    asset = create_asset(client, admin_header)
    first = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/versions",
        files={"file": ("first.txt", b"first synthetic file", "text/plain")},
        headers=admin_header,
    ).json()
    second = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/versions",
        files={"file": ("second.txt", b"second synthetic file", "text/plain")},
        headers=admin_header,
    ).json()

    response = client.get(
        f"/api/v1/modules/assets/assets/{asset['id']}/versions",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert [item["id"] for item in payload["items"]] == [second["id"], first["id"]]
    assert [item["version_number"] for item in payload["items"]] == [2, 1]


def test_upload_asset_version_rejects_missing_asset(client, admin_header):
    response = client.post(
        "/api/v1/modules/assets/assets/missing_asset/versions",
        files={"file": ("missing.txt", b"synthetic", "text/plain")},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_download_current_asset_version_returns_file_and_audits_sensitive_asset(
    client,
    admin_header,
    db_session,
):
    asset = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(sensitivity="SECRET"),
        headers=admin_header,
    ).json()
    content = b"synthetic sensitive support payload\n"
    upload = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/versions",
        files={"file": ("sensitive.txt", content, "text/plain")},
        headers=admin_header,
    ).json()

    response = client.get(
        f"/api/v1/modules/assets/assets/{asset['id']}/download",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.content == content
    assert response.headers["content-type"].startswith("text/plain")
    audit = db_session.query(AuditLog).filter(AuditLog.action == "assets.asset.download").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "assets.asset.downloaded").one()
    audit_payload = json.loads(audit.metadata_json)
    event_payload = json.loads(event.payload_json)
    assert audit_payload["asset_id"] == asset["id"]
    assert audit_payload["asset_version_id"] == upload["id"]
    assert audit_payload["sensitivity"] == "SECRET"
    assert event_payload["asset_id"] == asset["id"]

    combined = "\n".join([audit.metadata_json, event.payload_json])
    assert "synthetic sensitive support payload" not in combined
    assert "customer" not in combined.lower()
    assert "cliente" not in combined.lower()


def test_download_current_asset_version_rejects_asset_without_version(client, admin_header):
    asset = create_asset(client, admin_header)

    response = client.get(
        f"/api/v1/modules/assets/assets/{asset['id']}/download",
        headers=admin_header,
    )

    assert response.status_code == 409
    assert "version" in response.json()["message"].lower()
