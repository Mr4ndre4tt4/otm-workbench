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
