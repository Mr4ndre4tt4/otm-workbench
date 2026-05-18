# Rates Reference Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the backend/DB foundation for the Rates Reference Catalog with OTM Data Dictionary validation, reference policies, domain-filtered options, Rate Offering suggestions, and technical CSV preview.

**Architecture:** Add a backend-only modular slice under `src/otm_workbench/reference` and `src/otm_workbench/modules/rates`, registered from the existing FastAPI app. Persistence remains in the local SQLite/SQLAlchemy monolith, with a new Alembic migration for reference catalog and OTM table metadata tables. The OTM Data Dictionary JSON files remain the source of truth for table/column/FK checks; database metadata stores only the validated subset needed by the Workbench.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, SQLite, pytest, local OTM Data Dictionary JSON.

---

## Scope Boundary

This plan does not create UI, Excel template generation, full workbook validation, final CSV/XML export, real OTM integration, Load Plan, or CSVUTIL. All tests and examples must use synthetic domains and IDs such as `PUBLIC`, `OTM1`, `OTM2`, `DEMO`, and `SANDBOX`.

## File Structure

- Modify `src/otm_workbench/config.py`: add `otm_data_dictionary_root`.
- Modify `src/otm_workbench/models.py`: add reference catalog and OTM metadata models.
- Create `src/otm_workbench/reference/__init__.py`: package marker.
- Create `src/otm_workbench/reference/policies.py`: policy constants and validation result helpers.
- Create `src/otm_workbench/reference/services.py`: reference object import, domain scoping, option lookup, and reference validation.
- Create `src/otm_workbench/reference/routes.py`: `/api/v1/reference/*` endpoints.
- Create `src/otm_workbench/modules/__init__.py`: package marker.
- Create `src/otm_workbench/modules/rates/__init__.py`: package marker.
- Create `src/otm_workbench/modules/rates/dictionary.py`: Data Dictionary JSON reader and load-sequence validator.
- Create `src/otm_workbench/modules/rates/csv_preview.py`: OTM CSV preview builder.
- Create `src/otm_workbench/modules/rates/routes.py`: `/api/v1/modules/rates/*` endpoints.
- Modify `src/otm_workbench/main.py`: include reference and rates routers.
- Create `migrations/versions/b7d4a6f1c2a9_rates_reference_catalog.py`: schema migration.
- Create `tests/test_reference_catalog.py`: catalog import/options/policies/domain tests.
- Create `tests/test_rates_dictionary.py`: Data Dictionary and sequence validation tests.
- Create `tests/test_rates_csv_preview.py`: CSV contract tests.
- Modify `README.md`: add backend verification note for Rates Reference Catalog.

## Task 1: Database Models And Migration

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `migrations/versions/b7d4a6f1c2a9_rates_reference_catalog.py`
- Test: `tests/test_reference_catalog.py`

- [ ] **Step 1: Write failing metadata tests**

Add this to `tests/test_reference_catalog.py`:

```python
from otm_workbench.database import Base


def test_reference_catalog_tables_are_registered():
    table_names = set(Base.metadata.tables)

    assert "reference_object_types" in table_names
    assert "reference_objects" in table_names
    assert "reference_field_policies" in table_names
    assert "reference_import_batches" in table_names
    assert "otm_table_definitions" in table_names
    assert "otm_table_columns" in table_names
    assert "otm_table_foreign_keys" in table_names
    assert "otm_load_sequences" in table_names
    assert "otm_csv_contracts" in table_names
```

- [ ] **Step 2: Run the failing metadata test**

Run: `python -m pytest tests/test_reference_catalog.py::test_reference_catalog_tables_are_registered -q`

Expected: FAIL because the new tables do not exist in SQLAlchemy metadata.

- [ ] **Step 3: Add SQLAlchemy models**

Append these model classes to `src/otm_workbench/models.py`:

```python
class ReferenceObjectType(Base, TimestampMixin):
    __tablename__ = "reference_object_types"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ReferenceObject(Base, TimestampMixin):
    __tablename__ = "reference_objects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    object_type: Mapped[str] = mapped_column(String, index=True)
    gid: Mapped[str] = mapped_column(String, index=True)
    xid: Mapped[str] = mapped_column(String, default="")
    domain_name: Mapped[str] = mapped_column(String, index=True)
    display_name: Mapped[str] = mapped_column(String, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    source: Mapped[str] = mapped_column(String, default="manual")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sync_batch_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class ReferenceFieldPolicy(Base, TimestampMixin):
    __tablename__ = "reference_field_policies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    module_id: Mapped[str] = mapped_column(String, index=True)
    field_name: Mapped[str] = mapped_column(String, index=True)
    object_type: Mapped[str] = mapped_column(String, index=True)
    policy: Mapped[str] = mapped_column(String)
    severity_when_missing: Mapped[str] = mapped_column(String)
    allow_manual_value: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ReferenceImportBatch(Base, TimestampMixin):
    __tablename__ = "reference_import_batches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String)
    source_description: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="PENDING")
    records_received: Mapped[int] = mapped_column(Integer, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)


class ReferenceSnapshot(Base, TimestampMixin):
    __tablename__ = "reference_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    snapshot_name: Mapped[str] = mapped_column(String)
    object_types_json: Mapped[str] = mapped_column(Text, default="[]")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    source_import_batch_id: Mapped[str | None] = mapped_column(String, nullable=True)


class ReferenceSnapshotItem(Base):
    __tablename__ = "reference_snapshot_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey("reference_snapshots.id"), index=True)
    reference_object_id: Mapped[str] = mapped_column(String, index=True)
    object_type: Mapped[str] = mapped_column(String)
    gid: Mapped[str] = mapped_column(String)
    domain_name: Mapped[str] = mapped_column(String)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class OtmTableDefinition(Base, TimestampMixin):
    __tablename__ = "otm_table_definitions"

    table_name: Mapped[str] = mapped_column(String, primary_key=True)
    schema_name: Mapped[str] = mapped_column(String, default="glogowner")
    description: Mapped[str] = mapped_column(Text, default="")
    primary_key_json: Mapped[str] = mapped_column(Text, default="[]")
    source_path: Mapped[str] = mapped_column(String, default="")


class OtmTableColumn(Base):
    __tablename__ = "otm_table_columns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    table_name: Mapped[str] = mapped_column(String, index=True)
    column_name: Mapped[str] = mapped_column(String, index=True)
    data_type: Mapped[str] = mapped_column(String)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_constraint: Mapped[bool] = mapped_column(Boolean, default=False)
    constraint_values: Mapped[str] = mapped_column(Text, default="")
    default_value: Mapped[str] = mapped_column(String, default="")


class OtmTableForeignKey(Base):
    __tablename__ = "otm_table_foreign_keys"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    table_name: Mapped[str] = mapped_column(String, index=True)
    foreign_key_name: Mapped[str] = mapped_column(String)
    column_name: Mapped[str] = mapped_column(String)
    parent_table_name: Mapped[str] = mapped_column(String, index=True)
    parent_column_name: Mapped[str] = mapped_column(String)


class OtmLoadSequence(Base, TimestampMixin):
    __tablename__ = "otm_load_sequences"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    module_id: Mapped[str] = mapped_column(String, default="rates")
    sequence_name: Mapped[str] = mapped_column(String)
    table_name: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")


class OtmCsvContract(Base, TimestampMixin):
    __tablename__ = "otm_csv_contracts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    module_id: Mapped[str] = mapped_column(String, default="rates")
    table_name: Mapped[str] = mapped_column(String, index=True)
    date_format: Mapped[str] = mapped_column(String, default="YYYY-MM-DD HH24:MI:SS")
    special_rules_json: Mapped[str] = mapped_column(Text, default="{}")
```

- [ ] **Step 4: Add Alembic migration**

Create `migrations/versions/b7d4a6f1c2a9_rates_reference_catalog.py` with matching `op.create_table` calls for the models above. Use `down_revision = "a4e08b3ed2e6"`. Add indexes for `code`, `object_type`, `gid`, `domain_name`, `project_id`, `environment_id`, `profile_id`, `table_name`, and `parent_table_name`.

- [ ] **Step 5: Run metadata and migration checks**

Run: `python -m pytest tests/test_reference_catalog.py::test_reference_catalog_tables_are_registered -q`

Expected: PASS.

Run: `python -m alembic upgrade head`

Expected: exits 0 and creates the new schema on SQLite.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/models.py migrations/versions/b7d4a6f1c2a9_rates_reference_catalog.py tests/test_reference_catalog.py
git commit -m "feat: add rates reference catalog schema"
```

## Task 2: OTM Data Dictionary Reader

**Files:**
- Modify: `src/otm_workbench/config.py`
- Create: `src/otm_workbench/modules/__init__.py`
- Create: `src/otm_workbench/modules/rates/__init__.py`
- Create: `src/otm_workbench/modules/rates/dictionary.py`
- Test: `tests/test_rates_dictionary.py`

- [ ] **Step 1: Write failing Data Dictionary tests**

Create `tests/test_rates_dictionary.py`:

```python
from pathlib import Path

from otm_workbench.modules.rates.dictionary import (
    RATES_LOAD_SEQUENCE,
    load_table_definition,
    validate_load_sequence,
)


DATA_DICT = Path("OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict")


def test_load_rate_geo_cost_definition_from_data_dictionary():
    definition = load_table_definition(DATA_DICT, "RATE_GEO_COST")

    assert definition.table_name == "RATE_GEO_COST"
    assert definition.primary_key == ["RATE_GEO_COST_GROUP_GID", "RATE_GEO_COST_SEQ"]
    assert "RATE_GEO_COST_GROUP_GID" in definition.required_columns
    assert definition.foreign_keys[0].parent_table_name == "RATE_GEO_COST_GROUP"


def test_rates_load_sequence_tables_exist_in_data_dictionary():
    result = validate_load_sequence(DATA_DICT, RATES_LOAD_SEQUENCE)

    assert result.valid is True
    assert result.missing_tables == []
    assert "RATE_GEO_COST" in result.known_tables


def test_sequence_reports_fk_dependencies_that_are_outside_sequence():
    result = validate_load_sequence(DATA_DICT, ["RATE_GEO_COST"])

    assert result.valid is False
    assert any(
        issue.table_name == "RATE_GEO_COST"
        and issue.parent_table_name == "RATE_GEO_COST_GROUP"
        for issue in result.issues
    )
```

- [ ] **Step 2: Run the failing Data Dictionary tests**

Run: `python -m pytest tests/test_rates_dictionary.py -q`

Expected: FAIL because `otm_workbench.modules.rates.dictionary` does not exist.

- [ ] **Step 3: Add config setting**

In `src/otm_workbench/config.py`, add:

```python
    otm_data_dictionary_root: Path = Path(
        "OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict"
    )
```

- [ ] **Step 4: Implement dictionary reader**

Create `src/otm_workbench/modules/rates/dictionary.py`:

```python
from dataclasses import dataclass, field
import json
from pathlib import Path


RATES_LOAD_SEQUENCE = [
    "RATE_OFFERING",
    "RATE_UNIT_BREAK_PROFILE",
    "RATE_UNIT_BREAK",
    "X_LANE",
    "RATE_GEO",
    "ACCESSORIAL_CODE",
    "ACCESSORIAL_COST",
    "ACCESSORIAL_COST_UNIT_BREAK",
    "RATE_OFFERING_ACCESSORIAL",
    "RATE_GEO_ACCESSORIAL",
    "RATE_GEO_STOPS",
    "RATE_GEO_COST_GROUP",
    "RATE_GEO_COST",
]


@dataclass(frozen=True)
class ForeignKeyColumn:
    column_name: str
    parent_table_name: str
    parent_column_name: str


@dataclass(frozen=True)
class TableDefinition:
    table_name: str
    schema_name: str
    description: str
    columns: dict[str, dict[str, object]]
    primary_key: list[str]
    required_columns: list[str]
    date_columns: list[str]
    foreign_keys: list[ForeignKeyColumn]


@dataclass(frozen=True)
class SequenceIssue:
    table_name: str
    parent_table_name: str
    column_name: str
    severity: str
    message: str


@dataclass(frozen=True)
class SequenceValidationResult:
    valid: bool
    known_tables: list[str]
    missing_tables: list[str]
    issues: list[SequenceIssue] = field(default_factory=list)


def table_path(root: Path, table_name: str) -> Path:
    return root / f"{table_name.upper()}.json"


def load_table_definition(root: Path, table_name: str) -> TableDefinition:
    path = table_path(root, table_name)
    if not path.exists():
        raise FileNotFoundError(f"OTM Data Dictionary table not found: {table_name.upper()}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    columns = {item["name"].upper(): item for item in payload.get("columns", [])}
    primary_key = [item["columnName"].upper() for item in payload.get("primaryKey", [])]
    required_columns = [
        name
        for name, item in columns.items()
        if item.get("isNull") is False
    ]
    date_columns = [
        name
        for name, item in columns.items()
        if str(item.get("dataType", "")).upper() == "DATE"
    ]
    foreign_keys: list[ForeignKeyColumn] = []
    for fk in payload.get("foreignKeys", []):
        parent = str(fk.get("parentTableName", "")).upper()
        for relation in fk.get("columnRelation", []):
            foreign_keys.append(
                ForeignKeyColumn(
                    column_name=str(relation["columnName"]).upper(),
                    parent_table_name=parent,
                    parent_column_name=str(relation["parentColumnName"]).upper(),
                )
            )
    return TableDefinition(
        table_name=str(payload["table"]["name"]).upper(),
        schema_name=str(payload["table"].get("schema", "")).upper(),
        description=str(payload["table"].get("description", "")),
        columns=columns,
        primary_key=primary_key,
        required_columns=required_columns,
        date_columns=date_columns,
        foreign_keys=foreign_keys,
    )


def validate_load_sequence(root: Path, table_names: list[str]) -> SequenceValidationResult:
    normalized = [item.upper() for item in table_names]
    known_tables: list[str] = []
    missing_tables: list[str] = []
    issues: list[SequenceIssue] = []
    positions = {table: index for index, table in enumerate(normalized)}
    for table in normalized:
        try:
            definition = load_table_definition(root, table)
        except FileNotFoundError:
            missing_tables.append(table)
            continue
        known_tables.append(table)
        for foreign_key in definition.foreign_keys:
            parent = foreign_key.parent_table_name
            if parent not in positions:
                issues.append(
                    SequenceIssue(
                        table_name=table,
                        parent_table_name=parent,
                        column_name=foreign_key.column_name,
                        severity="WARNING",
                        message=f"{table}.{foreign_key.column_name} references {parent}, which is outside this sequence.",
                    )
                )
            elif positions[parent] > positions[table]:
                issues.append(
                    SequenceIssue(
                        table_name=table,
                        parent_table_name=parent,
                        column_name=foreign_key.column_name,
                        severity="ERROR",
                        message=f"{table}.{foreign_key.column_name} references {parent}, which appears later in the sequence.",
                    )
                )
    has_errors = any(issue.severity == "ERROR" for issue in issues)
    return SequenceValidationResult(
        valid=not missing_tables and not has_errors,
        known_tables=known_tables,
        missing_tables=missing_tables,
        issues=issues,
    )
```

- [ ] **Step 5: Run Data Dictionary tests**

Run: `python -m pytest tests/test_rates_dictionary.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/config.py src/otm_workbench/modules tests/test_rates_dictionary.py
git commit -m "feat: read rates data dictionary"
```

## Task 3: Reference Policies And Domain Scope Services

**Files:**
- Create: `src/otm_workbench/reference/__init__.py`
- Create: `src/otm_workbench/reference/policies.py`
- Create: `src/otm_workbench/reference/services.py`
- Test: `tests/test_reference_catalog.py`

- [ ] **Step 1: Write failing policy and domain tests**

Append to `tests/test_reference_catalog.py`:

```python
from otm_workbench.models import ReferenceFieldPolicy, ReferenceObject
from otm_workbench.reference.services import (
    ReferenceContext,
    list_reference_options,
    validate_reference_value,
)


def test_reference_options_are_filtered_by_public_and_profile_domain(db_session):
    db_session.add_all(
        [
            ReferenceObject(object_type="RATE_SERVICE", gid="PUBLIC.RS_STD", xid="RS_STD", domain_name="PUBLIC", display_name="Standard"),
            ReferenceObject(object_type="RATE_SERVICE", gid="OTM1.RS_EXP", xid="RS_EXP", domain_name="OTM1", display_name="Express"),
            ReferenceObject(object_type="RATE_SERVICE", gid="OTM2.RS_OTHER", xid="RS_OTHER", domain_name="OTM2", display_name="Other"),
        ]
    )
    db_session.commit()

    context = ReferenceContext(project_id=None, environment_id=None, profile_id="profile_otm1", domain_name="OTM1", can_view_all_domains=False)
    options = list_reference_options(db_session, context, "RATE_SERVICE")

    assert [item.gid for item in options] == ["PUBLIC.RS_STD", "OTM1.RS_EXP"]


def test_view_all_domains_context_can_see_all_domains(db_session):
    db_session.add_all(
        [
            ReferenceObject(object_type="CURRENCY", gid="PUBLIC.USD", xid="USD", domain_name="PUBLIC", display_name="US Dollar"),
            ReferenceObject(object_type="CURRENCY", gid="OTM2.BRL", xid="BRL", domain_name="OTM2", display_name="Brazilian Real"),
        ]
    )
    db_session.commit()

    context = ReferenceContext(project_id=None, environment_id=None, profile_id="profile_dba", domain_name="OTM1", can_view_all_domains=True)
    options = list_reference_options(db_session, context, "CURRENCY")

    assert [item.gid for item in options] == ["OTM2.BRL", "PUBLIC.USD"]


def test_must_exist_policy_returns_error_when_missing(db_session):
    db_session.add(
        ReferenceFieldPolicy(
            module_id="rates",
            field_name="currency_gid",
            object_type="CURRENCY",
            policy="MUST_EXIST",
            severity_when_missing="ERROR",
            allow_manual_value=False,
        )
    )
    db_session.commit()

    context = ReferenceContext(project_id=None, environment_id=None, profile_id="profile_otm1", domain_name="OTM1", can_view_all_domains=False)
    result = validate_reference_value(db_session, context, "rates", "currency_gid", "OTM1.MISSING")

    assert result.valid is False
    assert result.severity == "ERROR"
    assert result.policy == "MUST_EXIST"


def test_free_text_policy_accepts_missing_value(db_session):
    db_session.add(
        ReferenceFieldPolicy(
            module_id="rates",
            field_name="rate_geo_gid",
            object_type="RATE_GEO",
            policy="FREE_TEXT",
            severity_when_missing="INFO",
            allow_manual_value=True,
        )
    )
    db_session.commit()

    context = ReferenceContext(project_id=None, environment_id=None, profile_id="profile_otm1", domain_name="OTM1", can_view_all_domains=False)
    result = validate_reference_value(db_session, context, "rates", "rate_geo_gid", "OTM1.NEW_RATE_GEO")

    assert result.valid is True
    assert result.severity == "INFO"
    assert result.policy == "FREE_TEXT"
```

- [ ] **Step 2: Run failing service tests**

Run: `python -m pytest tests/test_reference_catalog.py -q`

Expected: FAIL because `otm_workbench.reference.services` does not exist.

- [ ] **Step 3: Implement policy constants**

Create `src/otm_workbench/reference/policies.py`:

```python
from dataclasses import dataclass


MUST_EXIST = "MUST_EXIST"
SHOULD_EXIST_ALLOW_NEW = "SHOULD_EXIST_ALLOW_NEW"
SUGGEST_ONLY = "SUGGEST_ONLY"
FREE_TEXT = "FREE_TEXT"

ERROR = "ERROR"
WARNING = "WARNING"
INFO = "INFO"


@dataclass(frozen=True)
class ReferenceValidationResult:
    valid: bool
    severity: str
    policy: str
    message: str
    object_type: str
    gid: str
    domain_name: str | None = None
```

- [ ] **Step 4: Implement reference services**

Create `src/otm_workbench/reference/services.py`:

```python
from dataclasses import dataclass
from sqlalchemy.orm import Session

from otm_workbench.models import ReferenceFieldPolicy, ReferenceObject, ReferenceObjectType
from otm_workbench.reference.policies import (
    ERROR,
    FREE_TEXT,
    INFO,
    MUST_EXIST,
    ReferenceValidationResult,
    SHOULD_EXIST_ALLOW_NEW,
    SUGGEST_ONLY,
    WARNING,
)


@dataclass(frozen=True)
class ReferenceContext:
    project_id: str | None
    environment_id: str | None
    profile_id: str | None
    domain_name: str
    can_view_all_domains: bool = False


def allowed_domains(context: ReferenceContext) -> list[str]:
    if context.can_view_all_domains:
        return ["*"]
    return ["PUBLIC", context.domain_name.upper()]


def seed_reference_object_types(db: Session) -> None:
    object_types = [
        ("EXCHANGE_RATE", "Exchange Rate"),
        ("RATE_SERVICE", "Rate Service"),
        ("RATE_DISTANCE", "Rate Distance"),
        ("RATE_VERSION", "Rate Version"),
        ("ACCESSORIAL_CODE", "Accessorial Code"),
        ("EQUIPMENT_GROUP", "Equipment Group"),
        ("EQUIPMENT_GROUP_PROFILE", "Equipment Group Profile"),
        ("TRANSPORT_MODE", "Transport Mode"),
        ("CURRENCY", "Currency"),
        ("RATE_OFFERING", "Rate Offering"),
        ("RATE_GEO", "Rate Geo"),
    ]
    for code, name in object_types:
        exists = db.query(ReferenceObjectType).filter(ReferenceObjectType.code == code).first()
        if not exists:
            db.add(ReferenceObjectType(code=code, name=name))
    db.commit()


def seed_rates_field_policies(db: Session) -> None:
    policies = [
        ("transport_mode_gid", "TRANSPORT_MODE", MUST_EXIST, ERROR, False),
        ("currency_gid", "CURRENCY", MUST_EXIST, ERROR, False),
        ("accessorial_code_gid", "ACCESSORIAL_CODE", MUST_EXIST, ERROR, False),
        ("rate_service_gid", "RATE_SERVICE", SHOULD_EXIST_ALLOW_NEW, WARNING, True),
        ("rate_distance_gid", "RATE_DISTANCE", SHOULD_EXIST_ALLOW_NEW, WARNING, True),
        ("rate_version_gid", "RATE_VERSION", SHOULD_EXIST_ALLOW_NEW, WARNING, True),
        ("equipment_group_gid", "EQUIPMENT_GROUP", SHOULD_EXIST_ALLOW_NEW, WARNING, True),
        ("equipment_group_profile_gid", "EQUIPMENT_GROUP_PROFILE", SHOULD_EXIST_ALLOW_NEW, WARNING, True),
        ("rate_offering_gid", "RATE_OFFERING", SUGGEST_ONLY, WARNING, True),
        ("rate_geo_gid", "RATE_GEO", FREE_TEXT, INFO, True),
        ("rate_geo_xid", "RATE_GEO", FREE_TEXT, INFO, True),
    ]
    for field_name, object_type, policy, severity, allow_manual in policies:
        exists = (
            db.query(ReferenceFieldPolicy)
            .filter(
                ReferenceFieldPolicy.module_id == "rates",
                ReferenceFieldPolicy.field_name == field_name,
            )
            .first()
        )
        if not exists:
            db.add(
                ReferenceFieldPolicy(
                    module_id="rates",
                    field_name=field_name,
                    object_type=object_type,
                    policy=policy,
                    severity_when_missing=severity,
                    allow_manual_value=allow_manual,
                )
            )
    db.commit()


def list_reference_options(
    db: Session,
    context: ReferenceContext,
    object_type: str,
) -> list[ReferenceObject]:
    query = (
        db.query(ReferenceObject)
        .filter(ReferenceObject.object_type == object_type.upper())
        .filter(ReferenceObject.is_active.is_(True))
    )
    if not context.can_view_all_domains:
        query = query.filter(ReferenceObject.domain_name.in_(allowed_domains(context)))
    return query.order_by(ReferenceObject.domain_name, ReferenceObject.gid).all()


def find_reference(
    db: Session,
    context: ReferenceContext,
    object_type: str,
    gid: str,
) -> ReferenceObject | None:
    query = (
        db.query(ReferenceObject)
        .filter(ReferenceObject.object_type == object_type.upper())
        .filter(ReferenceObject.gid == gid)
        .filter(ReferenceObject.is_active.is_(True))
    )
    if not context.can_view_all_domains:
        query = query.filter(ReferenceObject.domain_name.in_(allowed_domains(context)))
    return query.first()


def get_field_policy(db: Session, module_id: str, field_name: str) -> ReferenceFieldPolicy | None:
    return (
        db.query(ReferenceFieldPolicy)
        .filter(
            ReferenceFieldPolicy.module_id == module_id,
            ReferenceFieldPolicy.field_name == field_name,
            ReferenceFieldPolicy.is_active.is_(True),
        )
        .first()
    )


def validate_reference_value(
    db: Session,
    context: ReferenceContext,
    module_id: str,
    field_name: str,
    value: str,
) -> ReferenceValidationResult:
    seed_rates_field_policies(db)
    policy = get_field_policy(db, module_id, field_name)
    if not policy:
        return ReferenceValidationResult(
            valid=True,
            severity=INFO,
            policy=FREE_TEXT,
            message="No active policy exists for this field; value is treated as free text.",
            object_type="FREE_TEXT",
            gid=value,
        )
    if policy.policy == FREE_TEXT:
        return ReferenceValidationResult(
            valid=True,
            severity=INFO,
            policy=policy.policy,
            message="Free text value accepted.",
            object_type=policy.object_type,
            gid=value,
        )
    reference = find_reference(db, context, policy.object_type, value)
    if reference:
        return ReferenceValidationResult(
            valid=True,
            severity=INFO,
            policy=policy.policy,
            message="Reference found and allowed for current profile.",
            object_type=policy.object_type,
            gid=value,
            domain_name=reference.domain_name,
        )
    if policy.policy == MUST_EXIST:
        return ReferenceValidationResult(
            valid=False,
            severity=policy.severity_when_missing,
            policy=policy.policy,
            message="Reference is required but was not found in the allowed catalog scope.",
            object_type=policy.object_type,
            gid=value,
        )
    return ReferenceValidationResult(
        valid=True,
        severity=policy.severity_when_missing,
        policy=policy.policy,
        message="Reference was not found; value may represent a new object if the business process allows it.",
        object_type=policy.object_type,
        gid=value,
    )
```

- [ ] **Step 5: Run service tests**

Run: `python -m pytest tests/test_reference_catalog.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/reference tests/test_reference_catalog.py
git commit -m "feat: add reference catalog policy services"
```

## Task 4: Reference Import And API Routes

**Files:**
- Modify: `src/otm_workbench/reference/services.py`
- Create: `src/otm_workbench/reference/routes.py`
- Modify: `src/otm_workbench/main.py`
- Test: `tests/test_reference_catalog.py`

- [ ] **Step 1: Write failing API tests**

Append to `tests/test_reference_catalog.py`:

```python
def test_reference_import_and_options_api_filters_domains(client, admin_header):
    imported = client.post(
        "/api/v1/reference/import-batches",
        json={
            "source_type": "json",
            "source_description": "synthetic seed",
            "records": [
                {"object_type": "RATE_SERVICE", "gid": "PUBLIC.RS_STD", "xid": "RS_STD", "domain_name": "PUBLIC", "display_name": "Standard"},
                {"object_type": "RATE_SERVICE", "gid": "OTM1.RS_EXP", "xid": "RS_EXP", "domain_name": "OTM1", "display_name": "Express"},
                {"object_type": "RATE_SERVICE", "gid": "OTM2.RS_OTHER", "xid": "RS_OTHER", "domain_name": "OTM2", "display_name": "Other"},
            ],
        },
        headers=admin_header,
    )
    assert imported.status_code == 200
    assert imported.json()["records_inserted"] == 3

    response = client.get(
        "/api/v1/reference/options?object_type=RATE_SERVICE&domain_name=OTM1",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert [item["gid"] for item in response.json()["items"]] == ["PUBLIC.RS_STD", "OTM1.RS_EXP"]


def test_reference_validate_api_uses_policy(client, admin_header):
    response = client.post(
        "/api/v1/reference/validate",
        json={"module_id": "rates", "field_name": "currency_gid", "value": "OTM1.MISSING", "domain_name": "OTM1"},
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["severity"] == "ERROR"
```

- [ ] **Step 2: Run failing API tests**

Run: `python -m pytest tests/test_reference_catalog.py::test_reference_import_and_options_api_filters_domains tests/test_reference_catalog.py::test_reference_validate_api_uses_policy -q`

Expected: FAIL with 404 because reference routes are not registered.

- [ ] **Step 3: Add import service**

Append to `src/otm_workbench/reference/services.py`:

```python
from datetime import UTC, datetime
import json

from otm_workbench.models import ReferenceImportBatch


def import_reference_records(
    db: Session,
    records: list[dict[str, object]],
    source_type: str,
    source_description: str,
    actor_user_id: str | None,
) -> ReferenceImportBatch:
    batch = ReferenceImportBatch(
        source_type=source_type,
        source_description=source_description,
        status="RUNNING",
        records_received=len(records),
        started_at=datetime.now(UTC).replace(tzinfo=None),
        created_by=actor_user_id,
    )
    db.add(batch)
    db.commit()
    inserted = 0
    updated = 0
    rejected = 0
    for record in records:
        object_type = str(record.get("object_type", "")).upper()
        gid = str(record.get("gid", ""))
        domain_name = str(record.get("domain_name", "")).upper()
        if not object_type or not gid or not domain_name:
            rejected += 1
            continue
        existing = (
            db.query(ReferenceObject)
            .filter(ReferenceObject.object_type == object_type, ReferenceObject.gid == gid)
            .first()
        )
        metadata = record.get("metadata_json", "{}")
        metadata_json = metadata if isinstance(metadata, str) else json.dumps(metadata)
        if existing:
            existing.xid = str(record.get("xid", existing.xid))
            existing.domain_name = domain_name
            existing.display_name = str(record.get("display_name", existing.display_name))
            existing.metadata_json = metadata_json
            existing.sync_batch_id = batch.id
            updated += 1
        else:
            db.add(
                ReferenceObject(
                    object_type=object_type,
                    gid=gid,
                    xid=str(record.get("xid", "")),
                    domain_name=domain_name,
                    display_name=str(record.get("display_name", "")),
                    metadata_json=metadata_json,
                    source=source_type,
                    sync_batch_id=batch.id,
                    last_synced_at=datetime.now(UTC).replace(tzinfo=None),
                )
            )
            inserted += 1
    batch.status = "COMPLETED"
    batch.records_inserted = inserted
    batch.records_updated = updated
    batch.records_rejected = rejected
    batch.finished_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(batch)
    return batch
```

- [ ] **Step 4: Add reference router**

Create `src/otm_workbench/reference/routes.py`:

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_admin, require_user
from otm_workbench.models import User
from otm_workbench.reference.services import (
    ReferenceContext,
    import_reference_records,
    list_reference_options,
    seed_reference_object_types,
    validate_reference_value,
)

router = APIRouter(prefix="/api/v1/reference", tags=["reference"])


class ReferenceImportRequest(BaseModel):
    source_type: str = "json"
    source_description: str = ""
    records: list[dict[str, object]]


class ReferenceOptionResponse(BaseModel):
    object_type: str
    gid: str
    xid: str
    domain_name: str
    display_name: str


class ReferenceValidateRequest(BaseModel):
    module_id: str
    field_name: str
    value: str
    domain_name: str = "OTM1"


@router.get("/object-types")
def list_object_types(db: Session = Depends(get_db), user: User = Depends(require_user)):
    seed_reference_object_types(db)
    items = [
        {"code": item.code, "name": item.name, "description": item.description}
        for item in db.query(__import__("otm_workbench.models").models.ReferenceObjectType).order_by(__import__("otm_workbench.models").models.ReferenceObjectType.code).all()
    ]
    return PageResponse(items=items, total=len(items))


@router.post("/import-batches")
def create_import_batch(
    payload: ReferenceImportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    batch = import_reference_records(
        db=db,
        records=payload.records,
        source_type=payload.source_type,
        source_description=payload.source_description,
        actor_user_id=user.id,
    )
    return {
        "id": batch.id,
        "status": batch.status,
        "records_received": batch.records_received,
        "records_inserted": batch.records_inserted,
        "records_updated": batch.records_updated,
        "records_rejected": batch.records_rejected,
    }


@router.get("/options", response_model=PageResponse[ReferenceOptionResponse])
def reference_options(
    object_type: str,
    domain_name: str = "OTM1",
    view_all_domains: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    context = ReferenceContext(
        project_id=None,
        environment_id=None,
        profile_id=None,
        domain_name=domain_name,
        can_view_all_domains=bool(user.is_admin and view_all_domains),
    )
    objects = list_reference_options(db, context, object_type)
    items = [
        ReferenceOptionResponse(
            object_type=item.object_type,
            gid=item.gid,
            xid=item.xid,
            domain_name=item.domain_name,
            display_name=item.display_name,
        )
        for item in objects
    ]
    return PageResponse(items=items, total=len(items))


@router.post("/validate")
def validate_reference(
    payload: ReferenceValidateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    context = ReferenceContext(
        project_id=None,
        environment_id=None,
        profile_id=None,
        domain_name=payload.domain_name,
        can_view_all_domains=False,
    )
    result = validate_reference_value(
        db,
        context,
        payload.module_id,
        payload.field_name,
        payload.value,
    )
    return result.__dict__
```

- [ ] **Step 5: Simplify object-type import**

In `src/otm_workbench/reference/routes.py`, replace the dynamic `__import__` usage with a normal import:

```python
from otm_workbench.models import ReferenceObjectType, User
```

Then update the query:

```python
    items = [
        {"code": item.code, "name": item.name, "description": item.description}
        for item in db.query(ReferenceObjectType).order_by(ReferenceObjectType.code).all()
    ]
```

- [ ] **Step 6: Register router**

In `src/otm_workbench/main.py`, import and include the reference router:

```python
from otm_workbench.reference.routes import router as reference_router
```

Inside `create_app()` after `app.include_router(platform_router)`:

```python
    app.include_router(reference_router)
```

- [ ] **Step 7: Run reference API tests**

Run: `python -m pytest tests/test_reference_catalog.py -q`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/otm_workbench/main.py src/otm_workbench/reference tests/test_reference_catalog.py
git commit -m "feat: add reference catalog APIs"
```

## Task 5: Rates Dictionary And Rate Offering APIs

**Files:**
- Create: `src/otm_workbench/modules/rates/routes.py`
- Modify: `src/otm_workbench/main.py`
- Test: `tests/test_rates_dictionary.py`

- [ ] **Step 1: Write failing rates API tests**

Append to `tests/test_rates_dictionary.py`:

```python
def test_rates_dictionary_table_api_returns_pk_and_date_columns(client, admin_header):
    response = client.get("/api/v1/modules/rates/dictionary/tables/RATE_GEO_COST", headers=admin_header)

    assert response.status_code == 200
    assert response.json()["table_name"] == "RATE_GEO_COST"
    assert response.json()["primary_key"] == ["RATE_GEO_COST_GROUP_GID", "RATE_GEO_COST_SEQ"]
    assert "ATTRIBUTE_DATE1" in response.json()["date_columns"]


def test_rates_validate_load_sequence_api_reports_dependencies(client, admin_header):
    response = client.post(
        "/api/v1/modules/rates/dictionary/validate-load-sequence",
        json={"tables": ["RATE_GEO_COST"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert any(item["parent_table_name"] == "RATE_GEO_COST_GROUP" for item in response.json()["issues"])
```

- [ ] **Step 2: Run failing rates API tests**

Run: `python -m pytest tests/test_rates_dictionary.py::test_rates_dictionary_table_api_returns_pk_and_date_columns tests/test_rates_dictionary.py::test_rates_validate_load_sequence_api_reports_dependencies -q`

Expected: FAIL with 404 because rates routes are not registered.

- [ ] **Step 3: Implement rates router**

Create `src/otm_workbench/modules/rates/routes.py`:

```python
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import ReferenceObject, User
from otm_workbench.modules.rates.dictionary import (
    RATES_LOAD_SEQUENCE,
    load_table_definition,
    validate_load_sequence,
)

router = APIRouter(prefix="/api/v1/modules/rates", tags=["rates"])


class LoadSequenceRequest(BaseModel):
    tables: list[str] = RATES_LOAD_SEQUENCE


@router.get("/dictionary/tables")
def list_rates_dictionary_tables(user: User = Depends(require_user)):
    return PageResponse(items=[{"table_name": item} for item in RATES_LOAD_SEQUENCE], total=len(RATES_LOAD_SEQUENCE))


@router.get("/dictionary/tables/{table_name}")
def get_rates_dictionary_table(table_name: str, user: User = Depends(require_user)):
    definition = load_table_definition(Path(get_settings().otm_data_dictionary_root), table_name)
    return {
        "table_name": definition.table_name,
        "schema_name": definition.schema_name,
        "description": definition.description,
        "primary_key": definition.primary_key,
        "required_columns": definition.required_columns,
        "date_columns": definition.date_columns,
        "foreign_keys": [item.__dict__ for item in definition.foreign_keys],
    }


@router.post("/dictionary/validate-load-sequence")
def validate_rates_load_sequence(payload: LoadSequenceRequest, user: User = Depends(require_user)):
    result = validate_load_sequence(Path(get_settings().otm_data_dictionary_root), payload.tables)
    return {
        "valid": result.valid,
        "known_tables": result.known_tables,
        "missing_tables": result.missing_tables,
        "issues": [item.__dict__ for item in result.issues],
    }


@router.get("/reference/rate-offerings")
def list_rate_offerings(
    servprov_gid: str | None = None,
    transport_mode_gid: str | None = None,
    rate_service_gid: str | None = None,
    equipment_group_profile_gid: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(ReferenceObject).filter(ReferenceObject.object_type == "RATE_OFFERING")
    for key, value in {
        "servprov_gid": servprov_gid,
        "transport_mode_gid": transport_mode_gid,
        "rate_service_gid": rate_service_gid,
        "equipment_group_profile_gid": equipment_group_profile_gid,
    }.items():
        if value:
            query = query.filter(ReferenceObject.metadata_json.contains(f'"{key}": "{value}"'))
    objects = query.order_by(ReferenceObject.gid).all()
    items = [
        {
            "gid": item.gid,
            "xid": item.xid,
            "domain_name": item.domain_name,
            "display_name": item.display_name,
            "metadata_json": item.metadata_json,
        }
        for item in objects
    ]
    return PageResponse(items=items, total=len(items))
```

- [ ] **Step 4: Register rates router**

In `src/otm_workbench/main.py`, import and include:

```python
from otm_workbench.modules.rates.routes import router as rates_router
```

Inside `create_app()` after the reference router:

```python
    app.include_router(rates_router)
```

- [ ] **Step 5: Run rates dictionary API tests**

Run: `python -m pytest tests/test_rates_dictionary.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/main.py src/otm_workbench/modules tests/test_rates_dictionary.py
git commit -m "feat: expose rates dictionary APIs"
```

## Task 6: Rate Offering Duplicate Candidate Check

**Files:**
- Modify: `src/otm_workbench/modules/rates/routes.py`
- Test: `tests/test_reference_catalog.py`

- [ ] **Step 1: Write failing duplicate check test**

Append to `tests/test_reference_catalog.py`:

```python
def test_rate_offering_duplicate_check_returns_warning(client, admin_header):
    client.post(
        "/api/v1/reference/import-batches",
        json={
            "source_type": "json",
            "source_description": "rate offering seed",
            "records": [
                {
                    "object_type": "RATE_OFFERING",
                    "gid": "OTM1.RO_STD",
                    "xid": "RO_STD",
                    "domain_name": "OTM1",
                    "display_name": "Synthetic Standard Offering",
                    "metadata_json": {
                        "servprov_gid": "OTM1.SERVPROV_A",
                        "transport_mode_gid": "PUBLIC.TL",
                        "rate_service_gid": "OTM1.RS_STD",
                        "equipment_group_profile_gid": "PUBLIC.EQP_DRY",
                        "currency_gid": "PUBLIC.USD",
                    },
                }
            ],
        },
        headers=admin_header,
    )

    response = client.post(
        "/api/v1/modules/rates/reference/rate-offerings/duplicate-check",
        json={
            "servprov_gid": "OTM1.SERVPROV_A",
            "transport_mode_gid": "PUBLIC.TL",
            "rate_service_gid": "OTM1.RS_STD",
            "equipment_group_profile_gid": "PUBLIC.EQP_DRY",
            "currency_gid": "PUBLIC.USD",
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["severity"] == "WARNING"
    assert response.json()["candidates"][0]["gid"] == "OTM1.RO_STD"
```

- [ ] **Step 2: Run failing duplicate test**

Run: `python -m pytest tests/test_reference_catalog.py::test_rate_offering_duplicate_check_returns_warning -q`

Expected: FAIL because the endpoint does not exist.

- [ ] **Step 3: Add duplicate-check endpoint**

Append to `src/otm_workbench/modules/rates/routes.py`:

```python
import json


class RateOfferingDuplicateCheckRequest(BaseModel):
    servprov_gid: str
    transport_mode_gid: str
    rate_service_gid: str
    equipment_group_profile_gid: str
    currency_gid: str


@router.post("/reference/rate-offerings/duplicate-check")
def check_rate_offering_duplicate(
    payload: RateOfferingDuplicateCheckRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    candidates = []
    for item in db.query(ReferenceObject).filter(ReferenceObject.object_type == "RATE_OFFERING").all():
        metadata = json.loads(item.metadata_json or "{}")
        if all(
            metadata.get(key) == value
            for key, value in payload.model_dump().items()
        ):
            candidates.append(
                {
                    "gid": item.gid,
                    "xid": item.xid,
                    "domain_name": item.domain_name,
                    "display_name": item.display_name,
                }
            )
    return {
        "severity": "WARNING" if candidates else "INFO",
        "message": "Potential duplicate Rate Offering found." if candidates else "No duplicate candidate found.",
        "candidates": candidates,
    }
```

- [ ] **Step 4: Run duplicate tests**

Run: `python -m pytest tests/test_reference_catalog.py::test_rate_offering_duplicate_check_returns_warning -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/otm_workbench/modules/rates/routes.py tests/test_reference_catalog.py
git commit -m "feat: detect rate offering duplicate candidates"
```

## Task 7: OTM CSV Preview Contract

**Files:**
- Create: `src/otm_workbench/modules/rates/csv_preview.py`
- Modify: `src/otm_workbench/modules/rates/routes.py`
- Test: `tests/test_rates_csv_preview.py`

- [ ] **Step 1: Write failing CSV preview tests**

Create `tests/test_rates_csv_preview.py`:

```python
from pathlib import Path

from otm_workbench.modules.rates.csv_preview import build_otm_csv_preview


DATA_DICT = Path("OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict")


def test_otm_csv_preview_uses_table_first_then_columns():
    output = build_otm_csv_preview(
        DATA_DICT,
        table_name="RATE_GEO_COST",
        columns=["RATE_GEO_COST_GROUP_GID", "RATE_GEO_COST_SEQ", "CHARGE_AMOUNT"],
        rows=[{"RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_1", "RATE_GEO_COST_SEQ": 1, "CHARGE_AMOUNT": 10}],
    )

    lines = output.splitlines()
    assert lines[0] == "RATE_GEO_COST"
    assert lines[1] == "RATE_GEO_COST_GROUP_GID,RATE_GEO_COST_SEQ,CHARGE_AMOUNT"
    assert lines[2] == "OTM1.RGCG_1,1,10"


def test_otm_csv_preview_adds_alter_session_for_date_columns():
    output = build_otm_csv_preview(
        DATA_DICT,
        table_name="RATE_OFFERING",
        columns=["RATE_OFFERING_GID", "EFFECTIVE_DATE"],
        rows=[{"RATE_OFFERING_GID": "OTM1.RO_1", "EFFECTIVE_DATE": "2026-05-18 10:00:00"}],
    )

    lines = output.splitlines()
    assert lines[0] == "RATE_OFFERING"
    assert lines[1] == "RATE_OFFERING_GID,EFFECTIVE_DATE"
    assert lines[2] == "exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'"
    assert lines[3] == "OTM1.RO_1,2026-05-18 10:00:00"


def test_otm_csv_preview_rejects_unknown_columns():
    try:
        build_otm_csv_preview(
            DATA_DICT,
            table_name="RATE_GEO_COST",
            columns=["RATE_GEO_COST_GROUP_GID", "NOT_A_COLUMN"],
            rows=[{"RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_1", "NOT_A_COLUMN": "x"}],
        )
    except ValueError as exc:
        assert "NOT_A_COLUMN" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown column")
```

- [ ] **Step 2: Run failing CSV preview tests**

Run: `python -m pytest tests/test_rates_csv_preview.py -q`

Expected: FAIL because `csv_preview.py` does not exist.

- [ ] **Step 3: Implement CSV preview builder**

Create `src/otm_workbench/modules/rates/csv_preview.py`:

```python
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
        raise ValueError(f"Columns do not exist in OTM Data Dictionary for {definition.table_name}: {', '.join(missing)}")
    lines = [definition.table_name, ",".join(normalized_columns)]
    if any(column in definition.date_columns for column in normalized_columns):
        lines.append(DATE_FORMAT_DIRECTIVE)
    for row in rows:
        values = [serialize_value(row.get(column, row.get(column.lower(), ""))) for column in normalized_columns]
        lines.append(",".join(values))
    return "\n".join(lines)
```

- [ ] **Step 4: Add CSV preview API**

Append to `src/otm_workbench/modules/rates/routes.py`:

```python
from otm_workbench.modules.rates.csv_preview import build_otm_csv_preview


class CsvPreviewRequest(BaseModel):
    table_name: str
    columns: list[str]
    rows: list[dict[str, object]]


@router.post("/csv/preview")
def preview_rates_csv(payload: CsvPreviewRequest, user: User = Depends(require_user)):
    content = build_otm_csv_preview(
        Path(get_settings().otm_data_dictionary_root),
        payload.table_name,
        payload.columns,
        payload.rows,
    )
    return {"content": content}
```

- [ ] **Step 5: Add API test for CSV preview**

Append to `tests/test_rates_csv_preview.py`:

```python
def test_csv_preview_api(client, admin_header):
    response = client.post(
        "/api/v1/modules/rates/csv/preview",
        json={
            "table_name": "RATE_GEO_COST",
            "columns": ["RATE_GEO_COST_GROUP_GID", "RATE_GEO_COST_SEQ"],
            "rows": [{"RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_1", "RATE_GEO_COST_SEQ": 1}],
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["content"].splitlines()[0] == "RATE_GEO_COST"
```

- [ ] **Step 6: Run CSV preview tests**

Run: `python -m pytest tests/test_rates_csv_preview.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/otm_workbench/modules/rates/csv_preview.py src/otm_workbench/modules/rates/routes.py tests/test_rates_csv_preview.py
git commit -m "feat: add rates CSV preview contract"
```

## Task 8: Module Registry And Documentation

**Files:**
- Modify: `src/otm_workbench/platform/navigation.py`
- Modify: `README.md`
- Test: `tests/test_modules_navigation.py`

- [ ] **Step 1: Write failing module registry test**

Append to `tests/test_modules_navigation.py`:

```python
def test_modules_endpoint_returns_rates_module(client, admin_header):
    response = client.get("/api/v1/platform/modules", headers=admin_header)

    assert response.status_code == 200
    module_ids = [item["id"] for item in response.json()["items"]]
    assert "rates" in module_ids
```

- [ ] **Step 2: Run failing module test**

Run: `python -m pytest tests/test_modules_navigation.py::test_modules_endpoint_returns_rates_module -q`

Expected: FAIL because `rates` is not registered.

- [ ] **Step 3: Register rates module**

In `src/otm_workbench/platform/navigation.py`, add this module to the list returned/seeded by the existing module registry function:

```python
Module(
    id="rates",
    display_name="Rates Studio",
    route_base="/rates",
    status="PLANNED",
    required_capability="rates.reference.view",
)
```

- [ ] **Step 4: Update README**

Append to `README.md`:

```markdown
## Rates Reference Catalog Verification

The Rates Reference Catalog is backend/API-only. It validates OTM table metadata against the local Data Dictionary under `OTM_RESOURCES/DATA_DICT26B` and exposes reference catalog contracts for future tariff workflows.

```powershell
python -m pytest tests/test_reference_catalog.py tests/test_rates_dictionary.py tests/test_rates_csv_preview.py
python -m alembic upgrade head
```
```

- [ ] **Step 5: Run module test**

Run: `python -m pytest tests/test_modules_navigation.py::test_modules_endpoint_returns_rates_module -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add README.md src/otm_workbench/platform/navigation.py tests/test_modules_navigation.py
git commit -m "docs: register rates reference catalog module"
```

## Task 9: Full Verification

**Files:**
- All changed files

- [ ] **Step 1: Run reference test suite**

Run: `python -m pytest tests/test_reference_catalog.py tests/test_rates_dictionary.py tests/test_rates_csv_preview.py -q`

Expected: PASS.

- [ ] **Step 2: Run full pytest suite**

Run: `python -m pytest -q`

Expected: PASS.

- [ ] **Step 3: Run migrations**

Run: `python -m alembic upgrade head`

Expected: exits 0.

- [ ] **Step 4: Run lint**

Run: `python -m ruff check src tests`

Expected: PASS.

- [ ] **Step 5: Confirm working tree scope**

Run: `git status --short`

Expected: only intentional tracked changes are committed. `OTM_RESOURCES/` may remain untracked and must not be staged.

## Acceptance Checklist

- [ ] New database tables exist in SQLAlchemy metadata and Alembic migration.
- [ ] Data Dictionary reader loads `RATE_GEO_COST` PK, required columns, date columns, and FKs.
- [ ] Load sequence validation detects missing/out-of-order FK dependencies.
- [ ] Reference options are filtered by `PUBLIC + OTM1` for normal context.
- [ ] Admin/DBA-style context can request all domains through explicit flag.
- [ ] `MUST_EXIST` returns `ERROR` when missing.
- [ ] `SHOULD_EXIST_ALLOW_NEW` returns `WARNING` when missing.
- [ ] `SUGGEST_ONLY` for Rate Offering does not block creation.
- [ ] `FREE_TEXT` accepts missing catalog values.
- [ ] Import batch inserts/updates/rejects records and returns counts.
- [ ] Rate Offering duplicate check returns `WARNING` with candidates.
- [ ] CSV preview writes table name on line 1 and columns on line 2.
- [ ] CSV preview adds `exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'` when date columns are present.
- [ ] CSV preview rejects columns absent from the OTM Data Dictionary.
- [ ] No docs, tests, fixtures, or seeds mention real clients.
- [ ] `python -m pytest -q` passes.
- [ ] `python -m ruff check src tests` passes.
- [ ] `python -m alembic upgrade head` passes.

## Execution Notes

Keep `OTM_RESOURCES/` untracked. The implementation may read from it during tests, but the resource directory must not be added to git in this branch.
