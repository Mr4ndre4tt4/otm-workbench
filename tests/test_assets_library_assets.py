import json

from sqlalchemy import inspect

from otm_workbench.models import AuditLog, DomainEvent


def draft_asset_payload(**overrides):
    payload = {
        "name": "Synthetic OTM Mapping Spec",
        "description": "Client-safe synthetic support asset.",
        "asset_type": "SPEC",
        "category": "INTEGRATION",
        "visibility": "PROJECT",
        "scope_type": "PROJECT",
        "sensitivity": "INTERNAL",
        "module_id": "assets",
        "macro_object_code": "ORDER_RELEASE",
        "otm_table_name": "ORDER_RELEASE",
        "tags": ["SYNTHETIC", "MVP0"],
    }
    payload.update(overrides)
    return payload


def test_assets_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "assets" in table_names


def test_create_draft_asset_records_metadata_audit_and_event(client, admin_header, db_session):
    response = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    )

    assert response.status_code == 200
    asset = response.json()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "assets.asset.create").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "assets.asset.created").one()

    assert asset["status"] == "DRAFT"
    assert asset["asset_type"] == "SPEC"
    assert asset["category"] == "INTEGRATION"
    assert asset["visibility"] == "PROJECT"
    assert asset["scope_type"] == "PROJECT"
    assert asset["sensitivity"] == "INTERNAL"
    assert asset["tags"] == ["SYNTHETIC", "MVP0"]
    assert json.loads(audit.metadata_json)["asset_id"] == asset["id"]
    assert json.loads(event.payload_json)["asset_id"] == asset["id"]

    combined = "\n".join([json.dumps(asset, sort_keys=True), audit.metadata_json, event.payload_json])
    assert "customer" not in combined.lower()
    assert "cliente" not in combined.lower()


def test_create_draft_asset_rejects_unknown_classification(client, admin_header):
    response = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(asset_type="UNKNOWN"),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "classification" in response.json()["message"].lower()


def test_list_and_detail_assets_with_filters(client, admin_header):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(name="Synthetic Test Template", asset_type="TEMPLATE", category="TESTING"),
        headers=admin_header,
    )

    listed = client.get(
        "/api/v1/modules/assets/assets",
        params={"asset_type": "SPEC", "category": "INTEGRATION", "status": "DRAFT"},
        headers=admin_header,
    )
    detail = client.get(f"/api/v1/modules/assets/assets/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert detail.status_code == 200
    assert detail.json()["id"] == created["id"]


def test_update_asset_metadata_records_audit_and_event(client, admin_header, db_session):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()

    response = client.patch(
        f"/api/v1/modules/assets/assets/{created['id']}",
        json={
            "name": "Synthetic Updated Mapping Spec",
            "category": "TESTING",
            "sensitivity": "PUBLIC",
            "tags": ["UPDATED", "SYNTHETIC"],
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "assets.asset.update").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "assets.asset.updated").one()
    assert payload["name"] == "Synthetic Updated Mapping Spec"
    assert payload["category"] == "TESTING"
    assert payload["sensitivity"] == "PUBLIC"
    assert payload["tags"] == ["UPDATED", "SYNTHETIC"]
    assert json.loads(audit.metadata_json)["asset_id"] == created["id"]
    assert json.loads(event.payload_json)["changed_fields"] == [
        "category",
        "name",
        "sensitivity",
        "tags",
    ]

    combined = "\n".join([json.dumps(payload, sort_keys=True), audit.metadata_json, event.payload_json])
    assert "customer" not in combined.lower()
    assert "cliente" not in combined.lower()


def test_update_asset_metadata_rejects_unknown_classification(client, admin_header):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()

    response = client.patch(
        f"/api/v1/modules/assets/assets/{created['id']}",
        json={"category": "UNKNOWN"},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "classification" in response.json()["message"].lower()


def test_archive_asset_preserves_record_and_records_audit_event(client, admin_header, db_session):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()

    response = client.post(
        f"/api/v1/modules/assets/assets/{created['id']}/archive",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "assets.asset.archive").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "assets.asset.archived").one()
    assert payload["id"] == created["id"]
    assert payload["status"] == "ARCHIVED"
    assert json.loads(audit.metadata_json)["asset_id"] == created["id"]
    assert json.loads(event.payload_json)["status"] == "ARCHIVED"
