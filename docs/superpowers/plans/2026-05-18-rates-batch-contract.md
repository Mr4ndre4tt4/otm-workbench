# Rates Batch Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the backend/DB/API contract for persisted Rates batches, scenario validation, Data Dictionary-backed row checks, issue tracking, and technical CSV previews.

**Architecture:** Extend the existing `modules/rates` package with focused services for scenarios, batches, validation, and batch CSV preview. Store flexible row payloads as JSON while keeping scenario, table, row, and issue metadata relational and queryable.

**Tech Stack:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic, SQLite, pytest, Ruff.

---

## File Structure

- Modify `src/otm_workbench/models.py`: add `RateBatch`, `RateBatchTable`, `RateBatchRow`, and `RateBatchIssue`.
- Create `migrations/versions/<revision>_rates_batch_contract.py`: create batch tables and indexes.
- Create `src/otm_workbench/modules/rates/scenarios.py`: define scenario contracts and template responses.
- Create `src/otm_workbench/modules/rates/batches.py`: create/list/get batches, add tables and rows, normalize persisted entities.
- Create `src/otm_workbench/modules/rates/validation.py`: validate scenarios, dictionary tables/columns, sequence dependencies, and technical column rules.
- Modify `src/otm_workbench/modules/rates/csv_preview.py`: add normalization support for special technical columns without changing the existing table preview contract.
- Modify `src/otm_workbench/modules/rates/routes.py`: expose templates, batch CRUD-lite, validation, issues, and batch CSV preview endpoints.
- Create `tests/test_rates_batch_scenarios.py`: scenario/template tests.
- Create `tests/test_rates_batches.py`: persistence and API tests.
- Create `tests/test_rates_batch_validation.py`: validation and issue tests.
- Create `tests/test_rates_batch_csv_preview.py`: persisted batch CSV preview tests.
- Modify `README.md`: add a short backend verification note for Rates Batch Contract.

---

## Task 1: Database Models And Migration

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `migrations/versions/<revision>_rates_batch_contract.py`
- Test: `tests/test_rates_batches.py`

- [ ] **Step 1: Write failing model persistence test**

Create `tests/test_rates_batches.py` with:

```python
from otm_workbench.models import RateBatch, RateBatchIssue, RateBatchRow, RateBatchTable


def test_rate_batch_models_persist(db_session):
    batch = RateBatch(
        project_id="project_otm1",
        environment_id="uat",
        profile_id="profile_otm1",
        scenario_code="RATE_GEO_ONLY",
        name="Synthetic rate geo batch",
        domain_name="OTM1",
        source_type="api",
        created_by="codex",
    )
    db_session.add(batch)
    db_session.flush()

    table = RateBatchTable(
        batch_id=batch.id,
        table_name="RATE_GEO",
        sequence_index=4,
        requirement_level="REQUIRED",
        row_count=1,
        status="PENDING",
    )
    db_session.add(table)
    db_session.flush()

    row = RateBatchRow(
        batch_id=batch.id,
        batch_table_id=table.id,
        table_name="RATE_GEO",
        row_index=1,
        row_payload_json='{"RATE_GEO_GID": "OTM1.RG_DEMO_001"}',
        normalized_payload_json='{"RATE_GEO_GID": "OTM1.RG_DEMO_001"}',
        row_hash="hash",
        status="PENDING",
    )
    db_session.add(row)
    db_session.flush()

    issue = RateBatchIssue(
        batch_id=batch.id,
        batch_table_id=table.id,
        batch_row_id=row.id,
        severity="INFO",
        issue_code="ROW_ACCEPTED",
        table_name="RATE_GEO",
        column_name="RATE_GEO_GID",
        message="Row accepted.",
        details_json="{}",
    )
    db_session.add(issue)
    db_session.commit()

    assert db_session.query(RateBatch).count() == 1
    assert db_session.query(RateBatchTable).count() == 1
    assert db_session.query(RateBatchRow).count() == 1
    assert db_session.query(RateBatchIssue).count() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_rates_batches.py::test_rate_batch_models_persist -q
```

Expected: FAIL with import/name error for the new models.

- [ ] **Step 3: Add SQLAlchemy models**

Append these classes to `src/otm_workbench/models.py`:

```python
class RateBatch(Base, TimestampMixin):
    __tablename__ = "rate_batches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    scenario_code: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String, default="DRAFT", index=True)
    source_type: Mapped[str] = mapped_column(String, default="api")
    domain_name: Mapped[str] = mapped_column(String, index=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    exported_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")


class RateBatchTable(Base, TimestampMixin):
    __tablename__ = "rate_batch_tables"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("rate_batches.id"), index=True)
    table_name: Mapped[str] = mapped_column(String, index=True)
    sequence_index: Mapped[int] = mapped_column(Integer)
    requirement_level: Mapped[str] = mapped_column(String, default="OPTIONAL")
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="PENDING", index=True)


class RateBatchRow(Base, TimestampMixin):
    __tablename__ = "rate_batch_rows"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("rate_batches.id"), index=True)
    batch_table_id: Mapped[str] = mapped_column(ForeignKey("rate_batch_tables.id"), index=True)
    table_name: Mapped[str] = mapped_column(String, index=True)
    row_index: Mapped[int] = mapped_column(Integer)
    row_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    normalized_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    row_hash: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="PENDING", index=True)


class RateBatchIssue(Base):
    __tablename__ = "rate_batch_issues"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("rate_batches.id"), index=True)
    batch_table_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    batch_row_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String, index=True)
    issue_code: Mapped[str] = mapped_column(String, index=True)
    table_name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    column_name: Mapped[str | None] = mapped_column(String, nullable=True)
    message: Mapped[str] = mapped_column(Text)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
```

- [ ] **Step 4: Add Alembic migration**

Generate a revision:

```bash
python -m alembic revision -m "rates batch contract"
```

Edit the generated migration to create/drop `rate_batches`, `rate_batch_tables`, `rate_batch_rows`, and `rate_batch_issues` with columns matching the models.

- [ ] **Step 5: Run persistence test and migration**

Run:

```bash
python -m pytest tests/test_rates_batches.py::test_rate_batch_models_persist -q
python -m alembic upgrade head
```

Expected: both pass.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/models.py migrations/versions tests/test_rates_batches.py
git commit -m "feat: add rates batch schema"
```

---

## Task 2: Scenario Templates

**Files:**
- Create: `src/otm_workbench/modules/rates/scenarios.py`
- Modify: `src/otm_workbench/modules/rates/routes.py`
- Test: `tests/test_rates_batch_scenarios.py`

- [ ] **Step 1: Write failing scenario tests**

Create `tests/test_rates_batch_scenarios.py`:

```python
from otm_workbench.modules.rates.scenarios import get_rate_scenario, list_rate_scenarios


def test_rate_scenarios_include_initial_three_contracts():
    scenarios = list_rate_scenarios()

    assert [item.code for item in scenarios] == [
        "COMPLETE_TARIFF",
        "RATE_GEO_ONLY",
        "ACCESSORIAL_ONLY",
    ]


def test_rate_geo_only_required_tables_are_explicit():
    scenario = get_rate_scenario("RATE_GEO_ONLY")

    assert scenario.required_tables == [
        "X_LANE",
        "RATE_GEO",
        "RATE_GEO_COST_GROUP",
        "RATE_GEO_COST",
    ]
    assert "RATE_OFFERING" in scenario.pre_existing_tables


def test_rates_templates_api_returns_scenarios(client, admin_header):
    response = client.get("/api/v1/modules/rates/templates", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["items"][0]["code"] == "COMPLETE_TARIFF"
```

- [ ] **Step 2: Run tests to verify failure**

```bash
python -m pytest tests/test_rates_batch_scenarios.py -q
```

Expected: FAIL because `scenarios.py` and `/templates` do not exist.

- [ ] **Step 3: Implement scenario module**

Create `src/otm_workbench/modules/rates/scenarios.py`:

```python
from dataclasses import dataclass

from otm_workbench.modules.rates.dictionary import RATES_LOAD_SEQUENCE


@dataclass(frozen=True)
class RateScenario:
    code: str
    name: str
    description: str
    tables: list[str]
    required_tables: list[str]
    optional_tables: list[str]
    pre_existing_tables: list[str]


SCENARIOS = [
    RateScenario(
        code="COMPLETE_TARIFF",
        name="Complete tariff",
        description="Rate offering plus rate geo, accessorial, and cost tables.",
        tables=RATES_LOAD_SEQUENCE,
        required_tables=["X_LANE", "RATE_GEO", "RATE_GEO_COST_GROUP", "RATE_GEO_COST"],
        optional_tables=[
            "RATE_OFFERING",
            "RATE_UNIT_BREAK_PROFILE",
            "RATE_UNIT_BREAK",
            "ACCESSORIAL_CODE",
            "ACCESSORIAL_COST",
            "ACCESSORIAL_COST_UNIT_BREAK",
            "RATE_OFFERING_ACCESSORIAL",
            "RATE_GEO_ACCESSORIAL",
            "RATE_GEO_STOPS",
        ],
        pre_existing_tables=[],
    ),
    RateScenario(
        code="RATE_GEO_ONLY",
        name="Rate geo only",
        description="Rate records and costs when the offering exists or is handled separately.",
        tables=[
            "X_LANE",
            "RATE_GEO",
            "ACCESSORIAL_COST",
            "RATE_GEO_ACCESSORIAL",
            "RATE_GEO_COST_GROUP",
            "RATE_GEO_COST",
        ],
        required_tables=["X_LANE", "RATE_GEO", "RATE_GEO_COST_GROUP", "RATE_GEO_COST"],
        optional_tables=["ACCESSORIAL_COST", "RATE_GEO_ACCESSORIAL"],
        pre_existing_tables=["RATE_OFFERING"],
    ),
    RateScenario(
        code="ACCESSORIAL_ONLY",
        name="Accessorial only",
        description="Accessorial costs and relationships without a full rate geo package.",
        tables=["ACCESSORIAL_COST", "RATE_OFFERING_ACCESSORIAL", "RATE_GEO_ACCESSORIAL"],
        required_tables=["ACCESSORIAL_COST"],
        optional_tables=["RATE_OFFERING_ACCESSORIAL", "RATE_GEO_ACCESSORIAL"],
        pre_existing_tables=["RATE_OFFERING", "RATE_GEO", "ACCESSORIAL_CODE"],
    ),
]


def list_rate_scenarios() -> list[RateScenario]:
    return SCENARIOS


def get_rate_scenario(code: str) -> RateScenario:
    normalized = code.upper()
    for scenario in SCENARIOS:
        if scenario.code == normalized:
            return scenario
    raise ValueError(f"Unsupported rates scenario: {code}")


def requirement_for_table(scenario: RateScenario, table_name: str) -> str:
    table = table_name.upper()
    if table in scenario.required_tables:
        return "REQUIRED"
    if table in scenario.optional_tables:
        return "OPTIONAL"
    if table in scenario.pre_existing_tables:
        return "PRE_EXISTING"
    return "UNSUPPORTED"
```

- [ ] **Step 4: Add templates route**

In `src/otm_workbench/modules/rates/routes.py`, import `list_rate_scenarios` and add:

```python
@router.get("/templates")
def list_rates_templates(user: User = Depends(require_user)):
    items = [
        {
            "code": scenario.code,
            "name": scenario.name,
            "description": scenario.description,
            "tables": scenario.tables,
            "required_tables": scenario.required_tables,
            "optional_tables": scenario.optional_tables,
            "pre_existing_tables": scenario.pre_existing_tables,
        }
        for scenario in list_rate_scenarios()
    ]
    return PageResponse(items=items, total=len(items))
```

- [ ] **Step 5: Run scenario tests**

```bash
python -m pytest tests/test_rates_batch_scenarios.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/modules/rates/scenarios.py src/otm_workbench/modules/rates/routes.py tests/test_rates_batch_scenarios.py
git commit -m "feat: add rates batch scenario templates"
```

---

## Task 3: Batch Creation And Table Ingestion

**Files:**
- Create: `src/otm_workbench/modules/rates/batches.py`
- Modify: `src/otm_workbench/modules/rates/routes.py`
- Test: `tests/test_rates_batches.py`

- [ ] **Step 1: Add failing API tests**

Append to `tests/test_rates_batches.py`:

```python
def test_create_rate_batch_api(client, admin_header):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": "RATE_GEO_ONLY",
            "name": "Synthetic rate geo package",
            "domain_name": "OTM1",
            "project_id": "project_otm1",
            "environment_id": "uat",
            "profile_id": "profile_otm1",
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_code"] == "RATE_GEO_ONLY"
    assert payload["status"] == "DRAFT"
    assert payload["domain_name"] == "OTM1"


def test_add_rate_batch_tables_api_sorts_by_rates_sequence(client, admin_header):
    created = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": "RATE_GEO_ONLY",
            "name": "Synthetic rate geo package",
            "domain_name": "OTM1",
        },
        headers=admin_header,
    ).json()

    response = client.post(
        f"/api/v1/modules/rates/batches/{created['id']}/tables",
        json={
            "tables": [
                {
                    "table_name": "RATE_GEO_COST",
                    "rows": [
                        {
                            "RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_001",
                            "CHARGE_AMOUNT": 10,
                        }
                    ],
                },
                {
                    "table_name": "X_LANE",
                    "rows": [{"X_LANE_GID": "OTM1.RG_001", "X_LANE_XID": "RG_001"}],
                },
            ]
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    assert [item["table_name"] for item in response.json()["tables"]] == ["X_LANE", "RATE_GEO_COST"]
```

- [ ] **Step 2: Run tests to verify failure**

```bash
python -m pytest tests/test_rates_batches.py::test_create_rate_batch_api tests/test_rates_batches.py::test_add_rate_batch_tables_api_sorts_by_rates_sequence -q
```

Expected: FAIL with 404.

- [ ] **Step 3: Implement batch service**

Create `src/otm_workbench/modules/rates/batches.py` with functions:

```python
import hashlib
import json

from sqlalchemy.orm import Session

from otm_workbench.models import RateBatch, RateBatchRow, RateBatchTable
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
    created_by: str | None = None,
) -> RateBatch:
    scenario = get_rate_scenario(scenario_code)
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
            normalized_payload = {str(key).upper(): value for key, value in dict(row_payload).items()}
            db.add(
                RateBatchRow(
                    batch_id=batch.id,
                    batch_table_id=batch_table.id,
                    table_name=table_name,
                    row_index=index,
                    row_payload_json=json.dumps(row_payload, sort_keys=True),
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
```

- [ ] **Step 4: Add Pydantic models and routes**

In `routes.py`, add request/response helpers for batch creation and table ingestion. Keep them local to `routes.py` for this slice.

Required endpoints:

```python
@router.post("/batches")
def create_rates_batch(...)

@router.get("/batches")
def list_rates_batches(...)

@router.get("/batches/{batch_id}")
def get_rates_batch(...)

@router.post("/batches/{batch_id}/tables")
def add_rates_batch_tables(...)
```

Responses must include `id`, `scenario_code`, `name`, `domain_name`, `status`, and table summaries.

- [ ] **Step 5: Run batch API tests**

```bash
python -m pytest tests/test_rates_batches.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/modules/rates/batches.py src/otm_workbench/modules/rates/routes.py tests/test_rates_batches.py
git commit -m "feat: add rates batch APIs"
```

---

## Task 4: Validation And Issue Tracking

**Files:**
- Create: `src/otm_workbench/modules/rates/validation.py`
- Modify: `src/otm_workbench/modules/rates/routes.py`
- Test: `tests/test_rates_batch_validation.py`

- [ ] **Step 1: Write failing validation tests**

Create `tests/test_rates_batch_validation.py`:

```python
def create_batch(client, admin_header, scenario_code="RATE_GEO_ONLY"):
    return client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic batch", "domain_name": "OTM1"},
        headers=admin_header,
    ).json()


def test_validation_errors_when_required_table_missing(client, admin_header):
    batch = create_batch(client, admin_header)
    client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables",
        json={"tables": [{"table_name": "X_LANE", "rows": [{"X_LANE_GID": "OTM1.RG_001"}]}]},
        headers=admin_header,
    )

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/validate",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert any(issue["issue_code"] == "REQUIRED_TABLE_MISSING" for issue in payload["issues"])


def test_validation_rejects_unknown_column(client, admin_header):
    batch = create_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY")
    client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables",
        json={
            "tables": [
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [{"ACCESSORIAL_COST_GID": "OTM1.ACC_COST_001", "NOT_A_COLUMN": "x"}],
                }
            ]
        },
        headers=admin_header,
    )

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/validate",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert any(issue["issue_code"] == "UNKNOWN_COLUMN" for issue in payload["issues"])


def test_batch_issues_endpoint_returns_persisted_issues(client, admin_header):
    batch = create_batch(client, admin_header)
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)

    response = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/issues",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["total"] >= 1
```

- [ ] **Step 2: Run tests to verify failure**

```bash
python -m pytest tests/test_rates_batch_validation.py -q
```

Expected: FAIL with 404 or missing validation module.

- [ ] **Step 3: Implement validation service**

Create `src/otm_workbench/modules/rates/validation.py`:

```python
import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import RateBatch, RateBatchIssue, RateBatchRow, RateBatchTable, utcnow
from otm_workbench.modules.rates.dictionary import load_table_definition, validate_load_sequence
from otm_workbench.modules.rates.scenarios import get_rate_scenario


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


def validate_rate_batch(db: Session, *, dictionary_root: Path, batch: RateBatch) -> list[RateBatchIssue]:
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
                if column.upper() not in definition.columns:
                    add_issue(
                        db,
                        batch=batch,
                        table=table,
                        row=row,
                        severity="ERROR",
                        issue_code="UNKNOWN_COLUMN",
                        column_name=column.upper(),
                        message=f"{table.table_name}.{column.upper()} does not exist in the OTM Data Dictionary.",
                    )

    sequence_result = validate_load_sequence(dictionary_root, table_names)
    for sequence_issue in sequence_result.issues:
        matching_table = next((item for item in tables if item.table_name == sequence_issue.table_name), None)
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
```

- [ ] **Step 4: Add validate and issues routes**

Add:

```python
@router.post("/batches/{batch_id}/validate")
def validate_rates_batch(...)

@router.get("/batches/{batch_id}/issues")
def list_rates_batch_issues(...)
```

The validate response must include `valid`, `batch_id`, `status`, and `issues`.

- [ ] **Step 5: Run validation tests**

```bash
python -m pytest tests/test_rates_batch_validation.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/modules/rates/validation.py src/otm_workbench/modules/rates/routes.py tests/test_rates_batch_validation.py
git commit -m "feat: validate rates batches"
```

---

## Task 5: Technical CSV Normalization

**Files:**
- Modify: `src/otm_workbench/modules/rates/csv_preview.py`
- Test: `tests/test_rates_batch_csv_preview.py`

- [ ] **Step 1: Write failing normalization tests**

Create `tests/test_rates_batch_csv_preview.py`:

```python
from pathlib import Path

from otm_workbench.modules.rates.csv_preview import normalize_rows_for_otm_csv


DATA_DICT = Path("OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict")


def test_rate_geo_seq_is_removed_from_csv_columns_and_rows():
    columns, rows = normalize_rows_for_otm_csv(
        DATA_DICT,
        "RATE_GEO",
        ["RATE_GEO_GID", "RATE_GEO_SEQ"],
        [{"RATE_GEO_GID": "OTM1.RG_001", "RATE_GEO_SEQ": 99}],
    )

    assert columns == ["RATE_GEO_GID"]
    assert rows == [{"RATE_GEO_GID": "OTM1.RG_001"}]


def test_rate_geo_cost_group_seq_defaults_to_one():
    columns, rows = normalize_rows_for_otm_csv(
        DATA_DICT,
        "RATE_GEO_COST_GROUP",
        ["RATE_GEO_COST_GROUP_GID", "RATE_GEO_GID"],
        [{"RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_001", "RATE_GEO_GID": "OTM1.RG_001"}],
    )

    assert "RATE_GEO_COST_GROUP_SEQ" in columns
    assert rows[0]["RATE_GEO_COST_GROUP_SEQ"] == 1


def test_rate_geo_cost_seq_increments_and_charge_amount_base_is_blank():
    columns, rows = normalize_rows_for_otm_csv(
        DATA_DICT,
        "RATE_GEO_COST",
        ["RATE_GEO_COST_GROUP_GID", "CHARGE_AMOUNT", "CHARGE_AMOUNT_BASE"],
        [
            {"RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_001", "CHARGE_AMOUNT": 10, "CHARGE_AMOUNT_BASE": 10},
            {"RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_001", "CHARGE_AMOUNT": 20, "CHARGE_AMOUNT_BASE": 20},
        ],
    )

    assert "RATE_GEO_COST_SEQ" in columns
    assert rows[0]["RATE_GEO_COST_SEQ"] == 1
    assert rows[1]["RATE_GEO_COST_SEQ"] == 2
    assert rows[0]["CHARGE_AMOUNT_BASE"] is None
    assert rows[1]["CHARGE_AMOUNT_BASE"] is None
```

- [ ] **Step 2: Run tests to verify failure**

```bash
python -m pytest tests/test_rates_batch_csv_preview.py -q
```

Expected: FAIL because `normalize_rows_for_otm_csv` does not exist.

- [ ] **Step 3: Implement normalization**

In `csv_preview.py`, add:

```python
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
        normalized_columns = [column for column in normalized_columns if column != "RATE_GEO_SEQ"]
        for row in normalized_rows:
            row.pop("RATE_GEO_SEQ", None)

    if normalized_table == "RATE_GEO_COST_GROUP":
        if "RATE_GEO_COST_GROUP_SEQ" not in normalized_columns:
            normalized_columns.append("RATE_GEO_COST_GROUP_SEQ")
        for row in normalized_rows:
            row.setdefault("RATE_GEO_COST_GROUP_SEQ", 1)

    if normalized_table == "RATE_GEO_COST":
        if "RATE_GEO_COST_SEQ" not in normalized_columns:
            insert_at = 1 if normalized_columns and normalized_columns[0] == "RATE_GEO_COST_GROUP_GID" else len(normalized_columns)
            normalized_columns.insert(insert_at, "RATE_GEO_COST_SEQ")
        counters: dict[str, int] = {}
        for row in normalized_rows:
            group_gid = str(row.get("RATE_GEO_COST_GROUP_GID", ""))
            counters[group_gid] = counters.get(group_gid, 0) + 1
            row.setdefault("RATE_GEO_COST_SEQ", counters[group_gid])
            if "CHARGE_AMOUNT_BASE" in normalized_columns or "CHARGE_AMOUNT_BASE" in row:
                row["CHARGE_AMOUNT_BASE"] = None
        if "CHARGE_AMOUNT_BASE" not in normalized_columns:
            normalized_columns.append("CHARGE_AMOUNT_BASE")
            for row in normalized_rows:
                row["CHARGE_AMOUNT_BASE"] = None

    missing = [column for column in normalized_columns if column not in definition.columns]
    if missing:
        raise ValueError(
            "Columns do not exist in OTM Data Dictionary for "
            f"{definition.table_name}: {', '.join(missing)}"
        )
    return normalized_columns, normalized_rows
```

- [ ] **Step 4: Update table preview to use normalization**

At the start of `build_otm_csv_preview`, call:

```python
normalized_columns, normalized_rows = normalize_rows_for_otm_csv(
    dictionary_root,
    table_name,
    columns,
    rows,
)
```

Then use `normalized_columns` and `normalized_rows` for line generation.

- [ ] **Step 5: Run CSV tests**

```bash
python -m pytest tests/test_rates_csv_preview.py tests/test_rates_batch_csv_preview.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/modules/rates/csv_preview.py tests/test_rates_batch_csv_preview.py tests/test_rates_csv_preview.py
git commit -m "feat: normalize rates csv preview columns"
```

---

## Task 6: Persisted Batch CSV Preview Endpoint

**Files:**
- Modify: `src/otm_workbench/modules/rates/batches.py`
- Modify: `src/otm_workbench/modules/rates/routes.py`
- Test: `tests/test_rates_batch_csv_preview.py`

- [ ] **Step 1: Add failing endpoint test**

Append to `tests/test_rates_batch_csv_preview.py`:

```python
def test_batch_csv_preview_endpoint_returns_table_previews(client, admin_header):
    batch = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": "ACCESSORIAL_ONLY", "name": "Synthetic accessorial", "domain_name": "OTM1"},
        headers=admin_header,
    ).json()
    client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables",
        json={
            "tables": [
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": "OTM1.ACC_COST_001",
                            "ACCESSORIAL_CODE_GID": "OTM1.ACC_FUEL",
                        }
                    ],
                }
            ]
        },
        headers=admin_header,
    )

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"] == batch["id"]
    assert payload["previews"][0]["table_name"] == "ACCESSORIAL_COST"
    assert payload["previews"][0]["content"].splitlines()[0] == "ACCESSORIAL_COST"
```

- [ ] **Step 2: Run endpoint test to verify failure**

```bash
python -m pytest tests/test_rates_batch_csv_preview.py::test_batch_csv_preview_endpoint_returns_table_previews -q
```

Expected: FAIL with 404.

- [ ] **Step 3: Implement batch preview helper**

In `batches.py`, add:

```python
def get_batch_table_rows(db: Session, batch_table: RateBatchTable) -> list[dict[str, object]]:
    rows = (
        db.query(RateBatchRow)
        .filter(RateBatchRow.batch_table_id == batch_table.id)
        .order_by(RateBatchRow.row_index)
        .all()
    )
    return [json.loads(row.normalized_payload_json or "{}") for row in rows]
```

- [ ] **Step 4: Add csv-preview route**

In `routes.py`, add:

```python
@router.post("/batches/{batch_id}/csv-preview")
def preview_rates_batch_csv(batch_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).one()
    batch_tables = (
        db.query(RateBatchTable)
        .filter(RateBatchTable.batch_id == batch.id)
        .order_by(RateBatchTable.sequence_index)
        .all()
    )
    previews = []
    for batch_table in batch_tables:
        rows = get_batch_table_rows(db, batch_table)
        columns = sorted({column for row in rows for column in row})
        content = build_otm_csv_preview(
            Path(get_settings().otm_data_dictionary_root),
            batch_table.table_name,
            columns,
            rows,
        )
        previews.append({"table_name": batch_table.table_name, "content": content})
    batch.status = "EXPORT_PREVIEWED"
    db.commit()
    return {"batch_id": batch.id, "previews": previews}
```

- [ ] **Step 5: Run batch CSV preview tests**

```bash
python -m pytest tests/test_rates_batch_csv_preview.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/modules/rates/batches.py src/otm_workbench/modules/rates/routes.py tests/test_rates_batch_csv_preview.py
git commit -m "feat: preview rates batch csv"
```

---

## Task 7: Documentation And Full Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Append to the existing Rates verification section:

```markdown
The Rates Batch Contract adds backend-only persisted batches for synthetic tariff
scenarios. It stores submitted OTM table rows, validates table and column names
against the local Data Dictionary, records batch issues, and generates technical
CSV previews using OTM table header rules.
```

- [ ] **Step 2: Run full verification**

Run serially:

```bash
python -m pytest -q
python -m alembic upgrade head
python -m ruff check src tests
```

Expected:

```text
All tests pass
Alembic upgrade succeeds
All checks passed
```

- [ ] **Step 3: Inspect git status**

```bash
git status --short --branch
```

Expected: only intended tracked changes are staged/unstaged plus local untracked `OTM_RESOURCES/`.

- [ ] **Step 4: Commit docs if needed**

```bash
git add README.md
git commit -m "docs: document rates batch contract"
```

Skip the commit if `README.md` was already included in a prior task.

---

## Self-Review

Spec coverage:

- Batch lifecycle and DB persistence: Task 1 and Task 3.
- Three scenarios and table requirements: Task 2.
- Data Dictionary validation: Task 4.
- Sequence validation: Task 4.
- Technical column handling: Task 5.
- Persisted batch CSV preview: Task 6.
- Verification/docs: Task 7.

No real client names are used. All examples use `OTM1` and synthetic IDs. XML export, final CSV export, UI, real OTM integration, and Load Plan are intentionally deferred.
