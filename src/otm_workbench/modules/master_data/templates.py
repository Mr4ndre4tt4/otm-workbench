import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from openpyxl import load_workbook
from openpyxl import Workbook
from sqlalchemy.orm import Session

from otm_workbench.catalog.services import validate_column, validate_table
from otm_workbench.models import (
    Artifact,
    AuditLog,
    Evidence,
    Manifest,
    MasterDataBatch,
    MasterDataCanonicalRecord,
    MasterDataCsvFile,
    MasterDataOutputRecord,
    MasterDataTemplate,
)
from otm_workbench.modules.rates.csv_preview import build_otm_csv_preview
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

ITEMS_PACKAGING_STANDARD_TEMPLATE = {
    "code": "ITEMS_PACKAGING_STANDARD",
    "name": "Items & Packaging Standard",
    "version": 1,
    "status": "PUBLISHED",
    "catalog_macro_object_code": "ITEM",
    "data_category": "MASTER_DATA",
    "target_tables": ["ITEM", "SHIP_UNIT_SPEC", "PACKAGED_ITEM", "TI_HI"],
    "sheets": [
        {
            "code": "ITEMS",
            "name": "Items",
            "target_table": "ITEM",
            "fields": [
                {
                    "name": "item_gid",
                    "label": "Item GID",
                    "target_column": "ITEM_GID",
                    "required": True,
                    "data_type": "string",
                },
                {
                    "name": "item_xid",
                    "label": "Item XID",
                    "target_column": "ITEM_XID",
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
                {
                    "name": "item_type_gid",
                    "label": "Item Type GID",
                    "target_column": "ITEM_TYPE_GID",
                    "required": False,
                    "data_type": "string",
                },
            ],
        },
        {
            "code": "PACKAGING",
            "name": "Packaging",
            "target_table": "PACKAGED_ITEM",
            "fields": [
                {
                    "name": "packaged_item_gid",
                    "label": "Packaged Item GID",
                    "target_column": "PACKAGED_ITEM_GID",
                    "required": True,
                    "data_type": "string",
                },
                {
                    "name": "packaged_item_xid",
                    "label": "Packaged Item XID",
                    "target_column": "PACKAGED_ITEM_XID",
                    "required": True,
                    "data_type": "string",
                },
                {
                    "name": "item_gid",
                    "label": "Item GID",
                    "target_column": "ITEM_GID",
                    "required": True,
                    "data_type": "string",
                },
                {
                    "name": "packaging_unit_gid",
                    "label": "Packaging Unit GID",
                    "target_column": "PACKAGING_UNIT_GID",
                    "required": False,
                    "data_type": "string",
                },
                {
                    "name": "weight",
                    "label": "Weight",
                    "target_column": "PACKAGE_SHIP_UNIT_WEIGHT",
                    "required": False,
                    "data_type": "number",
                },
                {
                    "name": "weight_uom",
                    "label": "Weight UOM",
                    "target_column": "PACKAGE_SHIP_UNIT_WEIGHT_UOM",
                    "required": False,
                    "data_type": "string",
                },
                {
                    "name": "volume",
                    "label": "Volume",
                    "target_column": "PACKAGE_SU_VOLUME",
                    "required": False,
                    "data_type": "number",
                },
                {
                    "name": "volume_uom",
                    "label": "Volume UOM",
                    "target_column": "PACKAGE_SU_VOLUME_UOM_CODE",
                    "required": False,
                    "data_type": "string",
                },
                {
                    "name": "length",
                    "label": "Length",
                    "target_column": "PACKAGE_SU_LENGTH",
                    "required": False,
                    "data_type": "number",
                },
                {
                    "name": "width",
                    "label": "Width",
                    "target_column": "PACKAGE_SU_WIDTH",
                    "required": False,
                    "data_type": "number",
                },
            ],
        },
        {
            "code": "TI_HI",
            "name": "TI HI",
            "target_table": "TI_HI",
            "fields": [
                {
                    "name": "packaged_item_gid",
                    "label": "Packaged Item GID",
                    "target_column": "PACKAGED_ITEM_GID",
                    "required": True,
                    "data_type": "string",
                },
                {
                    "name": "packaging_unit_gid",
                    "label": "Packaging Unit GID",
                    "target_column": "PACKAGING_UNIT_GID",
                    "required": False,
                    "data_type": "string",
                },
                {
                    "name": "num_layers",
                    "label": "Number of Layers",
                    "target_column": "NUM_LAYERS",
                    "required": False,
                    "data_type": "number",
                },
                {
                    "name": "quantity_per_layer",
                    "label": "Quantity per Layer",
                    "target_column": "QUANTITY_PER_LAYER",
                    "required": False,
                    "data_type": "number",
                },
            ],
        },
    ],
    "description": "Synthetic starter template for item and packaged item master data.",
}

MASTER_DATA_TEMPLATE_SEEDS = [
    REGIONS_BASIC_TEMPLATE,
    ITEMS_PACKAGING_STANDARD_TEMPLATE,
]

MASTER_DATA_RELATIONSHIP_RULES = {
    "REGIONS_BASIC": [
        {
            "parent_sheet_code": "REGIONS",
            "parent_field_name": "region_gid",
            "child_sheet_code": "REGION_DETAILS",
            "child_field_name": "region_gid",
        },
    ],
    "ITEMS_PACKAGING_STANDARD": [
        {
            "parent_sheet_code": "ITEMS",
            "parent_field_name": "item_gid",
            "child_sheet_code": "PACKAGING",
            "child_field_name": "item_gid",
        },
        {
            "parent_sheet_code": "PACKAGING",
            "parent_field_name": "packaged_item_gid",
            "child_sheet_code": "TI_HI",
            "child_field_name": "packaged_item_gid",
        },
    ],
}


def seed_master_data_templates(db: Session) -> None:
    changed = False
    for seed in MASTER_DATA_TEMPLATE_SEEDS:
        exists = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == seed["code"]).first()
        if exists:
            if not json.loads(exists.sheets_json):
                exists.sheets_json = json.dumps(seed["sheets"])
                changed = True
            continue
        db.add(
            MasterDataTemplate(
                code=seed["code"],
                name=seed["name"],
                version=seed["version"],
                status=seed["status"],
                catalog_macro_object_code=seed["catalog_macro_object_code"],
                data_category=seed["data_category"],
                target_tables_json=json.dumps(seed["target_tables"]),
                sheets_json=json.dumps(seed["sheets"]),
                description=seed["description"],
            )
        )
        changed = True
    if changed:
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


def validate_master_data_batch_relationships(
    db: Session,
    batch: MasterDataBatch,
) -> dict[str, object]:
    if batch.status != "PARSED":
        raise ValueError("Only parsed Master Data batches can be relationship-validated.")

    parsed_rows = json.loads(batch.parsed_rows_json)
    issues = []
    for rule in MASTER_DATA_RELATIONSHIP_RULES.get(batch.template_code, []):
        parent_values = {
            row.get(rule["parent_field_name"])
            for row in parsed_rows.get(rule["parent_sheet_code"], [])
            if row.get(rule["parent_field_name"]) not in {None, ""}
        }
        for row_index, child_row in enumerate(parsed_rows.get(rule["child_sheet_code"], []), start=2):
            child_value = child_row.get(rule["child_field_name"])
            if child_value in {None, ""} or child_value in parent_values:
                continue
            issues.append(
                {
                    "code": "MASTER_DATA_RELATIONSHIP_ORPHAN",
                    "severity": "ERROR",
                    "sheet_code": rule["child_sheet_code"],
                    "field_name": rule["child_field_name"],
                    "row_number": row_index,
                    "message": "Child row references a parent key that does not exist in the same batch.",
                    "parent_sheet_code": rule["parent_sheet_code"],
                    "parent_field_name": rule["parent_field_name"],
                    "missing_value": child_value,
                }
            )

    batch.status = "RELATIONSHIP_FAILED" if issues else "RELATIONSHIP_VALIDATED"
    batch.issues_json = json.dumps(issues, sort_keys=True)
    batch.issue_count = len(issues)
    db.commit()

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "issue_count": batch.issue_count,
        "issues": issues,
    }


def map_master_data_batch_to_canonical_records(
    db: Session,
    template: MasterDataTemplate,
    batch: MasterDataBatch,
) -> dict[str, object]:
    if MASTER_DATA_RELATIONSHIP_RULES.get(batch.template_code):
        if batch.status != "RELATIONSHIP_VALIDATED":
            raise ValueError(
                "Master Data batch must be relationship-validated before mapping."
            )
    elif batch.status != "PARSED":
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


def build_master_data_csv_files(
    db: Session,
    batch: MasterDataBatch,
    dictionary_root: Path,
) -> dict[str, object]:
    if batch.status != "OUTPUT_BUILT":
        raise ValueError("Only output-built Master Data batches can build CSV files.")

    db.query(MasterDataCsvFile).filter(MasterDataCsvFile.batch_id == batch.id).delete()
    output_records = (
        db.query(MasterDataOutputRecord)
        .filter(MasterDataOutputRecord.batch_id == batch.id)
        .order_by(MasterDataOutputRecord.created_at, MasterDataOutputRecord.record_index)
        .all()
    )
    records_by_table: dict[str, list[dict[str, object]]] = {}
    for output_record in output_records:
        records_by_table.setdefault(output_record.target_table, []).append(
            json.loads(output_record.payload_json)
        )

    response_files = []
    for index, table_name in enumerate(records_by_table, start=1):
        rows = records_by_table[table_name]
        columns = sorted({column for row in rows for column in row})
        content = build_otm_csv_preview(dictionary_root, table_name, columns, rows)
        file_name = f"{index:03d}_{table_name}.csv"
        csv_file = MasterDataCsvFile(
            batch_id=batch.id,
            template_code=batch.template_code,
            table_name=table_name,
            file_name=file_name,
            row_count=len(rows),
            content=content,
        )
        db.add(csv_file)
        response_files.append(
            {
                "table_name": table_name,
                "file_name": file_name,
                "row_count": len(rows),
                "content": content,
            }
        )

    batch.status = "CSV_BUILT"
    db.commit()

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "csv_file_count": len(response_files),
        "files": response_files,
    }


def export_master_data_csv_package(
    db: Session,
    batch: MasterDataBatch,
    artifact_root: Path,
    generated_by: str,
) -> dict[str, object]:
    if batch.status != "CSV_BUILT":
        raise ValueError("Only CSV-built Master Data batches can be exported.")

    csv_files = (
        db.query(MasterDataCsvFile)
        .filter(MasterDataCsvFile.batch_id == batch.id)
        .order_by(MasterDataCsvFile.file_name)
        .all()
    )
    if not csv_files:
        raise ValueError("Master Data batch has no CSV files to export.")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    export_dir = artifact_root / "master_data" / batch.id / "csv_exports" / timestamp
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"master_data_batch_{batch.id}.zip"

    manifest_files = [
        {
            "table_name": csv_file.table_name,
            "file_name": csv_file.file_name,
            "row_count": csv_file.row_count,
            "size_bytes": len(csv_file.content.encode("utf-8")),
        }
        for csv_file in csv_files
    ]
    manifest_payload = {
        "schema_version": "master-data-csv-export-manifest/v1",
        "manifest_type": "master_data_csv_export",
        "source_module": "master_data",
        "source_entity_type": "master_data_batch",
        "source_entity_id": batch.id,
        "batch": {
            "id": batch.id,
            "template_code": batch.template_code,
            "status": "EXPORTED",
            "row_count": batch.row_count,
            "issue_count": batch.issue_count,
        },
        "files": manifest_files,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "generated_by": generated_by,
    }
    manifest_text = json.dumps(manifest_payload, indent=2, sort_keys=True)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest_text)
        for csv_file in csv_files:
            archive.writestr(f"csv/{csv_file.file_name}", csv_file.content)

    zip_hash, zip_size = file_sha256(str(zip_path))
    artifact = Artifact(
        source_module="master_data",
        artifact_type="master_data_csv_zip",
        file_path=str(zip_path),
        file_name=zip_path.name,
        content_type="application/zip",
        sha256=zip_hash,
        size_bytes=zip_size,
        sensitivity_level="client_safe",
    )
    db.add(artifact)
    db.flush()

    manifest = Manifest(
        source_module="master_data",
        status="CREATED",
        manifest_json=manifest_text,
    )
    db.add(manifest)
    db.flush()

    evidence_summary = {
        "source_entity_type": "master_data_batch",
        "source_entity_id": batch.id,
        "template_code": batch.template_code,
        "table_count": len(csv_files),
        "row_count": sum(csv_file.row_count for csv_file in csv_files),
        "artifact_type": "master_data_csv_zip",
    }
    evidence = Evidence(
        source_module="master_data",
        evidence_type="master_data_csv_export",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        artifact_id=artifact.id,
        manifest_id=manifest.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    audit = AuditLog(
        actor_user_id=generated_by,
        action="master_data.batch.export_csv",
        target_type="master_data_batch",
        target_id=batch.id,
        metadata_json=json.dumps(
            {
                "artifact_id": artifact.id,
                "manifest_id": manifest.id,
                "evidence_id": evidence.id,
                "table_count": len(csv_files),
            },
            sort_keys=True,
        ),
    )
    db.add(audit)

    batch.status = "EXPORTED"
    db.commit()

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "artifact_id": artifact.id,
        "manifest_id": manifest.id,
        "evidence_id": evidence.id,
        "file_name": artifact.file_name,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "tables": [csv_file.table_name for csv_file in csv_files],
    }
