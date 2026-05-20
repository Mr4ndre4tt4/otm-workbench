import xml.etree.ElementTree as ET

from tests.test_order_release_generator_batches import valid_rows


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
