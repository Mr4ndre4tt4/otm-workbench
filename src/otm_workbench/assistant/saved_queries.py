from pathlib import Path
import json
import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from otm_workbench.assistant.sql_helper import reject_unsafe_sql, validate_table_and_columns
from otm_workbench.models import (
    AssistantSavedQuery,
    AssistantSavedQueryColumn,
    AssistantSavedQueryTable,
    utcnow,
)


SELECT_FROM_PATTERN = re.compile(
    r"\bselect\s+(.*?)\s+from\s+([a-zA-Z0-9_]+)(?:\s+([a-zA-Z0-9_]+))?",
    re.IGNORECASE | re.DOTALL,
)
QUOTED_LITERAL_PATTERN = re.compile(r"=\s*'[^']+'")


def extract_single_table_references(sql_text: str) -> tuple[str, str, list[str]]:
    match = SELECT_FROM_PATTERN.search(sql_text)
    if not match:
        return "", "", []
    raw_columns = [item.strip() for item in match.group(1).split(",")]
    table_name = match.group(2).upper()
    alias = match.group(3) or ""
    columns = []
    for raw_column in raw_columns:
        column = raw_column.split()[0]
        if alias:
            column = column.replace(f"{alias}.", "", 1).replace(f"{alias.upper()}.", "", 1)
        columns.append(column.upper())
    return table_name, alias, columns


def create_saved_query(
    db: Session,
    *,
    name: str,
    purpose: str,
    sql_text: str,
    module_id: str | None = None,
    visibility: str = "PRIVATE",
    project_id: str | None = None,
    profile_id: str | None = None,
    environment_id: str | None = None,
    domain_name: str | None = None,
    access_policy_id: str | None = None,
    created_by: str | None = None,
) -> AssistantSavedQuery:
    table_name, alias, columns = extract_single_table_references(sql_text)
    query = AssistantSavedQuery(
        name=name.strip(),
        purpose=purpose.strip(),
        sql_text=sql_text.strip(),
        module_id=module_id,
        visibility=visibility.strip().upper(),
        project_id=project_id,
        profile_id=profile_id,
        environment_id=environment_id,
        domain_name=domain_name.upper() if domain_name else None,
        access_policy_id=access_policy_id,
        created_by=created_by,
        warnings_json="[]",
    )
    db.add(query)
    db.flush()
    if table_name:
        db.add(AssistantSavedQueryTable(query_id=query.id, table_name=table_name, alias=alias or "", role="PRIMARY"))
    for column in columns:
        db.add(
            AssistantSavedQueryColumn(
                query_id=query.id,
                table_name=table_name,
                column_name=column,
                alias=alias or "",
                role="SELECTED",
            )
        )
    db.commit()
    db.refresh(query)
    return query


def approve_saved_query(db: Session, query_id: str, *, dictionary_root: Path, reviewed_by: str) -> AssistantSavedQuery:
    query = db.get(AssistantSavedQuery, query_id)
    if query is None:
        raise ValueError("Saved query not found.")
    warnings = []
    unsafe = reject_unsafe_sql(query.sql_text)
    if unsafe:
        warnings.extend(unsafe["warnings"])
    if QUOTED_LITERAL_PATTERN.search(query.sql_text):
        warnings.append("Use bind parameters instead of quoted literals.")
    tables = db.query(AssistantSavedQueryTable).filter(AssistantSavedQueryTable.query_id == query.id).all()
    columns = db.query(AssistantSavedQueryColumn).filter(AssistantSavedQueryColumn.query_id == query.id).all()
    for table in tables:
        table_columns = [column.column_name for column in columns if column.table_name == table.table_name]
        _, table_warnings = validate_table_and_columns(dictionary_root, table.table_name, table_columns)
        warnings.extend(table_warnings)
    query.warnings_json = json.dumps(warnings, sort_keys=True)
    if warnings:
        query.status = "DRAFT"
    else:
        query.status = "APPROVED"
        query.reviewed_by = reviewed_by
        query.reviewed_at = utcnow()
    db.commit()
    db.refresh(query)
    return query


def serialize_saved_query(query: AssistantSavedQuery) -> dict[str, object]:
    return {
        "id": query.id,
        "name": query.name,
        "purpose": query.purpose,
        "module_id": query.module_id,
        "status": query.status,
        "visibility": query.visibility,
        "domain_name": query.domain_name,
        "warnings": json.loads(query.warnings_json or "[]"),
    }


def search_saved_queries(
    db: Session,
    *,
    query_text: str,
    allowed_domains: list[str],
    include_retired: bool = False,
) -> list[dict[str, object]]:
    normalized = query_text.strip().lower()
    query = db.query(AssistantSavedQuery)
    if not include_retired:
        query = query.filter(AssistantSavedQuery.status != "RETIRED")
    if "*" not in allowed_domains:
        query = query.filter(
            or_(
                AssistantSavedQuery.visibility == "PUBLIC",
                AssistantSavedQuery.domain_name.in_([domain.upper() for domain in allowed_domains]),
            )
        )
    rows = query.order_by(AssistantSavedQuery.updated_at.desc()).all()
    items = []
    for row in rows:
        haystack = f"{row.name} {row.purpose} {row.sql_text} {row.module_id or ''}".lower()
        if normalized and normalized not in haystack:
            continue
        if row.status != "APPROVED":
            continue
        items.append(serialize_saved_query(row))
    return items
