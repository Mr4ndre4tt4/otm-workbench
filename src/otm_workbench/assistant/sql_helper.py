from pathlib import Path
import re

from sqlalchemy.orm import Session

from otm_workbench.catalog.services import safe_load_table
from otm_workbench.models import AssistantJoinPattern


UNSAFE_SQL_PATTERN = re.compile(
    r"\b(update|delete|insert|merge|drop|alter|truncate|create|grant|revoke)\b",
    re.IGNORECASE,
)


def blocked_response(summary: str, warnings: list[str]) -> dict[str, object]:
    return {
        "answer_type": "blocked",
        "summary": summary,
        "confidence": "high",
        "source_mode": "none",
        "cost_level": "local",
        "warnings": warnings,
    }


def reject_unsafe_sql(sql_text: str) -> dict[str, object] | None:
    if UNSAFE_SQL_PATTERN.search(sql_text):
        return blocked_response(
            "Only SELECT drafts are supported.",
            ["Mutation and DDL SQL are not supported by the Assistant SQL Helper."],
        )
    return None


def normalize_identifier(value: str) -> str:
    return value.strip().upper()


def parameter_name(column_name: str) -> str:
    return column_name.strip().lower()


def alias_for_table(table_name: str) -> str:
    parts = [part for part in table_name.lower().split("_") if part]
    return "".join(part[0] for part in parts)[:4] or "t"


def data_dictionary_source(table_name: str) -> dict[str, object]:
    return {
        "source_type": "data_dictionary",
        "title": table_name,
        "source_mode": "indexed",
        "confidence": "high",
    }


def join_pattern_source(pattern: AssistantJoinPattern) -> dict[str, object]:
    return {
        "source_type": "join_pattern",
        "title": pattern.name,
        "source_mode": "curated",
        "confidence": pattern.confidence.lower(),
        "id": pattern.id,
    }


def validate_table_and_columns(dictionary_root: Path, table_name: str, columns: list[str]) -> tuple[object | None, list[str]]:
    normalized_table = normalize_identifier(table_name)
    definition = safe_load_table(dictionary_root, normalized_table)
    if definition is None:
        return None, [f"{normalized_table} was not found in the local Data Dictionary."]
    warnings = []
    for column in columns:
        normalized_column = normalize_identifier(column)
        if normalized_column not in definition.columns:
            warnings.append(f"{normalized_table}.{normalized_column} was not found.")
    return definition, warnings


def draft_single_table_select(
    dictionary_root: Path,
    *,
    table_name: str,
    columns: list[str],
    filter_column: str,
    purpose: str,
) -> dict[str, object]:
    normalized_table = normalize_identifier(table_name)
    normalized_columns = [normalize_identifier(column) for column in columns]
    normalized_filter = normalize_identifier(filter_column)
    definition, warnings = validate_table_and_columns(
        dictionary_root,
        normalized_table,
        normalized_columns + [normalized_filter],
    )
    if definition is None:
        return blocked_response("Requested table was not found in the local Data Dictionary.", warnings)
    if warnings:
        return blocked_response("One or more requested columns are not in the local Data Dictionary.", warnings)
    alias = alias_for_table(normalized_table)
    selected = ", ".join(f"{alias}.{column}" for column in normalized_columns)
    bind = parameter_name(normalized_filter)
    sql = f"select {selected} from {normalized_table} {alias} where {alias}.{normalized_filter} = :{bind}"
    return {
        "answer_type": "sql_draft",
        "summary": f"Draft SELECT for {normalized_table}.",
        "confidence": "high",
        "source_mode": "generated_draft",
        "cost_level": "local",
        "block": {
            "type": "sql_draft",
            "purpose": purpose,
            "sql": sql,
            "parameters": [{"name": bind, "description": f"Filter for {normalized_table}.{normalized_filter}"}],
            "tables": [normalized_table],
            "columns": [f"{normalized_table}.{column}" for column in normalized_columns],
            "assumptions": [],
            "warnings": [],
        },
        "sources": [data_dictionary_source(normalized_table)],
    }


def draft_joined_select(
    db: Session,
    dictionary_root: Path,
    *,
    join_pattern_id: str,
    left_columns: list[str],
    right_columns: list[str],
    filter_table: str,
    filter_column: str,
    purpose: str,
) -> dict[str, object]:
    pattern = db.get(AssistantJoinPattern, join_pattern_id)
    if pattern is None:
        return blocked_response("Join pattern was not found.", ["Join pattern was not found."])
    if pattern.status != "APPROVED":
        return blocked_response(
            "Join pattern is not approved.",
            ["Join pattern must be approved before joined SQL can be drafted."],
        )
    if pattern.join_type == "EXISTS":
        return blocked_response(
            "EXISTS join draft generation is not enabled yet.",
            ["Use an INNER or LEFT join pattern for this foundation slice."],
        )

    normalized_left_columns = [normalize_identifier(column) for column in left_columns]
    normalized_right_columns = [normalize_identifier(column) for column in right_columns]
    normalized_filter_table = normalize_identifier(filter_table)
    normalized_filter_column = normalize_identifier(filter_column)
    left_validation_columns = normalized_left_columns + [pattern.left_column]
    right_validation_columns = normalized_right_columns + [pattern.right_column]
    if normalized_filter_table == pattern.left_table:
        left_validation_columns.append(normalized_filter_column)
    elif normalized_filter_table == pattern.right_table:
        right_validation_columns.append(normalized_filter_column)
    else:
        return blocked_response(
            "Filter table must be one side of the approved join pattern.",
            [f"{normalized_filter_table} is not part of join pattern {pattern.id}."],
        )

    left_definition, left_warnings = validate_table_and_columns(
        dictionary_root,
        pattern.left_table,
        left_validation_columns,
    )
    right_definition, right_warnings = validate_table_and_columns(
        dictionary_root,
        pattern.right_table,
        right_validation_columns,
    )
    warnings = left_warnings + right_warnings
    if left_definition is None or right_definition is None:
        return blocked_response("Requested table was not found in the local Data Dictionary.", warnings)
    if warnings:
        return blocked_response("One or more requested columns are not in the local Data Dictionary.", warnings)

    left_alias = alias_for_table(pattern.left_table)
    right_alias = alias_for_table(pattern.right_table)
    selected_columns = [f"{left_alias}.{column}" for column in normalized_left_columns]
    selected_columns.extend(f"{right_alias}.{column}" for column in normalized_right_columns)
    filter_alias = left_alias if normalized_filter_table == pattern.left_table else right_alias
    bind = parameter_name(normalized_filter_column)
    join_keyword = "left join" if pattern.join_type == "LEFT" else "join"
    sql = (
        f"select {', '.join(selected_columns)} "
        f"from {pattern.left_table} {left_alias} "
        f"{join_keyword} {pattern.right_table} {right_alias} "
        f"on {left_alias}.{pattern.left_column} = {right_alias}.{pattern.right_column} "
        f"where {filter_alias}.{normalized_filter_column} = :{bind}"
    )

    return {
        "answer_type": "sql_draft",
        "summary": f"Draft joined SELECT for {pattern.left_table} and {pattern.right_table}.",
        "confidence": "high",
        "source_mode": "generated_draft",
        "cost_level": "local",
        "block": {
            "type": "sql_draft",
            "purpose": purpose,
            "sql": sql,
            "parameters": [
                {
                    "name": bind,
                    "description": f"Filter for {normalized_filter_table}.{normalized_filter_column}",
                }
            ],
            "tables": [pattern.left_table, pattern.right_table],
            "columns": [f"{pattern.left_table}.{column}" for column in normalized_left_columns]
            + [f"{pattern.right_table}.{column}" for column in normalized_right_columns],
            "join_patterns": [pattern.id],
            "assumptions": ["Generated from an explicitly approved Assistant join pattern."],
            "warnings": [],
        },
        "sources": [
            data_dictionary_source(pattern.left_table),
            data_dictionary_source(pattern.right_table),
            join_pattern_source(pattern),
        ],
    }


def explain_select_sql(dictionary_root: Path, sql_text: str) -> dict[str, object]:
    unsafe = reject_unsafe_sql(sql_text)
    if unsafe:
        return unsafe
    from_match = re.search(r"\bfrom\s+([a-zA-Z0-9_]+)(?:\s+([a-zA-Z0-9_]+))?", sql_text, flags=re.IGNORECASE)
    if not from_match:
        return blocked_response("I could not identify a FROM table in the SELECT.", ["Add an explicit FROM table."])
    table_name = normalize_identifier(from_match.group(1))
    alias = from_match.group(2) or alias_for_table(table_name)
    select_match = re.search(r"\bselect\s+(.*?)\s+from\b", sql_text, flags=re.IGNORECASE | re.DOTALL)
    raw_columns = [] if not select_match else [item.strip() for item in select_match.group(1).split(",")]
    columns = []
    for raw_column in raw_columns:
        cleaned = raw_column.split()[0]
        cleaned = cleaned.replace(f"{alias}.", "", 1).replace(f"{alias.upper()}.", "", 1)
        columns.append(normalize_identifier(cleaned))
    definition, warnings = validate_table_and_columns(dictionary_root, table_name, columns)
    if definition is None:
        return blocked_response("Requested table was not found in the local Data Dictionary.", warnings)
    known_columns = [f"{table_name}.{column}" for column in columns if column in definition.columns]
    return {
        "answer_type": "sql_draft",
        "summary": f"Explained SELECT for {table_name}.",
        "confidence": "medium" if warnings else "high",
        "source_mode": "generated_draft",
        "cost_level": "local",
        "block": {
            "type": "sql_draft",
            "purpose": f"Explain SELECT against {table_name}.",
            "sql": sql_text,
            "parameters": [],
            "tables": [table_name],
            "columns": known_columns,
            "assumptions": ["Only simple single-table SELECT explanation is supported in this foundation slice."],
            "warnings": warnings,
        },
        "sources": [data_dictionary_source(table_name)],
    }
