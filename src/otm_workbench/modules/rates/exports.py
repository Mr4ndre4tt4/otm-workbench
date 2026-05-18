from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import RateBatch, RateBatchIssue, RateBatchTable


@dataclass(frozen=True)
class RatesCsvExportResult:
    batch_id: str
    status: str
    artifact_id: str
    manifest_id: str
    evidence_id: str
    file_name: str
    file_path: str
    sha256: str
    size_bytes: int
    tables: list[str]


def ensure_exportable_batch(db: Session, batch: RateBatch) -> None:
    if batch.status not in {"VALIDATED", "EXPORT_PREVIEWED"}:
        raise ValueError("Rate batch must be validated before CSV export.")
    error_count = (
        db.query(RateBatchIssue)
        .filter(RateBatchIssue.batch_id == batch.id, RateBatchIssue.severity == "ERROR")
        .count()
    )
    if error_count:
        raise ValueError("Rate batch has ERROR issues and cannot be exported.")
    table_count = db.query(RateBatchTable).filter(RateBatchTable.batch_id == batch.id).count()
    if table_count == 0:
        raise ValueError("Rate batch has no tables to export.")
