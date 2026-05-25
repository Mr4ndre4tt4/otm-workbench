from otm_workbench.models import MasterDataTemplate
from otm_workbench.modules.master_data.templates import master_data_template_definition


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
