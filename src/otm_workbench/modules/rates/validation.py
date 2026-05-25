import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import RateBatch, RateBatchIssue, RateBatchRow, RateBatchTable, SchemaRoot, utcnow
from otm_workbench.modules.rates.dictionary import load_table_definition, validate_load_sequence
from otm_workbench.modules.rates.scenarios import get_rate_scenario
from otm_workbench.reference.services import ReferenceContext, validate_reference_value


def schema_root_ids_for_batch(batch: RateBatch) -> list[str]:
    try:
        parsed = json.loads(batch.schema_root_ids_json or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item).strip()]


def rate_batch_schema_validation_summary(db: Session, batch: RateBatch) -> dict[str, object] | None:
    schema_root_ids = schema_root_ids_for_batch(batch)
    if not schema_root_ids:
        return None
    checked_roots: list[str] = []
    issues: list[dict[str, str]] = []
    for schema_root_id in schema_root_ids:
        schema_root = db.get(SchemaRoot, schema_root_id)
        if schema_root is None:
            issues.append({"code": "SCHEMA_ROOT_MISSING", "schema_root_id": schema_root_id})
            continue
        checked_roots.append(schema_root.root_name)
    return {
        "status": "PASSED" if not issues else "FAILED",
        "schema_root_ids": schema_root_ids,
        "checked_roots": checked_roots,
        "issues": issues,
    }


def add_issue(
    db: Session,
    *,
    batch: RateBatch,
    severity: str,
    issue_code: str,
    message: str,
    table: RateBatchTable | None = None,
    row: RateBatchRow | None = None,
    column_name: str | None = None,
    details: dict[str, object] | None = None,
) -> RateBatchIssue:
    issue = RateBatchIssue(
        batch_id=batch.id,
        batch_table_id=table.id if table else None,
        batch_row_id=row.id if row else None,
        severity=severity,
        issue_code=issue_code,
        table_name=table.table_name if table else None,
        column_name=column_name,
        message=message,
        details_json=json.dumps(details or {}, sort_keys=True),
    )
    db.add(issue)
    return issue


def collect_batch_gid_values(
    rows_by_table: dict[str, list[RateBatchRow]],
    tables_by_id: dict[str, RateBatchTable],
) -> set[str]:
    values: set[str] = set()
    for table_id, rows in rows_by_table.items():
        table = tables_by_id[table_id]
        created_gid_column = f"{table.table_name}_GID"
        for row in rows:
            payload = json.loads(row.normalized_payload_json or "{}")
            for column, value in payload.items():
                if column.upper() == created_gid_column and value not in (None, ""):
                    values.add(str(value))
    return values


def validate_rate_batch(
    db: Session,
    *,
    dictionary_root: Path,
    batch: RateBatch,
) -> list[RateBatchIssue]:
    db.query(RateBatchIssue).filter(RateBatchIssue.batch_id == batch.id).delete()
    tables = (
        db.query(RateBatchTable)
        .filter(RateBatchTable.batch_id == batch.id)
        .order_by(RateBatchTable.sequence_index)
        .all()
    )
    table_names = [item.table_name for item in tables]
    scenario = get_rate_scenario(batch.scenario_code)
    tables_by_id = {table.id: table for table in tables}
    rows_by_table = {
        table.id: (
            db.query(RateBatchRow)
            .filter(RateBatchRow.batch_table_id == table.id)
            .order_by(RateBatchRow.row_index)
            .all()
        )
        for table in tables
    }
    batch_gid_values = collect_batch_gid_values(rows_by_table, tables_by_id)
    schema_validation = rate_batch_schema_validation_summary(db, batch)
    if schema_validation is not None:
        for schema_issue in schema_validation["issues"]:
            add_issue(
                db,
                batch=batch,
                severity="ERROR",
                issue_code="RATES_SCHEMA_ROOT_INVALID",
                message="Rate batch references a Schema Pack root that is not indexed.",
                details=schema_issue,
            )

    for required_table in scenario.required_tables:
        if required_table not in table_names:
            add_issue(
                db,
                batch=batch,
                severity="ERROR",
                issue_code="REQUIRED_TABLE_MISSING",
                message=f"{required_table} is required for {scenario.code}.",
                details={"required_table": required_table, "scenario_code": scenario.code},
            )

    for table in tables:
        if table.requirement_level == "UNSUPPORTED":
            add_issue(
                db,
                batch=batch,
                table=table,
                severity="ERROR",
                issue_code="TABLE_NOT_ALLOWED_FOR_SCENARIO",
                message=f"{table.table_name} is not allowed for {scenario.code}.",
                details={"scenario_code": scenario.code},
            )
        try:
            definition = load_table_definition(dictionary_root, table.table_name)
        except FileNotFoundError:
            add_issue(
                db,
                batch=batch,
                table=table,
                severity="ERROR",
                issue_code="UNKNOWN_TABLE",
                message=f"{table.table_name} does not exist in the OTM Data Dictionary.",
            )
            continue
        rows = rows_by_table[table.id]
        for row in rows:
            payload = json.loads(row.normalized_payload_json or "{}")
            for column in payload:
                column_name = column.upper()
                if column_name not in definition.columns:
                    add_issue(
                        db,
                        batch=batch,
                        table=table,
                        row=row,
                        severity="ERROR",
                        issue_code="UNKNOWN_COLUMN",
                        column_name=column_name,
                        message=(
                            f"{table.table_name}.{column_name} does not exist in the "
                            "OTM Data Dictionary."
                        ),
                    )
                    continue
                field_name = column_name.lower()
                reference_result = validate_reference_value(
                    db,
                    ReferenceContext(
                        project_id=batch.project_id,
                        environment_id=batch.environment_id,
                        profile_id=batch.profile_id,
                        domain_name=batch.domain_name,
                        can_view_all_domains=False,
                    ),
                    "rates",
                    field_name,
                    str(payload[column]),
                )
                if not reference_result.valid:
                    if str(payload[column]) in batch_gid_values:
                        continue
                    add_issue(
                        db,
                        batch=batch,
                        table=table,
                        row=row,
                        severity=reference_result.severity,
                        issue_code="REFERENCE_POLICY_VIOLATION",
                        column_name=column_name,
                        message=reference_result.message,
                        details={
                            "policy": reference_result.policy,
                            "object_type": reference_result.object_type,
                            "gid": reference_result.gid,
                        },
                    )

    sequence_result = validate_load_sequence(dictionary_root, table_names)
    for sequence_issue in sequence_result.issues:
        matching_table = next(
            (item for item in tables if item.table_name == sequence_issue.table_name),
            None,
        )
        add_issue(
            db,
            batch=batch,
            table=matching_table,
            severity=sequence_issue.severity,
            issue_code="SEQUENCE_DEPENDENCY",
            column_name=sequence_issue.column_name,
            message=sequence_issue.message,
            details={"parent_table_name": sequence_issue.parent_table_name},
        )

    issues = db.query(RateBatchIssue).filter(RateBatchIssue.batch_id == batch.id).all()
    has_errors = any(issue.severity == "ERROR" for issue in issues)
    batch.status = "DRAFT" if has_errors else "VALIDATED"
    batch.validated_at = utcnow()
    batch.summary_json = json.dumps(
        {
            "errors": sum(1 for issue in issues if issue.severity == "ERROR"),
            "warnings": sum(1 for issue in issues if issue.severity == "WARNING"),
            "infos": sum(1 for issue in issues if issue.severity == "INFO"),
        },
        sort_keys=True,
    )
    db.commit()
    return db.query(RateBatchIssue).filter(RateBatchIssue.batch_id == batch.id).all()
