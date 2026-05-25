import xml.etree.ElementTree as ET

from tests.test_order_release_generator_batches import valid_rows
from tests.test_order_release_generator_foundation import create_order_release_schema_root


def create_batch(client, admin_header, rows=None):
    template_id = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()["items"][0]["id"]
    response = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "synthetic_or.xlsx", "rows": rows or valid_rows()},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def test_preview_order_release_xml_groups_rows_by_release(client, admin_header):
    batch = create_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/order-release-generator/batches/{batch['id']}/preview-xml",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"] == batch["id"]
    assert payload["release_count"] == 2
    assert payload["line_count"] == 3
    xml_text = payload["xml"]
    root = ET.fromstring(xml_text)
    releases = root.findall(".//Release")
    release_gids = [release.findtext("./ReleaseGid/Gid/Xid") for release in releases]
    release_lines = root.findall(".//ReleaseLine")
    assert root.tag == "Transmission"
    assert release_gids == ["OR_SYN_001", "OR_SYN_002"]
    assert len(release_lines) == 3
    assert "cliente" not in xml_text.lower()
    assert "customer" not in xml_text.lower()


def test_preview_order_release_xml_reports_schema_root_validation(client, admin_header, db_session):
    transmission_root = create_order_release_schema_root(db_session, root_name="Transmission")
    release_root = create_order_release_schema_root(db_session, root_name="Release")
    template = client.post(
        "/api/v1/modules/order-release-generator/templates",
        headers=admin_header,
        json={
            "code": "TL_OR_XML_SCHEMA_ROOTS",
            "name": "Schema validated TL Order Release",
            "required_columns": [
                "release_gid",
                "source_location_gid",
                "destination_location_gid",
                "early_pickup_date",
                "late_delivery_date",
                "item_gid",
                "packaged_item_gid",
                "weight",
                "weight_uom",
            ],
            "defaults": {"domain_name": "OTM1"},
            "transmission_schema_root_id": transmission_root.id,
            "release_schema_root_id": release_root.id,
        },
    ).json()
    batch_response = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template["id"], "file_name": "schema_validated_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    )
    assert batch_response.status_code == 200

    response = client.post(
        f"/api/v1/modules/order-release-generator/batches/{batch_response.json()['id']}/preview-xml",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_validation"] == {
        "status": "PASSED",
        "transmission_schema_root_id": transmission_root.id,
        "release_schema_root_id": release_root.id,
        "checked_roots": ["Transmission", "Release"],
        "issues": [],
    }


def test_preview_order_release_xml_rejects_invalid_batch(client, admin_header):
    rows = valid_rows()
    rows[0].pop("release_gid")
    batch = create_batch(client, admin_header, rows)

    response = client.post(
        f"/api/v1/modules/order-release-generator/batches/{batch['id']}/preview-xml",
        headers=admin_header,
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ORDER_RELEASE_BATCH_INVALID"


def test_preview_order_release_xml_rejects_missing_batch(client, admin_header):
    response = client.post(
        "/api/v1/modules/order-release-generator/batches/missing-batch/preview-xml",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "ORDER_RELEASE_BATCH_NOT_FOUND"
