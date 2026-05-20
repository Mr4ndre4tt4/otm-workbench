import json

from sqlalchemy import inspect

from otm_workbench.models import AuditLog, DomainEvent
from tests.test_assets_library_assets import draft_asset_payload


def create_asset(client, admin_header):
    response = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def test_asset_links_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "asset_links" in table_names


def test_create_asset_link_records_audit_and_event(client, admin_header, db_session):
    asset = create_asset(client, admin_header)

    response = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/links",
        json={
            "link_type": "MODULE",
            "target_id": "integration_mapping",
            "target_label": "Integration Mapping Studio",
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "assets.asset_link.create").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "assets.asset_link.created").one()
    assert payload["asset_id"] == asset["id"]
    assert payload["link_type"] == "MODULE"
    assert payload["target_id"] == "integration_mapping"
    assert json.loads(audit.metadata_json)["asset_link_id"] == payload["id"]
    assert json.loads(event.payload_json)["asset_id"] == asset["id"]

    combined = "\n".join([json.dumps(payload, sort_keys=True), audit.metadata_json, event.payload_json])
    assert "customer" not in combined.lower()
    assert "cliente" not in combined.lower()


def test_create_asset_otm_table_link_validates_data_dictionary(client, admin_header):
    asset = create_asset(client, admin_header)

    valid = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/links",
        json={"link_type": "OTM_TABLE", "target_id": "RATE_GEO_COST"},
        headers=admin_header,
    )
    invalid = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/links",
        json={"link_type": "OTM_TABLE", "target_id": "NOT_A_REAL_OTM_TABLE"},
        headers=admin_header,
    )

    assert valid.status_code == 200
    assert valid.json()["target_id"] == "RATE_GEO_COST"
    assert invalid.status_code == 400
    assert "table" in invalid.json()["message"].lower()


def test_list_asset_links(client, admin_header):
    asset = create_asset(client, admin_header)
    first = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/links",
        json={"link_type": "MODULE", "target_id": "assets"},
        headers=admin_header,
    ).json()
    second = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/links",
        json={"link_type": "MACRO_OBJECT", "target_id": "ORDER_RELEASE"},
        headers=admin_header,
    ).json()

    response = client.get(f"/api/v1/modules/assets/assets/{asset['id']}/links", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert [item["id"] for item in payload["items"]] == [second["id"], first["id"]]


def test_create_asset_link_rejects_unknown_link_type(client, admin_header):
    asset = create_asset(client, admin_header)

    response = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/links",
        json={"link_type": "UNKNOWN", "target_id": "assets"},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "link" in response.json()["message"].lower()
