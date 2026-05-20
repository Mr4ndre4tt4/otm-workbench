from sqlalchemy import inspect


def test_assets_module_registered_in_platform_modules(client, admin_header):
    response = client.get("/api/v1/platform/modules", headers=admin_header)

    assert response.status_code == 200
    modules = {item["id"]: item for item in response.json()["items"]}
    assert modules["assets"]["status"] == "ACTIVE"
    assert modules["assets"]["route_base"] == "/assets"


def test_assets_health_endpoint(client, admin_header):
    response = client.get("/api/v1/modules/assets/health", headers=admin_header)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "module": "assets"}


def test_assets_classifications_are_seeded_and_grouped(client, admin_header):
    response = client.get("/api/v1/modules/assets/classifications", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    groups = {item["classification_type"]: item for item in payload["items"]}

    assert payload["total"] == 7
    assert groups["asset_type"]["items"][0]["code"] == "TEMPLATE"
    assert {item["code"] for item in groups["asset_visibility"]["items"]} == {
        "PROJECT",
        "PROFILE",
        "MODULE",
    }
    assert "SECRET" in {item["code"] for item in groups["asset_sensitivity"]["items"]}
    assert all(item["system_protected"] is True for group in groups.values() for item in group["items"])

    combined = str(payload)
    assert "customer" not in combined.lower()
    assert "cliente" not in combined.lower()


def test_asset_classifications_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "asset_classifications" in table_names
