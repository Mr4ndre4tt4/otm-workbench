import json
from pathlib import Path
from typing import BinaryIO

from openpyxl import load_workbook
from openpyxl import Workbook
from sqlalchemy.orm import Session

from otm_workbench.catalog.services import validate_column, validate_table
from otm_workbench.models import (
    Artifact,
    MasterDataBatch,
    MasterDataCanonicalRecord,
    MasterDataOutputRecord,
    MasterDataTemplate,
)
from otm_workbench.platform.services import file_sha256


REGIONS_BASIC_TEMPLATE = {
    "code": "REGIONS_BASIC",
    "name": "Regions Basic",
    "version": 1,
    "status": "PUBLISHED",
    "catalog_macro_object_code": "REGION",
    "data_category": "MASTER_DATA",
    "target_tables": ["REGION", "REGION_DETAIL"],
    "sheets": [
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
    ],
    "description": "Synthetic starter template for region master data.",
}


def seed_master_data_templates(db: Session) -> None:
    exists = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == REGIONS_BASIC_TEMPLATE["code"]).first()
    if exists:
        if not json.loads(exists.sheets_json):
            exists.sheets_json = json.dumps(REGIONS_BASIC_TEMPLATE["sheets"])
            db.commit()
        return
    db.add(
        MasterDataTemplate(
            code=REGIONS_BASIC_TEMPLATE["code"],
            name=REGIONS_BASIC_TEMPLATE["name"],
            version=REGIONS_BASIC_TEMPLATE["version"],
            status=REGIONS_BASIC_TEMPLATE["status"],
            catalog_macro_object_code=REGIONS_BASIC_TEMPLATE["catalog_macro_object_code"],
            data_category=REGIONS_BASIC_TEMPLATE["data_category"],
            target_tables_json=json.dumps(REGIONS_BASIC_TEMPLATE["target_tables"]),
            sheets_json=json.dumps(REGIONS_BASIC_TEMPLATE["sheets"]),
            description=REGIONS_BASIC_TEMPLATE["description"],
        )
    )
    db.commit()


def serialize_master_data_template(template: MasterDataTemplate) -> dict[str, object]:
    return {
        "id": template.id,
        "code": template.code,
        "name": template.name,
        "version": template.version,
        "status": template.status,
        "catalog_macro_object_code": template.catalog_macro_object_code,
        "data_category": template.data_category,
        "target_tables": json.loads(template.target_tables_json),
        "sheets": json.loads(template.sheets_json),
        "description": template.description,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }


def validate_master_data_template(template: MasterDataTemplate, dictionary_root: Path) -> dict[str, object]:
    sheets = json.loads(template.sheets_json)
    issues = []
    validated_tables = set()
    validated_column_count = 0
    field_count = 0
    for sheet in sheets:
        target_table = sheet["target_table"]
        table_result = validate_table(dictionary_root, target_table, usage="cutover")
        if table_result["exists"] and table_result["severity"] != "ERROR":
            validated_tables.add(target_table)
        else:
            issues.append(
                {
                    "code": "MASTER_DATA_TEMPLATE_TABLE_INVALID",
                    "severity": "ERROR",
                    "sheet_code": sheet["code"],
                    "target_table": target_table,
                    "message": table_result["message"],
                }
            )
        for field in sheet["fields"]:
            field_count += 1
            column_result = validate_column(dictionary_root, target_table, field["target_column"])
            if column_result["exists"]:
                validated_column_count += 1
            else:
                issues.append(
                    {
                        "code": "MASTER_DATA_TEMPLATE_COLUMN_INVALID",
                        "severity": "ERROR",
                        "sheet_code": sheet["code"],
                        "field_name": field["name"],
                        "target_table": target_table,
                        "target_column": field["target_column"],
                        "message": column_result["message"],
                    }
                )
    return {
        "template_code": template.code,
        "valid": not issues,
        "severity": "INFO" if not issues else "ERROR",
        "issues": issues,
        "summary": {
            "sheet_count": len(sheets),
            "field_count": field_count,
            "validated_table_count": len(validated_tables),
            "validated_column_count": validated_column_count,
        },
    }


def build_master_data_template_workbook(
    db: Session,
    template: MasterDataTemplate,
    artifact_root: Path,
) -> dict[str, object]:
    sheets = json.loads(template.sheets_json)
    workbook = Workbook()
    default_sheet = workbook.active
    field_count = 0

    for index, sheet in enumerate(sheets):
        worksheet = default_sheet if index == 0 else workbook.create_sheet()
        worksheet.title = sheet["code"][:31]
        fields = sheet["fields"]
        field_count += len(fields)
        worksheet.append([field["label"] for field in fields])
        worksheet.append([field["name"] for field in fields])
        worksheet.append([field["target_column"] for field in fields])

    output_dir = artifact_root / "master_data" / "templates" / template.code.lower()
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{template.code.lower()}_v{template.version}.xlsx"
    output_path = output_dir / file_name
    workbook.save(output_path)

    digest, size = file_sha256(str(output_path))
    artifact = Artifact(
        source_module="master_data",
        artifact_type="master_data_template_workbook",
        file_path=str(output_path),
        file_name=file_name,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        sha256=digest,
        size_bytes=size,
        sensitivity_level="client_safe",
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return {
        "template_code": template.code,
        "artifact_id": artifact.id,
        "file_name": artifact.file_name,
        "content_type": artifact.content_type,
        "sheet_count": len(sheets),
        "field_count": field_count,
    }


def parse_master_data_template_workbook(
    db: Session,
    template: MasterDataTemplate,
    file_obj: BinaryIO,
    file_name: str,
    content_type: str,
) -> dict[str, object]:
    sheets = json.loads(template.sheets_json)
    workbook = load_workbook(file_obj, data_only=True)
    sheet_summaries = []
    parsed_rows: dict[str, list[dict[str, object]]] = {}
    issues = []
    row_count = 0

    for sheet in sheets:
        if sheet["code"] not in workbook.sheetnames:
            issues.append(
                {
                    "code": "MASTER_DATA_WORKBOOK_SHEET_MISSING",
                    "severity": "ERROR",
                    "sheet_code": sheet["code"],
                    "message": "Uploaded workbook is missing a template sheet.",
                }
            )
            continue
        worksheet = workbook[sheet["code"]]
        fields = sheet["fields"]
        expected_headers = [field["label"] for field in fields]
        actual_headers = [cell.value for cell in worksheet[1]][: len(expected_headers)]
        if actual_headers != expected_headers:
            issues.append(
                {
                    "code": "MASTER_DATA_WORKBOOK_HEADERS_INVALID",
                    "severity": "ERROR",
                    "sheet_code": sheet["code"],
                    "message": "Uploaded workbook headers do not match the template.",
                    "expected_headers": expected_headers,
                    "actual_headers": actual_headers,
                }
            )
            continue

        sheet_rows = []
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            values = list(row[: len(fields)])
            if all(value is None for value in values):
                continue
            parsed_row = {field["name"]: values[index] for index, field in enumerate(fields)}
            sheet_rows.append(parsed_row)

        parsed_rows[sheet["code"]] = sheet_rows
        sheet_row_count = len(sheet_rows)
        row_count += sheet_row_count
        sheet_summaries.append(
            {
                "sheet_code": sheet["code"],
                "target_table": sheet["target_table"],
                "row_count": sheet_row_count,
            }
        )

    batch = MasterDataBatch(
        template_id=template.id,
        template_code=template.code,
        status="PARSED",
        file_name=file_name,
        content_type=content_type,
        sheet_summaries_json=json.dumps(sheet_summaries),
        parsed_rows_json=json.dumps(parsed_rows, sort_keys=True),
        issues_json=json.dumps(issues, sort_keys=True),
        row_count=0 if issues else row_count,
        issue_count=len(issues),
    )
    if issues:
        batch.status = "PARSE_FAILED"
    db.add(batch)
    db.commit()
    db.refresh(batch)

    return {
        "batch_id": batch.id,
        "template_code": batch.template_code,
        "status": batch.status,
        "file_name": batch.file_name,
        "sheet_count": len(sheet_summaries),
        "row_count": batch.row_count,
        "issue_count": batch.issue_count,
        "sheet_summaries": sheet_summaries,
        "issues": issues,
    }


def map_master_data_batch_to_canonical_records(
    db: Session,
    template: MasterDataTemplate,
    batch: MasterDataBatch,
) -> dict[str, object]:
    if batch.status != "PARSED":
        raise ValueError("Only parsed Master Data batches can be mapped.")

    sheets = json.loads(template.sheets_json)
    parsed_rows = json.loads(batch.parsed_rows_json)
    db.query(MasterDataCanonicalRecord).filter(
        MasterDataCanonicalRecord.batch_id == batch.id
    ).delete()

    response_records = []
    for sheet in sheets:
        fields = sheet["fields"]
        rows = parsed_rows.get(sheet["code"], [])
        for index, parsed_row in enumerate(rows, start=1):
            payload = {
                field["target_column"]: parsed_row.get(field["name"])
                for field in fields
                if field["name"] in parsed_row
            }
            canonical_record = MasterDataCanonicalRecord(
                batch_id=batch.id,
                template_code=batch.template_code,
                sheet_code=sheet["code"],
                target_table=sheet["target_table"],
                record_index=index,
                payload_json=json.dumps(payload, sort_keys=True),
            )
            db.add(canonical_record)
            response_records.append(
                {
                    "sheet_code": sheet["code"],
                    "target_table": sheet["target_table"],
                    "record_index": index,
                    "payload": payload,
                }
            )

    batch.status = "MAPPED"
    db.commit()

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "canonical_record_count": len(response_records),
        "records": response_records,
    }


def build_master_data_output_records(
    db: Session,
    batch: MasterDataBatch,
) -> dict[str, object]:
    if batch.status != "MAPPED":
        raise ValueError("Only mapped Master Data batches can build output records.")

    db.query(MasterDataOutputRecord).filter(MasterDataOutputRecord.batch_id == batch.id).delete()
    canonical_records = (
        db.query(MasterDataCanonicalRecord)
        .filter(MasterDataCanonicalRecord.batch_id == batch.id)
        .order_by(MasterDataCanonicalRecord.created_at, MasterDataCanonicalRecord.record_index)
        .all()
    )

    response_records = []
    for canonical_record in canonical_records:
        payload = json.loads(canonical_record.payload_json)
        output_record = MasterDataOutputRecord(
            batch_id=batch.id,
            template_code=batch.template_code,
            target_table=canonical_record.target_table,
            record_index=canonical_record.record_index,
            payload_json=json.dumps(payload, sort_keys=True),
        )
        db.add(output_record)
        response_records.append(
            {
                "target_table": canonical_record.target_table,
                "record_index": canonical_record.record_index,
                "payload": payload,
            }
        )

    batch.status = "OUTPUT_BUILT"
    db.commit()

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "output_record_count": len(response_records),
        "records": response_records,
    }
