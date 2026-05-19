from pathlib import Path

from openpyxl import load_workbook

from otm_workbench.models import Artifact


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
                    "name": "region_name",
                    "label": "Region Name",
                    "target_column": "REGION_NAME",
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


def test_master_data_template_validation_uses_catalog_dictionary(client, admin_header):
    response = client.post("/api/v1/modules/master-data/templates/REGIONS_BASIC/validate", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["template_code"] == "REGIONS_BASIC"
    assert payload["valid"] is True
    assert payload["severity"] == "INFO"
    assert payload["issues"] == []
    assert payload["summary"] == {
        "sheet_count": 2,
        "field_count": 5,
        "validated_table_count": 2,
        "validated_column_count": 5,
    }


def test_master_data_template_build_workbook_creates_artifact(client, admin_header, db_session):
    response = client.post(
        "/api/v1/modules/master-data/templates/REGIONS_BASIC/build-workbook",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["template_code"] == "REGIONS_BASIC"
    assert payload["file_name"] == "regions_basic_v1.xlsx"
    assert payload["content_type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert payload["sheet_count"] == 2
    assert payload["field_count"] == 5

    artifact = db_session.query(Artifact).filter(Artifact.id == payload["artifact_id"]).one()
    assert artifact.source_module == "master_data"
    assert artifact.artifact_type == "master_data_template_workbook"
    assert artifact.sensitivity_level == "client_safe"

    workbook_path = Path(artifact.file_path)
    assert workbook_path.exists()
    workbook = load_workbook(workbook_path)
    assert workbook.sheetnames == ["REGIONS", "REGION_DETAILS"]
    assert [cell.value for cell in workbook["REGIONS"][1]] == ["Region GID", "Region XID", "Region Name"]
    assert [cell.value for cell in workbook["REGION_DETAILS"][1]] == ["Region GID", "Location GID"]
