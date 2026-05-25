from sqlalchemy import inspect

from otm_workbench.models import IntegrationDefinition, SchemaFile, SchemaPack, SchemaRoot


def definition_payload(**overrides):
    payload = {
        "code": "PS_TO_EXT_DELIVERY",
        "name": "Planned Shipment to External Delivery",
        "description": "Synthetic mapping definition for backend tests.",
        "source_system": "OTM",
        "target_system": "EXT_SYSTEM",
        "source_format": "XML",
        "target_format": "JSON",
        "status": "ACTIVE",
    }
    payload.update(overrides)
    return payload


def create_schema_root(db_session, *, root_name: str):
    schema_pack = SchemaPack(
        code=f"OTM_26A_{root_name.upper()}",
        name=f"OTM 26A {root_name}",
        otm_version="26A",
        source_type="LOCAL_FOLDER",
        source_path="C:/synthetic/otm/26A",
        content_hash=f"hash-{root_name.lower()}",
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
        domain_area="INTEGRATION",
        root_type="MESSAGE",
        envelope_role="SOURCE" if root_name == "Transmission" else "TARGET",
    )
    db_session.add(schema_root)
    db_session.commit()
    return schema_root


def test_integration_definitions_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "integration_definitions" in table_names


def test_create_integration_definition_starts_as_draft(client, admin_header, db_session):
    response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(),
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    definition = db_session.get(IntegrationDefinition, payload["id"])
    assert definition is not None
    assert payload["code"] == "PS_TO_EXT_DELIVERY"
    assert payload["status"] == "DRAFT"
    assert payload["source_format"] == "XML"
    assert payload["target_format"] == "JSON"
    assert payload["created_by"]
    assert definition.status == "DRAFT"


def test_create_integration_definition_can_reference_catalog_schema_roots(client, admin_header, db_session):
    source_root = create_schema_root(db_session, root_name="Transmission")
    target_root = create_schema_root(db_session, root_name="ExternalDelivery")

    response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(
            code="PS_TO_EXT_DELIVERY_SCHEMA_ROOTS",
            source_schema_root_id=source_root.id,
            target_schema_root_id=target_root.id,
        ),
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    definition = db_session.get(IntegrationDefinition, payload["id"])
    assert payload["source_schema_root_id"] == source_root.id
    assert payload["target_schema_root_id"] == target_root.id
    assert definition.source_schema_root_id == source_root.id
    assert definition.target_schema_root_id == target_root.id


def test_create_integration_definition_rejects_unknown_schema_root(client, admin_header):
    response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(
            code="PS_TO_EXT_DELIVERY_UNKNOWN_SCHEMA_ROOT",
            source_schema_root_id="missing-schema-root",
        ),
        headers=admin_header,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INTEGRATION_SCHEMA_ROOT_NOT_FOUND"


def test_list_integration_definitions(client, admin_header):
    create_response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="PS_TO_EXT_DELIVERY_LIST"),
        headers=admin_header,
    )
    assert create_response.status_code == 200

    response = client.get("/api/v1/modules/integration-mapping/definitions", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["code"] == "PS_TO_EXT_DELIVERY_LIST"
    assert payload["items"][0]["status"] == "DRAFT"


def test_get_integration_definition(client, admin_header):
    create_response = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="PS_TO_EXT_DELIVERY_GET"),
        headers=admin_header,
    )
    definition_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{definition_id}",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["id"] == definition_id
    assert response.json()["code"] == "PS_TO_EXT_DELIVERY_GET"


def test_get_integration_definition_rejects_missing_id(client, admin_header):
    response = client.get(
        "/api/v1/modules/integration-mapping/definitions/missing-definition",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
