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


def test_create_custom_asset_classification_is_grouped_and_usable(client, admin_header):
    create_response = client.post(
        "/api/v1/modules/assets/classifications",
        json={
            "classification_type": "asset_category",
            "code": "PLAYBOOK",
            "name": "Playbook",
            "description": "Reusable synthetic implementation playbook.",
            "sort_order": 90,
        },
        headers=admin_header,
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["code"] == "PLAYBOOK"
    assert created["system_protected"] is False
    assert created["is_active"] is True

    grouped = client.get("/api/v1/modules/assets/classifications", headers=admin_header)
    categories = {
        item["code"]
        for group in grouped.json()["items"]
        if group["classification_type"] == "asset_category"
        for item in group["items"]
    }
    assert "PLAYBOOK" in categories

    asset = client.post(
        "/api/v1/modules/assets/assets",
        json={
            "name": "Synthetic Playbook Asset",
            "description": "Client-safe synthetic custom category asset.",
            "asset_type": "SPEC",
            "category": "PLAYBOOK",
            "visibility": "PROJECT",
            "scope_type": "PROJECT",
            "sensitivity": "INTERNAL",
            "module_id": "assets",
            "macro_object_code": "RATE_RECORD",
            "otm_table_name": "RATE_GEO_COST",
            "tags": ["SYNTHETIC"],
        },
        headers=admin_header,
    )
    assert asset.status_code == 200
    assert asset.json()["category"] == "PLAYBOOK"


def test_update_custom_asset_classification_and_protect_system_rows(client, admin_header):
    custom = client.post(
        "/api/v1/modules/assets/classifications",
        json={
            "classification_type": "asset_type",
            "code": "RUNBOOK",
            "name": "Runbook",
            "description": "Synthetic runbook.",
            "sort_order": 80,
        },
        headers=admin_header,
    ).json()

    updated = client.patch(
        f"/api/v1/modules/assets/classifications/{custom['id']}",
        json={"name": "Operational Runbook", "is_active": False},
        headers=admin_header,
    )
    grouped = client.get("/api/v1/modules/assets/classifications", headers=admin_header).json()
    system_spec = next(
        item
        for group in grouped["items"]
        if group["classification_type"] == "asset_type"
        for item in group["items"]
        if item["code"] == "SPEC"
    )
    protected = client.patch(
        f"/api/v1/modules/assets/classifications/{system_spec['id']}",
        json={"name": "Specification Updated"},
        headers=admin_header,
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Operational Runbook"
    assert updated.json()["is_active"] is False
    assert protected.status_code == 409
    assert protected.json()["code"] == "ASSET_CLASSIFICATION_PROTECTED"
