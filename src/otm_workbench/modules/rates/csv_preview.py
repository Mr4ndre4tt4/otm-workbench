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


def build_otm_csv_preview(
    dictionary_root: Path,
    table_name: str,
    columns: list[str],
    rows: list[dict[str, object]],
) -> str:
    definition = load_table_definition(dictionary_root, table_name)
    normalized_columns = [column.upper() for column in columns]
    missing = [column for column in normalized_columns if column not in definition.columns]
    if missing:
        raise ValueError(
            "Columns do not exist in OTM Data Dictionary for "
            f"{definition.table_name}: {', '.join(missing)}"
        )
    lines = [definition.table_name, ",".join(normalized_columns)]
    if any(column in definition.date_columns for column in normalized_columns):
        lines.append(DATE_FORMAT_DIRECTIVE)
    for row in rows:
        values = [
            serialize_value(row.get(column, row.get(column.lower(), "")))
            for column in normalized_columns
        ]
        lines.append(",".join(values))
    return "\n".join(lines)
