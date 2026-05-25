from sqlalchemy import inspect

from otm_workbench.models import SchemaFile, SchemaPack, SchemaRoot


def create_order_release_schema_root(db_session, *, root_name: str):
    schema_pack = SchemaPack(
        code=f"OTM_26A_OR_{root_name.upper()}",
        name=f"OTM 26A Order Release {root_name}",
        otm_version="26A",
        source_type="LOCAL_FOLDER",
        source_path="C:/synthetic/otm/26A",
        content_hash=f"hash-or-{root_name.lower()}",
        status="INDEXED",
    )
    db_session.add(schema_pack)
    db_session.flush()
    schema_file = SchemaFile(
        schema_pack_id=schema_pack.id,
        file_name=f"{root_name}.xsd",
        relative_path=f"{root_name}.xsd",
        file_type="XSD",
        namespace="http://xmlns.oracle.com/apps/otm/synthetic",
        import_count=0,
        top_level_element_count=1,
        complex_type_count=1,
        status="PARSED",
    )
    db_session.add(schema_file)
    db_session.flush()
    schema_root = SchemaRoot(
        schema_pack_id=schema_pack.id,
        schema_file_id=schema_file.id,
        root_name=root_name,
        namespace="http://xmlns.oracle.com/apps/otm/synthetic",
        domain_area="ORDER_RELEASE",
        root_type="MESSAGE",
        envelope_role="TRANSMISSION" if root_name == "Transmission" else "BODY",
    )
    db_session.add(schema_root)
    db_session.commit()
    return schema_root


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


def test_create_order_release_template_version_preserves_template_history(client, admin_header):
    created = client.post(
        "/api/v1/modules/order-release-generator/templates",
        headers=admin_header,
        json={
            "code": "TL_OR_VERSIONED_MVP0",
            "name": "Versioned TL Order Release",
            "required_columns": ["release_gid", "source_location_gid", "destination_location_gid"],
            "optional_columns": ["remarks"],
            "defaults": {"domain_name": "OTM1"},
        },
    ).json()

    response = client.post(
        f"/api/v1/modules/order-release-generator/templates/{created['id']}/versions",
        headers=admin_header,
        json={
            "name": "Versioned TL Order Release v2",
            "description": "Second synthetic version with an additional required column.",
            "required_columns": ["release_gid", "source_location_gid", "destination_location_gid", "weight"],
            "optional_columns": ["remarks", "weight_uom"],
            "defaults": {"domain_name": "OTM1", "weight_uom": "KG"},
        },
    )

    assert response.status_code == 200
    versioned = response.json()
    assert versioned["id"] != created["id"]
    assert versioned["code"] == "TL_OR_VERSIONED_MVP0"
    assert versioned["version"] == 2
    assert versioned["name"] == "Versioned TL Order Release v2"
    assert versioned["created_by"] == "admin@example.com"

    templates = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()
    matching = [item for item in templates["items"] if item["code"] == "TL_OR_VERSIONED_MVP0"]
    assert [item["version"] for item in matching] == [2, 1]

    batch_response = client.post(
        "/api/v1/modules/order-release-generator/batches",
        headers=admin_header,
        json={
            "template_id": versioned["id"],
            "file_name": "versioned_or.xlsx",
            "rows": [
                {
                    "release_gid": "OTM1.OR_VERSIONED_001",
                    "source_location_gid": "OTM1.SOURCE_A",
                    "destination_location_gid": "OTM1.DEST_A",
                    "weight": "100",
                    "weight_uom": "KG",
                }
            ],
        },
    )

    assert batch_response.status_code == 200
    assert batch_response.json()["status"] == "VALID"


def test_create_order_release_template_can_reference_schema_roots(client, admin_header, db_session):
    transmission_root = create_order_release_schema_root(db_session, root_name="Transmission")
    release_root = create_order_release_schema_root(db_session, root_name="Release")

    response = client.post(
        "/api/v1/modules/order-release-generator/templates",
        headers=admin_header,
        json={
            "code": "TL_OR_SCHEMA_ROOTS",
            "name": "Schema-rooted TL Order Release",
            "required_columns": ["release_gid", "source_location_gid", "destination_location_gid"],
            "optional_columns": ["remarks"],
            "defaults": {"domain_name": "OTM1"},
            "transmission_schema_root_id": transmission_root.id,
            "release_schema_root_id": release_root.id,
        },
    )

    assert response.status_code == 200
    template = response.json()
    assert template["transmission_schema_root_id"] == transmission_root.id
    assert template["release_schema_root_id"] == release_root.id


def test_create_order_release_template_rejects_unknown_schema_root(client, admin_header):
    response = client.post(
        "/api/v1/modules/order-release-generator/templates",
        headers=admin_header,
        json={
            "code": "TL_OR_UNKNOWN_SCHEMA_ROOT",
            "name": "Unknown schema rooted template",
            "required_columns": ["release_gid", "source_location_gid", "destination_location_gid"],
            "defaults": {"domain_name": "OTM1"},
            "transmission_schema_root_id": "missing-schema-root",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "ORDER_RELEASE_SCHEMA_ROOT_NOT_FOUND"


def test_modules_endpoint_returns_order_release_generator_module(client, admin_header):
    response = client.get("/api/v1/platform/modules", headers=admin_header)

    assert response.status_code == 200
    module_ids = [item["id"] for item in response.json()["items"]]
    assert "order_release_generator" in module_ids
