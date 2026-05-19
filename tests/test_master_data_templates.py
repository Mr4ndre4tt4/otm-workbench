def test_master_data_health(client, admin_header):
    response = client.get("/api/v1/modules/master-data/health", headers=admin_header)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "master_data",
        "catalog_macro_object_code": "REGION",
    }


def test_master_data_templates_seed_regions_basic(client, admin_header):
    response = client.get("/api/v1/modules/master-data/templates", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    template = payload["items"][0]
    assert template["code"] == "REGIONS_BASIC"
    assert template["name"] == "Regions Basic"
    assert template["version"] == 1
    assert template["status"] == "PUBLISHED"
    assert template["catalog_macro_object_code"] == "REGION"
    assert template["target_tables"] == ["REGION", "REGION_DETAIL"]
    assert template["data_category"] == "MASTER_DATA"


def test_master_data_template_detail_exposes_sheets_and_fields(client, admin_header):
    response = client.get("/api/v1/modules/master-data/templates/REGIONS_BASIC", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "REGIONS_BASIC"
    assert payload["sheets"] == [
        {
            "code": "REGIONS",
            "name": "Regions",
            "target_table": "REGION",
            "fields": [
                {
                    "name": "region_gid",
                    "label": "Region GID",
                    "target_column": "REGION_GID",
                    "required": True,
                    "data_type": "string",
                },
                {
                    "name": "region_xid",
                    "label": "Region XID",
                    "target_column": "REGION_XID",
                    "required": True,
                    "data_type": "string",
                },
                {
                    "name": "description",
                    "label": "Description",
                    "target_column": "DESCRIPTION",
                    "required": False,
                    "data_type": "string",
                },
            ],
        },
        {
            "code": "REGION_DETAILS",
            "name": "Region Details",
            "target_table": "REGION_DETAIL",
            "fields": [
                {
                    "name": "region_gid",
                    "label": "Region GID",
                    "target_column": "REGION_GID",
                    "required": True,
                    "data_type": "string",
                },
                {
                    "name": "location_gid",
                    "label": "Location GID",
                    "target_column": "LOCATION_GID",
                    "required": True,
                    "data_type": "string",
                },
            ],
        },
    ]
