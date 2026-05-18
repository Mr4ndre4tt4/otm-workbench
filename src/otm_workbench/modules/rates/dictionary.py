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
        name for name, item in columns.items() if item.get("isNull") is False
    ]
    date_columns = [
        name for name, item in columns.items() if str(item.get("dataType", "")).upper() == "DATE"
    ]
    foreign_keys: list[ForeignKeyColumn] = []
    for foreign_key in payload.get("foreignKeys", []):
        parent = str(foreign_key.get("parentTableName", "")).upper()
        for relation in foreign_key.get("columnRelation", []):
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
                severity = "ERROR" if parent in RATES_LOAD_SEQUENCE else "WARNING"
                issues.append(
                    SequenceIssue(
                        table_name=table,
                        parent_table_name=parent,
                        column_name=foreign_key.column_name,
                        severity=severity,
                        message=(
                            f"{table}.{foreign_key.column_name} references {parent}, "
                            "which is outside this sequence."
                        ),
                    )
                )
            elif positions[parent] > positions[table]:
                issues.append(
                    SequenceIssue(
                        table_name=table,
                        parent_table_name=parent,
                        column_name=foreign_key.column_name,
                        severity="ERROR",
                        message=(
                            f"{table}.{foreign_key.column_name} references {parent}, "
                            "which appears later in the sequence."
                        ),
                    )
                )
    has_errors = any(issue.severity == "ERROR" for issue in issues)
    return SequenceValidationResult(
        valid=not missing_tables and not has_errors,
        known_tables=known_tables,
        missing_tables=missing_tables,
        issues=issues,
    )
