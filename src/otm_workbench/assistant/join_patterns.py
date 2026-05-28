from pathlib import Path
import json

from sqlalchemy import or_
from sqlalchemy.orm import Session

from otm_workbench.assistant.sql_helper import validate_table_and_columns
from otm_workbench.models import AssistantJoinPattern, AssistantSavedQuery, utcnow


def normalize_join_type(value: str) -> str:
    normalized = value.strip().upper()
    return normalized if normalized in {"INNER", "LEFT", "EXISTS"} else "INNER"


def create_join_pattern(
    db: Session,
    *,
    name: str,
    left_table: str,
    left_column: str,
    right_table: str,
    right_column: str,
    join_type: str = "INNER",
    business_meaning: str = "",
    module_id: str | None = None,
    source_type: str = "MANUAL",
    source_id: str | None = None,
    created_by: str | None = None,
) -> AssistantJoinPattern:
    pattern = AssistantJoinPattern(
        name=name.strip(),
        module_id=module_id,
        left_table=left_table.strip().upper(),
        left_column=left_column.strip().upper(),
        right_table=right_table.strip().upper(),
        right_column=right_column.strip().upper(),
        join_type=normalize_join_type(join_type),
        business_meaning=business_meaning.strip(),
        source_type=source_type.strip().upper(),
        source_id=source_id,
        created_by=created_by,
        warnings_json="[]",
    )
    db.add(pattern)
    db.commit()
    db.refresh(pattern)
    return pattern


def validate_join_pattern(db: Session, pattern: AssistantJoinPattern, dictionary_root: Path) -> list[str]:
    warnings = []
    _, left_warnings = validate_table_and_columns(dictionary_root, pattern.left_table, [pattern.left_column])
    _, right_warnings = validate_table_and_columns(dictionary_root, pattern.right_table, [pattern.right_column])
    warnings.extend(left_warnings)
    warnings.extend(right_warnings)
    if pattern.source_type == "SAVED_QUERY":
        saved_query = db.get(AssistantSavedQuery, pattern.source_id)
        if saved_query is None or saved_query.status != "APPROVED":
            warnings.append("Saved query source must be approved before it can validate a join pattern.")
    return warnings


def approve_join_pattern(
    db: Session,
    pattern_id: str,
    *,
    dictionary_root: Path,
    reviewed_by: str,
) -> AssistantJoinPattern:
    pattern = db.get(AssistantJoinPattern, pattern_id)
    if pattern is None:
        raise ValueError("Join pattern not found.")
    warnings = validate_join_pattern(db, pattern, dictionary_root)
    pattern.warnings_json = json.dumps(warnings, sort_keys=True)
    if warnings:
        pattern.status = "DRAFT"
        pattern.confidence = "LOW"
    else:
        pattern.status = "APPROVED"
        pattern.confidence = "HIGH"
        pattern.reviewed_by = reviewed_by
        pattern.reviewed_at = utcnow()
    db.commit()
    db.refresh(pattern)
    return pattern


def serialize_join_pattern(pattern: AssistantJoinPattern) -> dict[str, object]:
    return {
        "id": pattern.id,
        "name": pattern.name,
        "module_id": pattern.module_id,
        "left_table": pattern.left_table,
        "left_column": pattern.left_column,
        "right_table": pattern.right_table,
        "right_column": pattern.right_column,
        "join_type": pattern.join_type,
        "business_meaning": pattern.business_meaning,
        "confidence": pattern.confidence,
        "status": pattern.status,
        "source_type": pattern.source_type,
        "source_id": pattern.source_id,
        "warnings": json.loads(pattern.warnings_json or "[]"),
    }


def search_join_patterns(
    db: Session,
    *,
    query_text: str = "",
    table_name: str | None = None,
    include_draft: bool = False,
) -> list[dict[str, object]]:
    query = db.query(AssistantJoinPattern)
    if not include_draft:
        query = query.filter(AssistantJoinPattern.status == "APPROVED")
    if table_name:
        normalized_table = table_name.upper()
        query = query.filter(
            or_(AssistantJoinPattern.left_table == normalized_table, AssistantJoinPattern.right_table == normalized_table)
        )
    normalized = query_text.strip().lower()
    rows = query.order_by(AssistantJoinPattern.updated_at.desc()).all()
    items = []
    for row in rows:
        haystack = f"{row.name} {row.business_meaning} {row.left_table} {row.right_table} {row.module_id or ''}".lower()
        if normalized and normalized not in haystack:
            continue
        items.append(serialize_join_pattern(row))
    return items
