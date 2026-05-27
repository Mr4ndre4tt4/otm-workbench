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


def create_project_with_environments(client, admin_header, *, name_suffix=""):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": f"Synthetic Integration Workspace{name_suffix}"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": f"Synthetic Integration Project{name_suffix}"},
        headers=admin_header,
    ).json()
    uat = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "UAT", "environment_type": "UAT"},
        headers=admin_header,
    ).json()
    dev = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    return project["id"], uat["id"], dev["id"]


def set_active_context(
    client,
    admin_header,
    *,
    project_id,
    environment_id,
    domain_name,
    can_view_all_domains=False,
):
    response = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project_id,
            "environment_id": environment_id,
            "domain_name": domain_name,
            "can_view_all_domains": can_view_all_domains,
        },
        headers=admin_header,
    )
    assert response.status_code == 200


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


def test_integration_definitions_follow_active_context_scope(client, admin_header):
    project_id, uat_id, dev_id = create_project_with_environments(client, admin_header)
    other_project_id, other_uat_id, _ = create_project_with_environments(client, admin_header, name_suffix=" Other")
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
    )
    visible = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="INT_SCOPE_VISIBLE"),
        headers=admin_header,
    ).json()
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM2",
    )
    hidden_domain = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="INT_SCOPE_HIDDEN_DOMAIN"),
        headers=admin_header,
    ).json()
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=dev_id,
        domain_name="OTM1",
    )
    client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="INT_SCOPE_HIDDEN_ENV"),
        headers=admin_header,
    )
    set_active_context(
        client,
        admin_header,
        project_id=other_project_id,
        environment_id=other_uat_id,
        domain_name="OTM1",
    )
    hidden_project = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="INT_SCOPE_HIDDEN_PROJECT"),
        headers=admin_header,
    ).json()
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
    )

    listed = client.get("/api/v1/modules/integration-mapping/definitions", headers=admin_header)
    visible_detail = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{visible['id']}",
        headers=admin_header,
    )
    hidden_detail = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{hidden_domain['id']}",
        headers=admin_header,
    )
    hidden_validate = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{hidden_domain['id']}/validate",
        headers=admin_header,
    )
    hidden_project_detail = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{hidden_project['id']}",
        headers=admin_header,
    )
    hidden_project_validate = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{hidden_project['id']}/validate",
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [visible["id"]]
    assert visible_detail.status_code == 200
    assert visible_detail.json()["id"] == visible["id"]
    assert visible_detail.json()["project_id"] == project_id
    assert visible_detail.json()["environment_id"] == uat_id
    assert visible_detail.json()["domain_name"] == "OTM1"
    assert hidden_detail.status_code == 404
    assert hidden_validate.status_code == 404
    assert hidden_project_detail.status_code == 404
    assert hidden_project_validate.status_code == 404


def test_integration_definitions_require_active_context_for_non_admin_access_and_create(
    client,
    admin_header,
    auth_header,
):
    created = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="INT_NO_CONTEXT_ADMIN"),
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/integration-mapping/definitions", headers=auth_header)
    detail = client.get(
        f"/api/v1/modules/integration-mapping/definitions/{created['id']}",
        headers=auth_header,
    )
    validate = client.post(
        f"/api/v1/modules/integration-mapping/definitions/{created['id']}/validate",
        headers=auth_header,
    )
    create = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="INT_NO_CONTEXT_USER"),
        headers=auth_header,
    )

    assert listed.status_code == 200
    assert listed.json()["items"] == []
    assert listed.json()["total"] == 0
    assert detail.status_code == 404
    assert detail.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
    assert validate.status_code == 404
    assert create.status_code == 403
    assert create.json()["code"] == "ACTIVE_CONTEXT_REQUIRED"


def test_integration_definition_dba_context_can_see_all_domains_in_active_environment(client, admin_header):
    project_id, uat_id, dev_id = create_project_with_environments(client, admin_header)
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
    )
    otm1 = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="INT_DBA_OTM1"),
        headers=admin_header,
    ).json()
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM2",
    )
    otm2 = client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="INT_DBA_OTM2"),
        headers=admin_header,
    ).json()
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=dev_id,
        domain_name="OTM3",
    )
    client.post(
        "/api/v1/modules/integration-mapping/definitions",
        json=definition_payload(code="INT_DBA_OTHER_ENV"),
        headers=admin_header,
    )
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
        can_view_all_domains=True,
    )

    listed = client.get("/api/v1/modules/integration-mapping/definitions", headers=admin_header)

    assert listed.status_code == 200
    assert {item["id"] for item in listed.json()["items"]} == {otm1["id"], otm2["id"]}


def test_get_integration_definition_rejects_missing_id(client, admin_header):
    response = client.get(
        "/api/v1/modules/integration-mapping/definitions/missing-definition",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "INTEGRATION_DEFINITION_NOT_FOUND"
