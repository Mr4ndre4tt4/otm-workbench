from otm_workbench.models import MacroObjectSchemaLink, ReferenceObject, SchemaFile, SchemaPack, SchemaRoot


def seed_reference_options(db_session):
    db_session.add_all(
        [
            ReferenceObject(
                object_type="RATE_SERVICE",
                gid="PUBLIC.RS_STANDARD",
                xid="RS_STANDARD",
                domain_name="PUBLIC",
                display_name="Standard service",
            ),
            ReferenceObject(
                object_type="RATE_SERVICE",
                gid="OTM1.RS_EXPRESS",
                xid="RS_EXPRESS",
                domain_name="OTM1",
                display_name="Express service",
            ),
            ReferenceObject(
                object_type="RATE_SERVICE",
                gid="OTM2.RS_OTHER",
                xid="RS_OTHER",
                domain_name="OTM2",
                display_name="Other service",
            ),
        ]
    )
    db_session.commit()


def test_catalog_health(client, admin_header):
    response = client.get("/api/v1/catalog/health", headers=admin_header)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["module"] == "catalog"


def test_catalog_table_detail_and_columns_use_data_dictionary(client, admin_header):
    detail = client.get("/api/v1/catalog/tables/RATE_GEO_COST", headers=admin_header)
    columns = client.get("/api/v1/catalog/tables/RATE_GEO_COST/columns", headers=admin_header)

    assert detail.status_code == 200
    assert columns.status_code == 200
    assert detail.json()["table_name"] == "RATE_GEO_COST"
    assert detail.json()["exists"] is True
    assert "RATE_GEO_COST_GROUP_GID" in [item["column_name"] for item in columns.json()["items"]]
    assert "file_path" not in str(detail.json())


def test_catalog_tables_list_supports_data_dictionary_search(client, admin_header):
    response = client.get("/api/v1/catalog/tables?query=rate_geo&limit=10", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    table_names = [item["table_name"] for item in payload["items"]]
    assert "RATE_GEO" in table_names
    assert "RATE_GEO_COST" in table_names
    assert payload["total"] >= len(payload["items"])
    assert all("file_path" not in item for item in payload["items"])
    assert all("data_category" in item for item in payload["items"])


def test_catalog_reference_options_filter_public_and_profile_domain(client, admin_header, db_session):
    seed_reference_options(db_session)

    response = client.get(
        "/api/v1/catalog/reference/options?object_type=RATE_SERVICE&domain_name=OTM1",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["object_type"] == "RATE_SERVICE"
    assert payload["allowed_domains"] == ["PUBLIC", "OTM1"]
    assert [item["gid"] for item in payload["items"]] == ["PUBLIC.RS_STANDARD", "OTM1.RS_EXPRESS"]
    assert "OTM2.RS_OTHER" not in str(payload)


def test_catalog_reference_options_use_active_context_domain_when_omitted(client, admin_header, db_session):
    seed_reference_options(db_session)
    context = client.post(
        "/api/v1/platform/active-context",
        json={"domain_name": "otm2"},
        headers=admin_header,
    )

    response = client.get(
        "/api/v1/catalog/reference/options?object_type=RATE_SERVICE",
        headers=admin_header,
    )

    assert context.status_code == 200
    assert response.status_code == 200
    payload = response.json()
    assert payload["domain_name"] == "OTM2"
    assert payload["allowed_domains"] == ["PUBLIC", "OTM2"]
    assert [item["gid"] for item in payload["items"]] == ["PUBLIC.RS_STANDARD", "OTM2.RS_OTHER"]
    assert "OTM1.RS_EXPRESS" not in str(payload)


def test_catalog_validate_table_blocks_transactional_table(client, admin_header):
    response = client.post(
        "/api/v1/catalog/validate/table",
        json={"table_name": "SHIPMENT", "usage": "cutover"},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["table_name"] == "SHIPMENT"
    assert payload["exists"] is True
    assert payload["allow_cutover"] is False
    assert payload["severity"] == "ERROR"
    assert "transactional" in payload["message"].lower()


def test_catalog_validate_column_reports_missing_column(client, admin_header):
    response = client.post(
        "/api/v1/catalog/validate/column",
        json={"table_name": "RATE_GEO_COST", "column_name": "MISSING_COLUMN"},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["table_name"] == "RATE_GEO_COST"
    assert payload["column_name"] == "MISSING_COLUMN"
    assert payload["exists"] is False
    assert payload["severity"] == "ERROR"


def test_catalog_validate_reference_uses_policy_and_domain_scope(client, admin_header):
    response = client.post(
        "/api/v1/catalog/validate/reference",
        json={
            "module_id": "rates",
            "field_name": "currency_gid",
            "value": "OTM2.BRL",
            "domain_name": "OTM1",
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert payload["severity"] == "ERROR"
    assert payload["policy"] == "MUST_EXIST"
    assert payload["object_type"] == "CURRENCY"
    assert payload["gid"] == "OTM2.BRL"


def test_catalog_validate_reference_uses_active_context_domain_when_omitted(client, admin_header, db_session):
    db_session.add(
        ReferenceObject(
            object_type="CURRENCY",
            gid="OTM2.BRL",
            xid="BRL",
            domain_name="OTM2",
            display_name="Brazilian Real",
        )
    )
    db_session.commit()
    context = client.post(
        "/api/v1/platform/active-context",
        json={"domain_name": "otm2"},
        headers=admin_header,
    )

    response = client.post(
        "/api/v1/catalog/validate/reference",
        json={
            "module_id": "rates",
            "field_name": "currency_gid",
            "value": "OTM2.BRL",
        },
        headers=admin_header,
    )

    assert context.status_code == 200
    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["severity"] == "INFO"
    assert payload["policy"] == "MUST_EXIST"
    assert payload["object_type"] == "CURRENCY"
    assert payload["gid"] == "OTM2.BRL"
    assert payload["domain_name"] == "OTM2"


def test_catalog_macro_objects_seed_and_list(client, admin_header, db_session):
    response = client.get("/api/v1/catalog/macro-objects", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    codes = [item["code"] for item in payload["items"]]
    assert "RATE_OFFERING" in codes
    assert "RATE_RECORD" in codes
    assert "ITEM" in codes
    assert "REGION" in codes
    assert payload["total"] >= 4


def test_catalog_macro_object_detail_expands_tables_and_dependencies(client, admin_header):
    response = client.get("/api/v1/catalog/macro-objects/RATE_RECORD", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "RATE_RECORD"
    assert payload["category"] == "RATES_SETUP"
    assert payload["allow_cutover"] is True
    assert "RATE_GEO" in [item["table_name"] for item in payload["tables"]]
    assert "RATE_GEO_COST" in [item["table_name"] for item in payload["tables"]]
    assert "RATE_OFFERING" in [item["depends_on_code"] for item in payload["dependencies"]]
    assert all(item["validated_by_datadict"] is True for item in payload["tables"])
    assert payload["summary"] == {
        "table_count": 4,
        "dependency_count": 1,
        "validated_table_count": 4,
        "all_tables_validated": True,
        "csvutil_table_count": 4,
        "cutover_table_count": 4,
    }


def test_catalog_macro_object_tables_endpoint(client, admin_header):
    response = client.get("/api/v1/catalog/macro-objects/ITEM/tables", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert "ITEM" in [item["table_name"] for item in payload["items"]]
    assert "PACKAGED_ITEM" in [item["table_name"] for item in payload["items"]]
    assert all(item["allow_csvutil"] is True for item in payload["items"])


def test_catalog_macro_object_load_plan_orders_dependencies_before_target(client, admin_header):
    response = client.get("/api/v1/catalog/macro-objects/RATE_RECORD/load-plan", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["macro_object_code"] == "RATE_RECORD"
    assert [item["macro_object_code"] for item in payload["items"]] == ["RATE_OFFERING", "RATE_RECORD"]
    assert payload["items"][0]["dependency_role"] == "DEPENDENCY"
    assert payload["items"][1]["dependency_role"] == "TARGET"
    assert payload["items"][1]["tables"] == [
        "RATE_GEO",
        "RATE_GEO_COST",
        "RATE_GEO_COST_GROUP",
        "X_LANE",
    ]
    assert payload["summary"] == {
        "step_count": 2,
        "dependency_count": 1,
        "target_table_count": 4,
        "all_target_tables_validated": True,
    }


def test_catalog_macro_object_data_dictionary_cross_check_includes_schema_links(client, admin_header, db_session):
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
        root_name="RATE_GEO",
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
            macro_object_code="RATE_RECORD",
            schema_root_id=root.id,
            relationship_role="SEMANTIC_ROOT",
            confidence="HIGH",
            functional_confidence="DATA_DICTIONARY_CROSSED",
            source_reference_status="PINNED",
            source_reference_label="Oracle Rate Record",
            source_reference_url="https://docs.oracle.com/en/cloud/saas/transportation/25c/otmol/planning/rate_manager/create_rate_record.htm",
        )
    )
    db_session.commit()

    response = client.get("/api/v1/catalog/macro-objects/RATE_RECORD/data-dictionary-cross-check", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["macro_object_code"] == "RATE_RECORD"
    assert payload["summary"] == {
        "target_table_count": 4,
        "validated_table_count": 4,
        "missing_table_count": 0,
        "schema_link_count": 1,
        "all_target_tables_validated": True,
        "all_schema_links_have_source_reference": True,
        "guidance_ready": True,
        "readiness_status": "READY",
    }
    assert [item["table_name"] for item in payload["table_checks"]] == [
        "RATE_GEO",
        "RATE_GEO_COST",
        "RATE_GEO_COST_GROUP",
        "X_LANE",
    ]
    assert all(item["exists_in_data_dictionary"] is True for item in payload["table_checks"])
    assert payload["schema_links"][0]["root_name"] == "RATE_GEO"
    assert payload["schema_links"][0]["root_display_label"] == "Rate Record / Rate Geo"
    assert payload["schema_links"][0]["data_dictionary_family"] == "RATE_GEO"
    assert payload["schema_links"][0]["functional_confidence"] == "DATA_DICTIONARY_CROSSED"
    assert "source_path" not in str(payload)
    assert "C:/otm/contracts/26A" not in str(payload)


def test_catalog_macro_object_cross_check_blocks_guidance_without_schema_links(client, admin_header):
    response = client.get("/api/v1/catalog/macro-objects/ITEM/data-dictionary-cross-check", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["macro_object_code"] == "ITEM"
    assert payload["summary"]["target_table_count"] == 4
    assert payload["summary"]["validated_table_count"] == 4
    assert payload["summary"]["schema_link_count"] == 0
    assert payload["summary"]["all_target_tables_validated"] is True
    assert payload["summary"]["all_schema_links_have_source_reference"] is False
    assert payload["summary"]["guidance_ready"] is False
    assert payload["summary"]["readiness_status"] == "BLOCKED_SCHEMA_LINKS"
