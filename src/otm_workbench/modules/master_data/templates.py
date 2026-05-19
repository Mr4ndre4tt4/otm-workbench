import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.catalog.services import validate_column, validate_table
from otm_workbench.models import MasterDataTemplate


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
