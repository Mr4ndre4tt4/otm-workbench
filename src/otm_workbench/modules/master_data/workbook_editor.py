from otm_workbench.models import MasterDataTemplate
from otm_workbench.modules.master_data.templates import master_data_template_definition


def _string_value(value: object) -> str:
    return "" if value is None else str(value).strip()


def build_master_data_workbook_editor_contract(template: MasterDataTemplate) -> dict[str, object]:
    definition = master_data_template_definition(template)
    fields_by_key = {str(field["field_key"]): field for field in definition.get("fields", [])}
    mappings_by_sheet: dict[str, list[dict[str, object]]] = {}
    for mapping in definition.get("mappings", []):
        sheet_code = str(mapping.get("sheet_code") or "")
        if not sheet_code and mapping.get("source_field_key"):
            field = fields_by_key.get(str(mapping["source_field_key"]))
            sheet_code = str(field.get("sheet_code") or "") if field else ""
        if sheet_code:
            mappings_by_sheet.setdefault(sheet_code, []).append(mapping)

    sheets = []
    for sheet in definition.get("sheets", []):
        sheet_code = str(sheet["code"])
        field_keys = [str(field_key) for field_key in sheet.get("field_keys", [])]
        sheet_fields = []
        for field_key in field_keys:
            field = fields_by_key[field_key]
            sheet_fields.append(
                {
                    "field_key": field_key,
                    "label": field["label"],
                    "data_type": field.get("data_type", "string"),
                    "required": bool(field.get("required", False)),
                }
            )
        target_table = next(
            (
                str(mapping["target_table"])
                for mapping in mappings_by_sheet.get(sheet_code, [])
                if mapping.get("target_table")
            ),
            "",
        )
        sheets.append(
            {
                "code": sheet_code,
                "name": sheet["name"],
                "target_table": target_table,
                "fields": sheet_fields,
                "starter_rows": [
                    {
                        "row_id": f"{sheet_code}-1",
                        "values": {field_key: "" for field_key in field_keys},
                    }
                ],
            }
        )

    return {
        "template_code": template.code,
        "template_name": template.name,
        "version": template.version,
        "sheets": sheets,
        "relationship_rules": definition.get("relationship_rules", []),
        "documentation_refs": definition.get("documentation_refs", []),
    }


def validate_master_data_workbook_rows(template: MasterDataTemplate, payload: dict[str, object]) -> dict[str, object]:
    definition = master_data_template_definition(template)
    fields_by_key = {str(field["field_key"]): field for field in definition.get("fields", [])}
    sheets_by_code = {str(sheet["code"]): sheet for sheet in definition.get("sheets", [])}
    issues: list[dict[str, object]] = []
    normalized_rows: dict[str, list[dict[str, object]]] = {sheet_code: [] for sheet_code in sheets_by_code}

    for sheet_payload in payload.get("sheets", []):
        sheet_code = str(sheet_payload.get("sheet_code", "")).strip().upper()
        if sheet_code not in sheets_by_code:
            issues.append(
                {
                    "code": "UNKNOWN_SHEET",
                    "message": f"Sheet {sheet_code or '<blank>'} is not defined by template {template.code}.",
                    "severity": "ERROR",
                    "sheet_code": sheet_code,
                }
            )
            continue

        sheet = sheets_by_code[sheet_code]
        for index, row_payload in enumerate(sheet_payload.get("rows", []), start=1):
            values = dict(row_payload.get("values", {}))
            if not values:
                continue
            row_id = str(row_payload.get("row_id") or f"{sheet_code}-{index}")
            normalized_rows[sheet_code].append({"row_id": row_id, "values": values})
            for field_key in sheet.get("field_keys", []):
                field = fields_by_key[str(field_key)]
                if bool(field.get("required", False)) and _string_value(values.get(str(field_key))) == "":
                    issues.append(
                        {
                            "code": "REQUIRED_FIELD_MISSING",
                            "message": f"{field['label']} is required.",
                            "severity": "ERROR",
                            "sheet_code": sheet_code,
                            "row_id": row_id,
                            "field_key": str(field_key),
                        }
                    )

    for rule in definition.get("relationship_rules", []):
        parent_sheet_code = str(rule.get("parent_sheet_code", "")).strip().upper()
        child_sheet_code = str(rule.get("child_sheet_code", "")).strip().upper()
        parent_field_key = str(rule.get("parent_field_key") or rule.get("parent_field_name") or "")
        child_field_key = str(rule.get("child_field_key") or rule.get("child_field_name") or "")
        if not parent_sheet_code or not child_sheet_code or not parent_field_key or not child_field_key:
            continue

        parent_values = {
            _string_value(parent_row["values"].get(parent_field_key))
            for parent_row in normalized_rows.get(parent_sheet_code, [])
            if _string_value(parent_row["values"].get(parent_field_key)) != ""
        }
        for child_row in normalized_rows.get(child_sheet_code, []):
            child_value = _string_value(child_row["values"].get(child_field_key))
            if child_value and child_value not in parent_values:
                issues.append(
                    {
                        "code": "RELATIONSHIP_PARENT_NOT_FOUND",
                        "message": (
                            f"{child_sheet_code}.{child_field_key} value {child_value} "
                            f"does not exist in {parent_sheet_code}.{parent_field_key}."
                        ),
                        "severity": str(rule.get("severity", "ERROR")),
                        "sheet_code": child_sheet_code,
                        "row_id": child_row["row_id"],
                        "field_key": child_field_key,
                        "parent_sheet_code": parent_sheet_code,
                        "parent_field_key": parent_field_key,
                    }
                )

    row_count = sum(len(rows) for rows in normalized_rows.values())
    return {
        "template_code": template.code,
        "valid": not issues,
        "status": "VALID" if not issues else "INVALID",
        "issues": issues,
        "summary": {
            "sheet_count": len(sheets_by_code),
            "row_count": row_count,
            "issue_count": len(issues),
        },
    }
