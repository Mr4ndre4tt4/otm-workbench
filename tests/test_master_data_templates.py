import json
import zipfile
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook
from openpyxl import load_workbook
from sqlalchemy import text

from otm_workbench.models import Artifact, AuditLog, Evidence, Manifest


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
    assert payload["total"] == 2
    templates_by_code = {template["code"]: template for template in payload["items"]}
    template = templates_by_code["REGIONS_BASIC"]
    assert template["code"] == "REGIONS_BASIC"
    assert template["name"] == "Regions Basic"
    assert template["version"] == 1
    assert template["status"] == "PUBLISHED"
    assert template["catalog_macro_object_code"] == "REGION"
    assert template["target_tables"] == ["REGION", "REGION_DETAIL"]
    assert template["data_category"] == "MASTER_DATA"
    items_template = templates_by_code["ITEMS_PACKAGING_STANDARD"]
    assert items_template["name"] == "Items & Packaging Standard"
    assert items_template["catalog_macro_object_code"] == "ITEM"
    assert items_template["target_tables"] == ["ITEM", "SHIP_UNIT_SPEC", "PACKAGED_ITEM", "TI_HI"]


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


def test_master_data_items_packaging_template_detail_and_validation(client, admin_header):
    detail = client.get(
        "/api/v1/modules/master-data/templates/ITEMS_PACKAGING_STANDARD",
        headers=admin_header,
    )

    assert detail.status_code == 200
    payload = detail.json()
    assert payload["code"] == "ITEMS_PACKAGING_STANDARD"
    assert [sheet["code"] for sheet in payload["sheets"]] == ["ITEMS", "PACKAGING", "TI_HI"]
    assert payload["sheets"][0]["target_table"] == "ITEM"
    assert [field["target_column"] for field in payload["sheets"][0]["fields"]] == [
        "ITEM_GID",
        "ITEM_XID",
        "DESCRIPTION",
        "ITEM_TYPE_GID",
    ]
    assert payload["sheets"][1]["target_table"] == "PACKAGED_ITEM"
    assert payload["sheets"][2]["target_table"] == "TI_HI"

    validation = client.post(
        "/api/v1/modules/master-data/templates/ITEMS_PACKAGING_STANDARD/validate",
        headers=admin_header,
    )

    assert validation.status_code == 200
    validation_payload = validation.json()
    assert validation_payload["valid"] is True
    assert validation_payload["issues"] == []
    assert validation_payload["summary"] == {
        "sheet_count": 3,
        "field_count": 18,
        "validated_table_count": 3,
        "validated_column_count": 18,
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


def test_master_data_template_batch_upload_parses_workbook(client, admin_header, db_session):
    workbook = Workbook()
    regions = workbook.active
    regions.title = "REGIONS"
    regions.append(["Region GID", "Region XID", "Region Name"])
    regions.append(["SYN.REGION_001", "REGION_001", "Synthetic Region"])
    details = workbook.create_sheet("REGION_DETAILS")
    details.append(["Region GID", "Location GID"])
    details.append(["SYN.REGION_001", "SYN.LOCATION_001"])
    workbook_bytes = BytesIO()
    workbook.save(workbook_bytes)
    workbook_bytes.seek(0)

    response = client.post(
        "/api/v1/modules/master-data/templates/REGIONS_BASIC/batches",
        headers=admin_header,
        files={
            "file": (
                "regions_basic_upload.xlsx",
                workbook_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["template_code"] == "REGIONS_BASIC"
    assert payload["status"] == "PARSED"
    assert payload["file_name"] == "regions_basic_upload.xlsx"
    assert payload["sheet_count"] == 2
    assert payload["row_count"] == 2
    assert payload["issue_count"] == 0
    assert payload["sheet_summaries"] == [
        {"sheet_code": "REGIONS", "target_table": "REGION", "row_count": 1},
        {"sheet_code": "REGION_DETAILS", "target_table": "REGION_DETAIL", "row_count": 1},
    ]

    row = db_session.execute(
        text(
            "select template_code, status, file_name, row_count, issue_count "
            "from master_data_batches where id = :batch_id"
        ),
        {"batch_id": payload["batch_id"]},
    ).one()
    assert row.template_code == "REGIONS_BASIC"
    assert row.status == "PARSED"
    assert row.file_name == "regions_basic_upload.xlsx"
    assert row.row_count == 2
    assert row.issue_count == 0


def test_master_data_template_batch_upload_skips_generated_metadata_rows(
    client,
    admin_header,
):
    workbook = Workbook()
    regions = workbook.active
    regions.title = "REGIONS"
    regions.append(["Region GID", "Region XID", "Region Name"])
    regions.append(["region_gid", "region_xid", "region_name"])
    regions.append(["REGION_GID", "REGION_XID", "REGION_NAME"])
    regions.append(["SYN.REGION_001", "REGION_001", "Synthetic Region"])
    details = workbook.create_sheet("REGION_DETAILS")
    details.append(["Region GID", "Location GID"])
    details.append(["region_gid", "location_gid"])
    details.append(["REGION_GID", "LOCATION_GID"])
    details.append(["SYN.REGION_001", "SYN.LOCATION_001"])
    workbook_bytes = BytesIO()
    workbook.save(workbook_bytes)
    workbook_bytes.seek(0)

    response = client.post(
        "/api/v1/modules/master-data/templates/REGIONS_BASIC/batches",
        headers=admin_header,
        files={
            "file": (
                "regions_basic_generated_upload.xlsx",
                workbook_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "PARSED"
    assert payload["row_count"] == 2
    assert payload["sheet_summaries"] == [
        {"sheet_code": "REGIONS", "target_table": "REGION", "row_count": 1},
        {"sheet_code": "REGION_DETAILS", "target_table": "REGION_DETAIL", "row_count": 1},
    ]


def test_master_data_template_batch_upload_persists_parse_issues(client, admin_header, db_session):
    workbook = Workbook()
    regions = workbook.active
    regions.title = "REGIONS"
    regions.append(["Wrong Region", "Region XID", "Region Name"])
    regions.append(["SYN.REGION_001", "REGION_001", "Synthetic Region"])
    details = workbook.create_sheet("REGION_DETAILS")
    details.append(["Region GID", "Location GID"])
    details.append(["SYN.REGION_001", "SYN.LOCATION_001"])
    workbook_bytes = BytesIO()
    workbook.save(workbook_bytes)
    workbook_bytes.seek(0)

    response = client.post(
        "/api/v1/modules/master-data/templates/REGIONS_BASIC/batches",
        headers=admin_header,
        files={
            "file": (
                "regions_basic_bad_headers.xlsx",
                workbook_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["template_code"] == "REGIONS_BASIC"
    assert payload["status"] == "PARSE_FAILED"
    assert payload["file_name"] == "regions_basic_bad_headers.xlsx"
    assert payload["row_count"] == 0
    assert payload["issue_count"] == 1
    assert payload["issues"] == [
        {
            "code": "MASTER_DATA_WORKBOOK_HEADERS_INVALID",
            "severity": "ERROR",
            "sheet_code": "REGIONS",
            "message": "Uploaded workbook headers do not match the template.",
            "expected_headers": ["Region GID", "Region XID", "Region Name"],
            "actual_headers": ["Wrong Region", "Region XID", "Region Name"],
        }
    ]

    row = db_session.execute(
        text(
            "select status, row_count, issue_count, issues_json "
            "from master_data_batches where id = :batch_id"
        ),
        {"batch_id": payload["batch_id"]},
    ).one()
    assert row.status == "PARSE_FAILED"
    assert row.row_count == 0
    assert row.issue_count == 1
    assert "MASTER_DATA_WORKBOOK_HEADERS_INVALID" in row.issues_json


def test_master_data_batch_relationship_validation_persists_orphan_issues(
    client,
    admin_header,
    db_session,
):
    workbook = Workbook()
    regions = workbook.active
    regions.title = "REGIONS"
    regions.append(["Region GID", "Region XID", "Region Name"])
    regions.append(["SYN.REGION_001", "REGION_001", "Synthetic Region"])
    details = workbook.create_sheet("REGION_DETAILS")
    details.append(["Region GID", "Location GID"])
    details.append(["SYN.REGION_999", "SYN.LOCATION_001"])
    workbook_bytes = BytesIO()
    workbook.save(workbook_bytes)
    workbook_bytes.seek(0)
    batch_response = client.post(
        "/api/v1/modules/master-data/templates/REGIONS_BASIC/batches",
        headers=admin_header,
        files={
            "file": (
                "regions_basic_orphan_detail.xlsx",
                workbook_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    batch_id = batch_response.json()["batch_id"]

    response = client.post(
        f"/api/v1/modules/master-data/batches/{batch_id}/validate-relationships",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"] == batch_id
    assert payload["status"] == "RELATIONSHIP_FAILED"
    assert payload["issue_count"] == 1
    assert payload["issues"] == [
        {
            "code": "MASTER_DATA_RELATIONSHIP_ORPHAN",
            "severity": "ERROR",
            "sheet_code": "REGION_DETAILS",
            "field_name": "region_gid",
            "row_number": 2,
            "message": "Child row references a parent key that does not exist in the same batch.",
            "parent_sheet_code": "REGIONS",
            "parent_field_name": "region_gid",
            "missing_value": "SYN.REGION_999",
        }
    ]

    row = db_session.execute(
        text(
            "select status, issue_count, issues_json "
            "from master_data_batches where id = :batch_id"
        ),
        {"batch_id": batch_id},
    ).one()
    assert row.status == "RELATIONSHIP_FAILED"
    assert row.issue_count == 1
    assert "MASTER_DATA_RELATIONSHIP_ORPHAN" in row.issues_json


def test_master_data_batch_relationship_validation_is_idempotent(client, admin_header):
    workbook = Workbook()
    regions = workbook.active
    regions.title = "REGIONS"
    regions.append(["Region GID", "Region XID", "Region Name"])
    regions.append(["SYN.REGION_001", "REGION_001", "Synthetic Region"])
    details = workbook.create_sheet("REGION_DETAILS")
    details.append(["Region GID", "Location GID"])
    details.append(["SYN.REGION_001", "SYN.LOCATION_001"])
    workbook_bytes = BytesIO()
    workbook.save(workbook_bytes)
    workbook_bytes.seek(0)
    batch_response = client.post(
        "/api/v1/modules/master-data/templates/REGIONS_BASIC/batches",
        headers=admin_header,
        files={
            "file": (
                "regions_basic_upload.xlsx",
                workbook_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    batch_id = batch_response.json()["batch_id"]
    first_response = client.post(
        f"/api/v1/modules/master-data/batches/{batch_id}/validate-relationships",
        headers=admin_header,
    )

    second_response = client.post(
        f"/api/v1/modules/master-data/batches/{batch_id}/validate-relationships",
        headers=admin_header,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json() == {
        "batch_id": batch_id,
        "status": "RELATIONSHIP_VALIDATED",
        "issue_count": 0,
        "issues": [],
    }


def test_master_data_batch_mapping_requires_relationship_validation(client, admin_header):
    workbook = Workbook()
    regions = workbook.active
    regions.title = "REGIONS"
    regions.append(["Region GID", "Region XID", "Region Name"])
    regions.append(["SYN.REGION_001", "REGION_001", "Synthetic Region"])
    details = workbook.create_sheet("REGION_DETAILS")
    details.append(["Region GID", "Location GID"])
    details.append(["SYN.REGION_001", "SYN.LOCATION_001"])
    workbook_bytes = BytesIO()
    workbook.save(workbook_bytes)
    workbook_bytes.seek(0)
    batch_response = client.post(
        "/api/v1/modules/master-data/templates/REGIONS_BASIC/batches",
        headers=admin_header,
        files={
            "file": (
                "regions_basic_upload.xlsx",
                workbook_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    batch_id = batch_response.json()["batch_id"]

    response = client.post(f"/api/v1/modules/master-data/batches/{batch_id}/map", headers=admin_header)

    assert response.status_code == 409
    payload = response.json()
    assert payload["code"] == "MASTER_DATA_BATCH_NOT_MAPPABLE"
    assert "relationship-validated" in payload["details"]["error"]


def test_master_data_batch_mapping_creates_canonical_records(client, admin_header, db_session):
    workbook = Workbook()
    regions = workbook.active
    regions.title = "REGIONS"
    regions.append(["Region GID", "Region XID", "Region Name"])
    regions.append(["SYN.REGION_001", "REGION_001", "Synthetic Region"])
    details = workbook.create_sheet("REGION_DETAILS")
    details.append(["Region GID", "Location GID"])
    details.append(["SYN.REGION_001", "SYN.LOCATION_001"])
    workbook_bytes = BytesIO()
    workbook.save(workbook_bytes)
    workbook_bytes.seek(0)
    batch_response = client.post(
        "/api/v1/modules/master-data/templates/REGIONS_BASIC/batches",
        headers=admin_header,
        files={
            "file": (
                "regions_basic_upload.xlsx",
                workbook_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    batch_id = batch_response.json()["batch_id"]
    client.post(
        f"/api/v1/modules/master-data/batches/{batch_id}/validate-relationships",
        headers=admin_header,
    )

    response = client.post(f"/api/v1/modules/master-data/batches/{batch_id}/map", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"] == batch_id
    assert payload["status"] == "MAPPED"
    assert payload["canonical_record_count"] == 2
    assert payload["records"] == [
        {
            "sheet_code": "REGIONS",
            "target_table": "REGION",
            "record_index": 1,
            "payload": {
                "REGION_GID": "SYN.REGION_001",
                "REGION_XID": "REGION_001",
                "REGION_NAME": "Synthetic Region",
            },
        },
        {
            "sheet_code": "REGION_DETAILS",
            "target_table": "REGION_DETAIL",
            "record_index": 1,
            "payload": {
                "REGION_GID": "SYN.REGION_001",
                "LOCATION_GID": "SYN.LOCATION_001",
            },
        },
    ]

    rows = db_session.execute(
        text(
            "select sheet_code, target_table, record_index, payload_json "
            "from master_data_canonical_records where batch_id = :batch_id"
        ),
        {"batch_id": batch_id},
    ).all()
    assert len(rows) == 2
    rows_by_sheet = {row.sheet_code: row for row in rows}
    assert rows_by_sheet["REGIONS"].target_table == "REGION"
    assert '"REGION_GID": "SYN.REGION_001"' in rows_by_sheet["REGIONS"].payload_json


def test_master_data_batch_build_output_creates_output_records(client, admin_header, db_session):
    workbook = Workbook()
    regions = workbook.active
    regions.title = "REGIONS"
    regions.append(["Region GID", "Region XID", "Region Name"])
    regions.append(["SYN.REGION_001", "REGION_001", "Synthetic Region"])
    details = workbook.create_sheet("REGION_DETAILS")
    details.append(["Region GID", "Location GID"])
    details.append(["SYN.REGION_001", "SYN.LOCATION_001"])
    workbook_bytes = BytesIO()
    workbook.save(workbook_bytes)
    workbook_bytes.seek(0)
    batch_response = client.post(
        "/api/v1/modules/master-data/templates/REGIONS_BASIC/batches",
        headers=admin_header,
        files={
            "file": (
                "regions_basic_upload.xlsx",
                workbook_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    batch_id = batch_response.json()["batch_id"]
    client.post(
        f"/api/v1/modules/master-data/batches/{batch_id}/validate-relationships",
        headers=admin_header,
    )
    client.post(f"/api/v1/modules/master-data/batches/{batch_id}/map", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/master-data/batches/{batch_id}/build-output",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"] == batch_id
    assert payload["status"] == "OUTPUT_BUILT"
    assert payload["output_record_count"] == 2
    assert payload["records"] == [
        {
            "target_table": "REGION",
            "record_index": 1,
            "payload": {
                "REGION_GID": "SYN.REGION_001",
                "REGION_NAME": "Synthetic Region",
                "REGION_XID": "REGION_001",
            },
        },
        {
            "target_table": "REGION_DETAIL",
            "record_index": 1,
            "payload": {
                "LOCATION_GID": "SYN.LOCATION_001",
                "REGION_GID": "SYN.REGION_001",
            },
        },
    ]

    rows = db_session.execute(
        text(
            "select target_table, record_index, payload_json "
            "from master_data_output_records where batch_id = :batch_id"
        ),
        {"batch_id": batch_id},
    ).all()
    assert len(rows) == 2
    rows_by_table = {row.target_table: row for row in rows}
    assert rows_by_table["REGION"].record_index == 1
    assert '"REGION_XID": "REGION_001"' in rows_by_table["REGION"].payload_json


def test_master_data_batch_build_csv_creates_otm_csv_files(client, admin_header, db_session):
    workbook = Workbook()
    regions = workbook.active
    regions.title = "REGIONS"
    regions.append(["Region GID", "Region XID", "Region Name"])
    regions.append(["SYN.REGION_001", "REGION_001", "Synthetic Region"])
    details = workbook.create_sheet("REGION_DETAILS")
    details.append(["Region GID", "Location GID"])
    details.append(["SYN.REGION_001", "SYN.LOCATION_001"])
    workbook_bytes = BytesIO()
    workbook.save(workbook_bytes)
    workbook_bytes.seek(0)
    batch_response = client.post(
        "/api/v1/modules/master-data/templates/REGIONS_BASIC/batches",
        headers=admin_header,
        files={
            "file": (
                "regions_basic_upload.xlsx",
                workbook_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    batch_id = batch_response.json()["batch_id"]
    client.post(
        f"/api/v1/modules/master-data/batches/{batch_id}/validate-relationships",
        headers=admin_header,
    )
    client.post(f"/api/v1/modules/master-data/batches/{batch_id}/map", headers=admin_header)
    client.post(f"/api/v1/modules/master-data/batches/{batch_id}/build-output", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/master-data/batches/{batch_id}/build-csv",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"] == batch_id
    assert payload["status"] == "CSV_BUILT"
    assert payload["csv_file_count"] == 2
    assert payload["files"][0]["table_name"] == "REGION"
    assert payload["files"][0]["file_name"] == "001_REGION.csv"
    assert payload["files"][0]["row_count"] == 1
    assert payload["files"][0]["content"].splitlines() == [
        "REGION",
        "REGION_GID,REGION_XID,REGION_NAME",
        "SYN.REGION_001,REGION_001,Synthetic Region",
    ]
    assert payload["files"][1]["table_name"] == "REGION_DETAIL"
    assert payload["files"][1]["file_name"] == "002_REGION_DETAIL.csv"
    assert payload["files"][1]["content"].splitlines() == [
        "REGION_DETAIL",
        "REGION_GID,LOCATION_GID",
        "SYN.REGION_001,SYN.LOCATION_001",
    ]

    rows = db_session.execute(
        text(
            "select table_name, file_name, row_count, content "
            "from master_data_csv_files where batch_id = :batch_id order by file_name"
        ),
        {"batch_id": batch_id},
    ).all()
    assert len(rows) == 2
    assert rows[0].table_name == "REGION"
    assert rows[0].file_name == "001_REGION.csv"
    assert rows[0].row_count == 1
    assert rows[0].content.startswith("REGION\nREGION_GID,REGION_XID,REGION_NAME")


def test_master_data_batch_export_csv_package_creates_zip_manifest_and_evidence(
    client,
    admin_header,
    db_session,
):
    workbook = Workbook()
    regions = workbook.active
    regions.title = "REGIONS"
    regions.append(["Region GID", "Region XID", "Region Name"])
    regions.append(["SYN.REGION_001", "REGION_001", "Synthetic Region"])
    details = workbook.create_sheet("REGION_DETAILS")
    details.append(["Region GID", "Location GID"])
    details.append(["SYN.REGION_001", "SYN.LOCATION_001"])
    workbook_bytes = BytesIO()
    workbook.save(workbook_bytes)
    workbook_bytes.seek(0)
    batch_response = client.post(
        "/api/v1/modules/master-data/templates/REGIONS_BASIC/batches",
        headers=admin_header,
        files={
            "file": (
                "regions_basic_upload.xlsx",
                workbook_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    batch_id = batch_response.json()["batch_id"]
    client.post(
        f"/api/v1/modules/master-data/batches/{batch_id}/validate-relationships",
        headers=admin_header,
    )
    client.post(f"/api/v1/modules/master-data/batches/{batch_id}/map", headers=admin_header)
    client.post(f"/api/v1/modules/master-data/batches/{batch_id}/build-output", headers=admin_header)
    client.post(f"/api/v1/modules/master-data/batches/{batch_id}/build-csv", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/master-data/batches/{batch_id}/export-csv-package",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"] == batch_id
    assert payload["status"] == "EXPORTED"
    assert payload["file_name"].startswith("master_data_batch_")
    assert payload["file_name"].endswith(".zip")
    assert payload["tables"] == ["REGION", "REGION_DETAIL"]

    artifact = db_session.query(Artifact).filter(Artifact.id == payload["artifact_id"]).one()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "master_data.batch.export_csv").one()
    assert artifact.source_module == "master_data"
    assert artifact.artifact_type == "master_data_csv_zip"
    assert artifact.content_type == "application/zip"
    assert artifact.sensitivity_level == "client_safe"
    assert evidence.evidence_type == "master_data_csv_export"
    assert evidence.client_safe is True
    assert str(artifact.id) in audit.metadata_json

    with zipfile.ZipFile(artifact.file_path) as archive:
        names = sorted(archive.namelist())
        assert names == ["csv/001_REGION.csv", "csv/002_REGION_DETAIL.csv", "manifest.json"]
        csv_text = archive.read("csv/001_REGION.csv").decode("utf-8")
        manifest_payload = json.loads(archive.read("manifest.json").decode("utf-8"))

    assert csv_text.splitlines()[0] == "REGION"
    assert manifest_payload["manifest_type"] == "master_data_csv_export"
    assert manifest_payload["schema_version"] == "master-data-csv-export-manifest/v1"
    assert manifest_payload["source_entity_id"] == batch_id
    assert manifest_payload["files"][0]["file_name"] == "001_REGION.csv"
    assert json.loads(manifest.manifest_json)["manifest_type"] == "master_data_csv_export"
