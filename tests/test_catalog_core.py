from otm_workbench.models import ReferenceObject


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
