from sqlalchemy import inspect


def test_order_release_generator_health_requires_authentication(client):
    response = client.get("/api/v1/modules/order-release-generator/health")

    assert response.status_code == 401


def test_order_release_generator_health(client, admin_header):
    response = client.get("/api/v1/modules/order-release-generator/health", headers=admin_header)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "module": "order_release_generator"}


def test_order_release_templates_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "order_release_templates" in table_names


def test_list_order_release_templates_seeds_synthetic_tl_template(client, admin_header):
    response = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    template = payload["items"][0]
    assert template["code"] == "TL_ORDER_RELEASE_MVP0"
    assert template["name"] == "Synthetic TL Order Release"
    assert template["version"] == 1
    assert template["status"] == "ACTIVE"
    assert template["macro_object_code"] == "ORDER_RELEASE"
    assert "release_gid" in template["required_columns"]


def test_create_order_release_template_can_drive_batch_authoring(client, admin_header):
    response = client.post(
        "/api/v1/modules/order-release-generator/templates",
        headers=admin_header,
        json={
            "code": "TL_OR_CUSTOM_MVP0",
            "name": "Custom TL Order Release",
            "description": "Synthetic template created through governed backend authoring.",
            "required_columns": ["release_gid", "source_location_gid", "destination_location_gid"],
            "optional_columns": ["remarks"],
            "defaults": {"domain_name": "OTM1", "transport_mode": "TL"},
        },
    )

    assert response.status_code == 200
    template = response.json()
    assert template["code"] == "TL_OR_CUSTOM_MVP0"
    assert template["version"] == 1
    assert template["status"] == "ACTIVE"
    assert template["macro_object_code"] == "ORDER_RELEASE"
    assert template["created_by"] == "admin@example.com"

    templates = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()
    assert templates["total"] == 2
    assert any(item["code"] == "TL_OR_CUSTOM_MVP0" for item in templates["items"])

    batch_response = client.post(
        "/api/v1/modules/order-release-generator/batches",
        headers=admin_header,
        json={
            "template_id": template["id"],
            "file_name": "custom_or.xlsx",
            "rows": [
                {
                    "release_gid": "OTM1.OR_CUSTOM_001",
                    "source_location_gid": "OTM1.SOURCE_A",
                    "destination_location_gid": "OTM1.DEST_A",
                    "remarks": "synthetic custom row",
                }
            ],
        },
    )

    assert batch_response.status_code == 200
    batch = batch_response.json()
    assert batch["status"] == "VALID"
    assert batch["summary"]["template_code"] == "TL_OR_CUSTOM_MVP0"


def test_create_order_release_template_rejects_invalid_contract(client, admin_header):
    response = client.post(
        "/api/v1/modules/order-release-generator/templates",
        headers=admin_header,
        json={
            "code": "bad code",
            "name": "Invalid Template",
            "required_columns": ["release_gid", "release_gid"],
            "optional_columns": ["release_gid"],
            "defaults": {"unknown_column": "value"},
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ORDER_RELEASE_TEMPLATE_INVALID"


def test_modules_endpoint_returns_order_release_generator_module(client, admin_header):
    response = client.get("/api/v1/platform/modules", headers=admin_header)

    assert response.status_code == 200
    module_ids = [item["id"] for item in response.json()["items"]]
    assert "order_release_generator" in module_ids
