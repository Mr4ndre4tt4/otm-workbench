import hashlib
import json

from sqlalchemy.orm import Session

from otm_workbench.models import RateBatch, RateBatchRow, RateBatchTable, SchemaRoot
from otm_workbench.modules.rates.dictionary import RATES_LOAD_SEQUENCE
from otm_workbench.modules.rates.scenarios import get_rate_scenario, requirement_for_table


def table_sequence_index(table_name: str) -> int:
    table = table_name.upper()
    if table in RATES_LOAD_SEQUENCE:
        return RATES_LOAD_SEQUENCE.index(table)
    return len(RATES_LOAD_SEQUENCE) + 100


def stable_row_hash(payload: dict[str, object]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


class UnknownRatesSchemaRoot(ValueError):
    def __init__(self, *, schema_root_id: str) -> None:
        self.schema_root_id = schema_root_id
        super().__init__("Rate batch references an unknown schema root.")


def normalize_schema_root_ids(values: list[str] | None) -> list[str]:
    if values is None:
        return []
    normalized: list[str] = []
    for value in values:
        schema_root_id = str(value).strip()
        if schema_root_id and schema_root_id not in normalized:
            normalized.append(schema_root_id)
    return normalized


def require_schema_roots(db: Session, schema_root_ids: list[str]) -> None:
    for schema_root_id in schema_root_ids:
        if db.get(SchemaRoot, schema_root_id) is None:
            raise UnknownRatesSchemaRoot(schema_root_id=schema_root_id)


def create_rate_batch(
    db: Session,
    *,
    scenario_code: str,
    name: str,
    domain_name: str,
    project_id: str | None = None,
    environment_id: str | None = None,
    profile_id: str | None = None,
    description: str = "",
    source_type: str = "api",
    schema_root_ids: list[str] | None = None,
    created_by: str | None = None,
) -> RateBatch:
    scenario = get_rate_scenario(scenario_code)
    normalized_schema_root_ids = normalize_schema_root_ids(schema_root_ids)
    require_schema_roots(db, normalized_schema_root_ids)
    batch = RateBatch(
        project_id=project_id,
        environment_id=environment_id,
        profile_id=profile_id,
        scenario_code=scenario.code,
        name=name,
        description=description,
        status="DRAFT",
        source_type=source_type,
        domain_name=domain_name.upper(),
        created_by=created_by,
        schema_root_ids_json=json.dumps(normalized_schema_root_ids),
        summary_json="{}",
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def add_rate_batch_tables(
    db: Session,
    *,
    batch: RateBatch,
    tables: list[dict[str, object]],
) -> list[RateBatchTable]:
    scenario = get_rate_scenario(batch.scenario_code)
    db.query(RateBatchRow).filter(RateBatchRow.batch_id == batch.id).delete()
    db.query(RateBatchTable).filter(RateBatchTable.batch_id == batch.id).delete()
    created_tables: list[RateBatchTable] = []
    for table_payload in sorted(tables, key=lambda item: table_sequence_index(str(item["table_name"]))):
        table_name = str(table_payload["table_name"]).upper()
        rows = list(table_payload.get("rows", []))
        batch_table = RateBatchTable(
            batch_id=batch.id,
            table_name=table_name,
            sequence_index=table_sequence_index(table_name),
            requirement_level=requirement_for_table(scenario, table_name),
            row_count=len(rows),
            status="PENDING",
        )
        db.add(batch_table)
        db.flush()
        for index, row_payload in enumerate(rows, start=1):
            source_payload = dict(row_payload)
            normalized_payload = {str(key).upper(): value for key, value in source_payload.items()}
            db.add(
                RateBatchRow(
                    batch_id=batch.id,
                    batch_table_id=batch_table.id,
                    table_name=table_name,
                    row_index=index,
                    row_payload_json=json.dumps(source_payload, sort_keys=True),
                    normalized_payload_json=json.dumps(normalized_payload, sort_keys=True),
                    row_hash=stable_row_hash(normalized_payload),
                    status="PENDING",
                )
            )
        created_tables.append(batch_table)
    db.commit()
    for item in created_tables:
        db.refresh(item)
    return created_tables


def get_batch_table_rows(db: Session, batch_table: RateBatchTable) -> list[dict[str, object]]:
    rows = (
        db.query(RateBatchRow)
        .filter(RateBatchRow.batch_table_id == batch_table.id)
        .order_by(RateBatchRow.row_index)
        .all()
    )
    return [json.loads(row.normalized_payload_json or "{}") for row in rows]
