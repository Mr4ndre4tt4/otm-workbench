import json

from sqlalchemy.orm import Session

from otm_workbench.models import OrderReleaseBatch, OrderReleaseBatchRow, OrderReleaseTemplate
from otm_workbench.modules.order_release_generator.templates import parse_json_list


def normalize_row(raw_row: dict[str, object]) -> dict[str, str]:
    return {str(key).strip(): str(value).strip() for key, value in raw_row.items() if str(key).strip()}


def row_issues(row: dict[str, str], required_columns: list[str]) -> list[dict[str, str]]:
    issues = []
    for column in required_columns:
        if not row.get(column):
            issues.append(
                {
                    "code": "MISSING_REQUIRED_COLUMN",
                    "column": column,
                    "severity": "ERROR",
                }
            )
    return issues


def create_order_release_batch(
    db: Session,
    *,
    template: OrderReleaseTemplate,
    file_name: str,
    rows: list[dict[str, object]],
    created_by: str,
) -> OrderReleaseBatch:
    required_columns = parse_json_list(template.required_columns_json)
    normalized_rows = [normalize_row(row) for row in rows]
    row_results = [row_issues(row, required_columns) for row in normalized_rows]
    issue_count = sum(len(issues) for issues in row_results)
    release_gids = {row.get("release_gid", "") for row, issues in zip(normalized_rows, row_results, strict=True) if not issues and row.get("release_gid")}
    batch = OrderReleaseBatch(
        template_id=template.id,
        status="INVALID" if issue_count else "VALID",
        file_name=file_name.strip(),
        row_count=len(normalized_rows),
        release_count=len(release_gids),
        issue_count=issue_count,
        summary_json=json.dumps(
            {
                "template_code": template.code,
                "release_count": len(release_gids),
                "row_count": len(normalized_rows),
                "issue_count": issue_count,
            },
            sort_keys=True,
        ),
        created_by=created_by,
    )
    db.add(batch)
    db.flush()
    for index, row in enumerate(normalized_rows, start=1):
        issues = row_results[index - 1]
        db.add(
            OrderReleaseBatchRow(
                batch_id=batch.id,
                row_number=index,
                release_gid=row.get("release_gid") or None,
                status="INVALID" if issues else "VALID",
                normalized_json=json.dumps(row, sort_keys=True),
                issues_json=json.dumps(issues, sort_keys=True),
            )
        )
    db.commit()
    db.refresh(batch)
    return batch


def parse_json_object(value: str) -> dict[str, object]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def parse_json_array(value: str) -> list[dict[str, object]]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def serialize_order_release_batch(batch: OrderReleaseBatch, rows: list[OrderReleaseBatchRow] | None = None) -> dict[str, object]:
    payload = {
        "id": batch.id,
        "template_id": batch.template_id,
        "status": batch.status,
        "file_name": batch.file_name,
        "row_count": batch.row_count,
        "release_count": batch.release_count,
        "issue_count": batch.issue_count,
        "summary": parse_json_object(batch.summary_json),
        "created_by": batch.created_by,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
    }
    if rows is not None:
        payload["rows"] = [
            {
                "id": row.id,
                "batch_id": row.batch_id,
                "row_number": row.row_number,
                "release_gid": row.release_gid,
                "status": row.status,
                "normalized_json": parse_json_object(row.normalized_json),
                "issues": parse_json_array(row.issues_json),
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
            for row in rows
        ]
    return payload
