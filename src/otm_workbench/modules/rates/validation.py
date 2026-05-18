import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import RateBatch, RateBatchIssue, RateBatchRow, RateBatchTable, utcnow
from otm_workbench.modules.rates.dictionary import load_table_definition, validate_load_sequence
from otm_workbench.modules.rates.scenarios import get_rate_scenario
from otm_workbench.reference.services import ReferenceContext, validate_reference_value


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
        rows = (
            db.query(RateBatchRow)
            .filter(RateBatchRow.batch_table_id == table.id)
            .order_by(RateBatchRow.row_index)
            .all()
        )
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
