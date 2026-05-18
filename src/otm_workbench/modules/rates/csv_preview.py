from pathlib import Path

from otm_workbench.modules.rates.dictionary import load_table_definition


DATE_FORMAT_DIRECTIVE = "exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'"


def serialize_value(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    if "," in text or "\n" in text or '"' in text:
        return '"' + text.replace('"', '""') + '"'
    return text


def normalize_rows_for_otm_csv(
    dictionary_root: Path,
    table_name: str,
    columns: list[str],
    rows: list[dict[str, object]],
) -> tuple[list[str], list[dict[str, object]]]:
    definition = load_table_definition(dictionary_root, table_name)
    normalized_table = definition.table_name
    normalized_columns = [column.upper() for column in columns]
    normalized_rows = [
        {str(key).upper(): value for key, value in row.items()}
        for row in rows
    ]

    if normalized_table == "RATE_GEO":
        normalized_columns = [
            column for column in normalized_columns if column != "RATE_GEO_SEQ"
        ]
        for row in normalized_rows:
            row.pop("RATE_GEO_SEQ", None)

    if normalized_table == "RATE_GEO_COST_GROUP":
        if "RATE_GEO_COST_GROUP_SEQ" not in normalized_columns:
            normalized_columns.append("RATE_GEO_COST_GROUP_SEQ")
        for row in normalized_rows:
            row.setdefault("RATE_GEO_COST_GROUP_SEQ", 1)

    if normalized_table == "RATE_GEO_COST":
        if "RATE_GEO_COST_SEQ" not in normalized_columns:
            insert_at = (
                1
                if normalized_columns and normalized_columns[0] == "RATE_GEO_COST_GROUP_GID"
                else len(normalized_columns)
            )
            normalized_columns.insert(insert_at, "RATE_GEO_COST_SEQ")
        counters: dict[str, int] = {}
        should_blank_charge_amount_base = (
            "CHARGE_AMOUNT_BASE" in normalized_columns
            or any("CHARGE_AMOUNT_BASE" in row for row in normalized_rows)
        )
        for row in normalized_rows:
            group_gid = str(row.get("RATE_GEO_COST_GROUP_GID", ""))
            counters[group_gid] = counters.get(group_gid, 0) + 1
            row.setdefault("RATE_GEO_COST_SEQ", counters[group_gid])
            if should_blank_charge_amount_base:
                row["CHARGE_AMOUNT_BASE"] = None
        if should_blank_charge_amount_base and "CHARGE_AMOUNT_BASE" not in normalized_columns:
            normalized_columns.append("CHARGE_AMOUNT_BASE")

    missing = [column for column in normalized_columns if column not in definition.columns]
    if missing:
        raise ValueError(
            "Columns do not exist in OTM Data Dictionary for "
            f"{definition.table_name}: {', '.join(missing)}"
        )
    return normalized_columns, normalized_rows


def build_otm_csv_preview(
    dictionary_root: Path,
    table_name: str,
    columns: list[str],
    rows: list[dict[str, object]],
) -> str:
    definition = load_table_definition(dictionary_root, table_name)
    normalized_columns, normalized_rows = normalize_rows_for_otm_csv(
        dictionary_root,
        table_name,
        columns,
        rows,
    )
    lines = [definition.table_name, ",".join(normalized_columns)]
    if any(column in definition.date_columns for column in normalized_columns):
        lines.append(DATE_FORMAT_DIRECTIVE)
    for row in normalized_rows:
        values = [
            serialize_value(row.get(column, row.get(column.lower(), "")))
            for column in normalized_columns
        ]
        lines.append(",".join(values))
    return "\n".join(lines)
