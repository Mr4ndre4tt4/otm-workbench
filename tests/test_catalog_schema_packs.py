from otm_workbench.models import (
    MacroObjectSchemaLink,
    SchemaFile,
    SchemaPack,
    SchemaPath,
    SchemaRoot,
    ServiceOperation,
)


def test_catalog_schema_pack_create_and_list_is_client_safe(client, admin_header):
    created = client.post(
        "/api/v1/catalog/schema-packs",
        json={
            "code": "OTM_26A_CORE",
            "name": "OTM 26A core contracts",
            "otm_version": "26A",
            "source_type": "LOCAL_FOLDER",
            "source_path": "C:/otm/contracts/26A",
            "content_hash": "hash-26a",
        },
        headers=admin_header,
    )

    assert created.status_code == 200
    payload = created.json()
    assert payload["code"] == "OTM_26A_CORE"
    assert payload["otm_version"] == "26A"
    assert payload["status"] == "DRAFT"
    assert payload["root_count"] == 0
    assert "source_path" not in payload

    listed = client.get("/api/v1/catalog/schema-packs?otm_version=26A", headers=admin_header)

    assert listed.status_code == 200
    list_payload = listed.json()
    assert list_payload["total"] == 1
    assert list_payload["items"][0]["code"] == "OTM_26A_CORE"
    assert "C:/otm/contracts/26A" not in str(list_payload)


def test_catalog_schema_roots_paths_and_operations_are_queryable(client, admin_header, db_session):
    pack = SchemaPack(
        code="OTM_26A_CORE",
        name="OTM 26A core contracts",
        otm_version="26A",
        source_type="LOCAL_FOLDER",
        source_path="C:/otm/contracts/26A",
        content_hash="hash-26a",
        status="READY",
        namespace_count=3,
        root_count=2,
        operation_count=1,
        created_by="admin@example.com",
    )
    db_session.add(pack)
    db_session.flush()
    schema_file = SchemaFile(
        schema_pack_id=pack.id,
        file_name="Order.xsd",
        relative_path="Order.xsd",
        file_type="XSD",
        namespace="http://xmlns.oracle.com/apps/otm",
        import_count=2,
        top_level_element_count=9,
        complex_type_count=49,
        status="PARSED",
    )
    db_session.add(schema_file)
    db_session.flush()
    root = SchemaRoot(
        schema_pack_id=pack.id,
        schema_file_id=schema_file.id,
        root_name="Release",
        namespace="http://xmlns.oracle.com/apps/otm",
        domain_area="ORDER",
        root_type="DOMAIN_ROOT",
        envelope_role="NONE",
        recommended_modules_json='["order_release_generator","integration_mapping"]',
        documentation="Synthetic docs only.",
    )
    db_session.add(root)
    db_session.flush()
    db_session.add_all(
        [
            SchemaPath(
                schema_root_id=root.id,
                parent_path=None,
                path="/Release",
                node_name="Release",
                data_type="ReleaseType",
                min_occurs="1",
                max_occurs="1",
                is_required=True,
                is_repeatable=False,
                documentation="Root release element.",
                source_file="Order.xsd",
                sequence_index=1,
            ),
            SchemaPath(
                schema_root_id=root.id,
                parent_path="/Release",
                path="/Release/ReleaseLine",
                node_name="ReleaseLine",
                data_type="ReleaseLineType",
                min_occurs="0",
                max_occurs="unbounded",
                is_required=False,
                is_repeatable=True,
                documentation="Release line collection.",
                source_file="Order.xsd",
                sequence_index=2,
            ),
        ]
    )
    db_session.add(
        ServiceOperation(
            schema_pack_id=pack.id,
            schema_file_id=schema_file.id,
            service_name="OrderReleaseService",
            operation_name="processAction",
            input_message="AgentMessage",
            output_message="AgentReplyMessage",
            fault_message="",
            target_namespace="http://xmlns.oracle.com/apps/otm/OrderReleaseService",
            related_roots_json='["Release"]',
        )
    )
    db_session.commit()

    roots = client.get(
        "/api/v1/catalog/schema-roots?recommended_module=order_release_generator",
        headers=admin_header,
    )
    paths = client.get(f"/api/v1/catalog/schema-roots/{root.id}/paths?query=ReleaseLine", headers=admin_header)
    operations = client.get("/api/v1/catalog/schema-operations?service_name=OrderReleaseService", headers=admin_header)

    assert roots.status_code == 200
    assert paths.status_code == 200
    assert operations.status_code == 200
    assert roots.json()["items"][0]["root_name"] == "Release"
    assert paths.json()["items"][0]["path"] == "/Release/ReleaseLine"
    assert paths.json()["items"][0]["is_repeatable"] is True
    assert operations.json()["items"][0]["operation_name"] == "processAction"
    assert "source_path" not in str(roots.json())
    assert "C:/otm/contracts/26A" not in str(operations.json())


def test_catalog_macro_object_schema_links_return_official_roots(client, admin_header, db_session):
    pack = SchemaPack(
        code="OTM_26A_CORE",
        name="OTM 26A core contracts",
        otm_version="26A",
        source_type="LOCAL_FOLDER",
        source_path="C:/otm/contracts/26A",
        content_hash="hash-26a",
        status="READY",
    )
    db_session.add(pack)
    db_session.flush()
    schema_file = SchemaFile(
        schema_pack_id=pack.id,
        file_name="Rate.xsd",
        relative_path="Rate.xsd",
        file_type="XSD",
        namespace="http://xmlns.oracle.com/apps/otm",
        status="PARSED",
    )
    db_session.add(schema_file)
    db_session.flush()
    root = SchemaRoot(
        schema_pack_id=pack.id,
        schema_file_id=schema_file.id,
        root_name="RATE_OFFERING",
        namespace="http://xmlns.oracle.com/apps/otm",
        domain_area="RATE",
        root_type="ROWSET",
        envelope_role="NONE",
        recommended_modules_json='["rates"]',
    )
    db_session.add(root)
    db_session.flush()
    db_session.add(
        MacroObjectSchemaLink(
            macro_object_code="RATE_OFFERING",
            schema_root_id=root.id,
            relationship_role="SEMANTIC_ROOT",
            confidence="HIGH",
            notes="Rate.xsd top-level RATE_OFFERING root.",
        )
    )
    db_session.commit()

    response = client.get("/api/v1/catalog/macro-objects/RATE_OFFERING/schema-links", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["macro_object_code"] == "RATE_OFFERING"
    assert payload["total"] == 1
    assert payload["items"][0]["root_name"] == "RATE_OFFERING"
    assert payload["items"][0]["relationship_role"] == "SEMANTIC_ROOT"
    assert payload["items"][0]["confidence"] == "HIGH"
