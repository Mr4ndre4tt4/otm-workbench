from sqlalchemy import inspect


def valid_rows():
    return [
        {
            "release_gid": "OTM1.OR_SYN_001",
            "source_location_gid": "OTM1.SOURCE_A",
            "destination_location_gid": "OTM1.DEST_A",
            "early_pickup_date": "2026-05-20 08:00:00",
            "late_delivery_date": "2026-05-21 17:00:00",
            "item_gid": "OTM1.ITEM_A",
            "packaged_item_gid": "OTM1.PACK_A",
            "weight": "100",
            "weight_uom": "KG",
        },
        {
            "release_gid": "OTM1.OR_SYN_001",
            "source_location_gid": "OTM1.SOURCE_A",
            "destination_location_gid": "OTM1.DEST_A",
            "early_pickup_date": "2026-05-20 08:00:00",
            "late_delivery_date": "2026-05-21 17:00:00",
            "item_gid": "OTM1.ITEM_B",
            "packaged_item_gid": "OTM1.PACK_B",
            "weight": "55",
            "weight_uom": "KG",
        },
        {
            "release_gid": "OTM1.OR_SYN_002",
            "source_location_gid": "OTM1.SOURCE_B",
            "destination_location_gid": "OTM1.DEST_B",
            "early_pickup_date": "2026-05-22 08:00:00",
            "late_delivery_date": "2026-05-23 17:00:00",
            "item_gid": "OTM1.ITEM_C",
            "packaged_item_gid": "OTM1.PACK_C",
            "weight": "75",
            "weight_uom": "KG",
        },
    ]


def test_order_release_batch_tables_exist_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "order_release_batches" in table_names
    assert "order_release_batch_rows" in table_names


def test_create_order_release_batch_normalizes_rows_and_summary(client, admin_header):
    templates = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()
    template_id = templates["items"][0]["id"]

    response = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "synthetic_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["template_id"] == template_id
    assert payload["status"] == "VALID"
    assert payload["row_count"] == 3
    assert payload["release_count"] == 2
    assert payload["issue_count"] == 0
    assert payload["rows"][0]["row_number"] == 1
    assert payload["rows"][0]["release_gid"] == "OTM1.OR_SYN_001"
    assert payload["rows"][0]["normalized_json"]["weight_uom"] == "KG"


def test_create_order_release_batch_records_missing_required_columns_as_issues(client, admin_header):
    templates = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()
    template_id = templates["items"][0]["id"]
    rows = valid_rows()
    rows[0].pop("release_gid")

    response = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "synthetic_or.xlsx", "rows": rows},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "INVALID"
    assert payload["row_count"] == 3
    assert payload["release_count"] == 2
    assert payload["issue_count"] == 1
    assert payload["rows"][0]["status"] == "INVALID"
    assert payload["rows"][0]["issues"][0]["code"] == "MISSING_REQUIRED_COLUMN"
    assert payload["rows"][0]["issues"][0]["column"] == "release_gid"
    combined = str(payload)
    assert "cliente" not in combined.lower()
    assert "customer" not in combined.lower()


def test_get_order_release_batch_detail(client, admin_header):
    template_id = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()["items"][0]["id"]
    created = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "synthetic_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    ).json()

    response = client.get(f"/api/v1/modules/order-release-generator/batches/{created['id']}", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created["id"]
    assert len(payload["rows"]) == 3


def test_list_order_release_batches_returns_recent_backend_state(client, admin_header):
    template_id = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()["items"][0]["id"]
    created = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "synthetic_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    ).json()

    response = client.get("/api/v1/modules/order-release-generator/batches", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == created["id"]
    assert payload["items"][0]["status"] == "VALID"
    assert "rows" not in payload["items"][0]


def test_create_order_release_batch_rejects_missing_template(client, admin_header):
    response = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": "missing-template", "file_name": "synthetic_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "ORDER_RELEASE_TEMPLATE_NOT_FOUND"
