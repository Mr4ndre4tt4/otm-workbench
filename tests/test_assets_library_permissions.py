from tests.test_assets_library_assets import draft_asset_payload


def create_asset(client, admin_header):
    response = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def test_authenticated_non_admin_without_active_context_cannot_read_operational_assets(
    client,
    admin_header,
    auth_header,
):
    asset = create_asset(client, admin_header)

    listed = client.get("/api/v1/modules/assets/assets", headers=auth_header)
    detail = client.get(f"/api/v1/modules/assets/assets/{asset['id']}", headers=auth_header)

    assert listed.status_code == 200
    assert listed.json()["total"] == 0
    assert listed.json()["items"] == []
    assert detail.status_code == 404
    assert detail.json()["code"] == "ASSET_NOT_FOUND"


def test_non_admin_cannot_create_asset(client, auth_header):
    response = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=auth_header,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_non_admin_cannot_update_archive_link_or_upload_asset(client, admin_header, auth_header):
    asset = create_asset(client, admin_header)

    update = client.patch(
        f"/api/v1/modules/assets/assets/{asset['id']}",
        json={"name": "Synthetic Updated Name"},
        headers=auth_header,
    )
    archive = client.post(f"/api/v1/modules/assets/assets/{asset['id']}/archive", headers=auth_header)
    link = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/links",
        json={"link_type": "MODULE", "target_id": "assets"},
        headers=auth_header,
    )
    upload = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/versions",
        files={"file": ("synthetic.txt", b"synthetic", "text/plain")},
        headers=auth_header,
    )

    assert update.status_code == 403
    assert archive.status_code == 403
    assert link.status_code == 403
    assert upload.status_code == 403
