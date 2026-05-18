from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.modules.rates.dictionary import TableDefinition, load_table_definition
from otm_workbench.reference.services import ReferenceContext, allowed_domains, list_reference_options


TRANSACTIONAL_TABLE_PREFIXES = (
    "SHIPMENT",
    "ORDER_RELEASE",
    "INVOICE",
    "VOUCHER",
    "TRACKING",
)

TRANSACTIONAL_TABLES = {
    "SHIPMENT",
    "ORDER_RELEASE",
    "INVOICE",
    "VOUCHER",
}

RATES_TABLES = {
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
}


@dataclass(frozen=True)
class TableClassification:
    data_category: str
    is_transactional: bool
    allow_cutover: bool
    allow_csvutil: bool


def classify_table(table_name: str) -> TableClassification:
    normalized = table_name.upper()
    is_transactional = normalized in TRANSACTIONAL_TABLES or normalized.startswith(TRANSACTIONAL_TABLE_PREFIXES)
    if is_transactional:
        return TableClassification(
            data_category="TRANSACTIONAL",
            is_transactional=True,
            allow_cutover=False,
            allow_csvutil=False,
        )
    if normalized in RATES_TABLES:
        return TableClassification(
            data_category="RATES_SETUP",
            is_transactional=False,
            allow_cutover=True,
            allow_csvutil=True,
        )
    return TableClassification(
        data_category="UNKNOWN",
        is_transactional=False,
        allow_cutover=False,
        allow_csvutil=False,
    )


def serialize_table_definition(definition: TableDefinition) -> dict[str, object]:
    classification = classify_table(definition.table_name)
    return {
        "table_name": definition.table_name,
        "exists": True,
        "schema_name": definition.schema_name,
        "description": definition.description,
        "primary_key": definition.primary_key,
        "required_columns": definition.required_columns,
        "date_columns": definition.date_columns,
        "foreign_key_count": len(definition.foreign_keys),
        "data_category": classification.data_category,
        "is_transactional": classification.is_transactional,
        "allow_cutover": classification.allow_cutover,
        "allow_csvutil": classification.allow_csvutil,
    }


def serialize_columns(definition: TableDefinition) -> list[dict[str, object]]:
    items = []
    for column_name, payload in sorted(definition.columns.items()):
        items.append(
            {
                "column_name": column_name,
                "data_type": payload.get("dataType"),
                "nullable": payload.get("isNull"),
                "is_primary_key": column_name in definition.primary_key,
                "is_required": column_name in definition.required_columns,
            }
        )
    return items


def safe_load_table(dictionary_root: Path, table_name: str) -> TableDefinition | None:
    try:
        return load_table_definition(dictionary_root, table_name)
    except FileNotFoundError:
        return None


def validate_table(dictionary_root: Path, table_name: str, usage: str | None = None) -> dict[str, object]:
    normalized = table_name.upper()
    definition = safe_load_table(dictionary_root, normalized)
    if definition is None:
        return {
            "table_name": normalized,
            "exists": False,
            "data_category": "UNKNOWN",
            "is_transactional": False,
            "allow_cutover": False,
            "allow_csvutil": False,
            "severity": "ERROR",
            "message": "Table is not present in the local OTM Data Dictionary.",
        }
    classification = classify_table(normalized)
    usage_normalized = (usage or "").lower()
    blocked = (usage_normalized == "cutover" and not classification.allow_cutover) or (
        usage_normalized == "csvutil" and not classification.allow_csvutil
    )
    severity = "ERROR" if blocked else "INFO"
    message = "Table is allowed for the requested usage."
    if blocked and classification.is_transactional:
        message = "Transactional table is blocked by default for cutover and CSVUTIL generation."
    elif blocked:
        message = "Table is not explicitly allowlisted for the requested usage."
    return {
        **serialize_table_definition(definition),
        "severity": severity,
        "message": message,
    }


def validate_column(dictionary_root: Path, table_name: str, column_name: str) -> dict[str, object]:
    normalized_table = table_name.upper()
    normalized_column = column_name.upper()
    definition = safe_load_table(dictionary_root, normalized_table)
    if definition is None:
        return {
            "table_name": normalized_table,
            "column_name": normalized_column,
            "table_exists": False,
            "exists": False,
            "severity": "ERROR",
            "message": "Table is not present in the local OTM Data Dictionary.",
        }
    column = definition.columns.get(normalized_column)
    if column is None:
        return {
            "table_name": normalized_table,
            "column_name": normalized_column,
            "table_exists": True,
            "exists": False,
            "severity": "ERROR",
            "message": "Column is not present in the local OTM Data Dictionary table.",
        }
    return {
        "table_name": normalized_table,
        "column_name": normalized_column,
        "table_exists": True,
        "exists": True,
        "data_type": column.get("dataType"),
        "nullable": column.get("isNull"),
        "severity": "INFO",
        "message": "Column exists in the local OTM Data Dictionary table.",
    }


def reference_options_payload(
    db: Session,
    *,
    object_type: str,
    domain_name: str,
    project_id: str | None = None,
    environment_id: str | None = None,
    profile_id: str | None = None,
    can_view_all_domains: bool = False,
) -> dict[str, object]:
    context = ReferenceContext(
        project_id=project_id,
        environment_id=environment_id,
        profile_id=profile_id,
        domain_name=domain_name,
        can_view_all_domains=can_view_all_domains,
    )
    options = list_reference_options(db, context, object_type)
    return {
        "object_type": object_type.upper(),
        "project_id": project_id,
        "environment_id": environment_id,
        "profile_id": profile_id,
        "domain_name": domain_name.upper(),
        "allowed_domains": allowed_domains(context),
        "items": [
            {
                "gid": item.gid,
                "xid": item.xid,
                "domain_name": item.domain_name,
                "display_name": item.display_name,
            }
            for item in options
        ],
    }
