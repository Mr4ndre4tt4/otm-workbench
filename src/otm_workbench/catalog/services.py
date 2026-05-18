from dataclasses import dataclass
import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.catalog.canonical import MASTERDATA_TABLES, RATES_TABLES
from otm_workbench.models import OtmMacroObject, OtmMacroObjectDependency, OtmMacroObjectTable
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
    if normalized in MASTERDATA_TABLES:
        return TableClassification(
            data_category="MASTER_DATA",
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


MACRO_OBJECT_SEED = [
    {
        "code": "RATE_OFFERING",
        "name": "Rate Offering",
        "category": "RATES_SETUP",
        "description": "Rate offering setup and reusable tariff header metadata.",
        "default_load_order": 100,
        "default_method": "HYBRID",
        "method_options": ["SOURCING", "CSV", "MANUAL"],
        "allow_cutover": True,
        "allow_csvutil": True,
        "tables": [
            {"table_name": "RATE_OFFERING", "relationship_role": "PRIMARY", "is_primary_table": True},
        ],
        "dependencies": [],
    },
    {
        "code": "RATE_RECORD",
        "name": "Rate Record",
        "category": "RATES_SETUP",
        "description": "Rate record, lane and cost setup tables.",
        "default_load_order": 200,
        "default_method": "HYBRID",
        "method_options": ["SOURCING", "CSV", "MANUAL"],
        "allow_cutover": True,
        "allow_csvutil": True,
        "tables": [
            {"table_name": "X_LANE", "relationship_role": "LANE", "is_primary_table": False},
            {"table_name": "RATE_GEO", "relationship_role": "PRIMARY", "is_primary_table": True},
            {"table_name": "RATE_GEO_COST_GROUP", "relationship_role": "COST_GROUP", "is_primary_table": False},
            {"table_name": "RATE_GEO_COST", "relationship_role": "COST", "is_primary_table": False},
        ],
        "dependencies": [
            {"depends_on_code": "RATE_OFFERING", "dependency_type": "MUST_LOAD_BEFORE"},
        ],
    },
    {
        "code": "ITEM",
        "name": "Item",
        "category": "MASTER_DATA",
        "description": "Item and packaging master data.",
        "default_load_order": 300,
        "default_method": "CSV",
        "method_options": ["CSV"],
        "allow_cutover": True,
        "allow_csvutil": True,
        "tables": [
            {"table_name": "ITEM", "relationship_role": "PRIMARY", "is_primary_table": True},
            {"table_name": "SHIP_UNIT_SPEC", "relationship_role": "PACKAGING", "is_primary_table": False},
            {"table_name": "PACKAGED_ITEM", "relationship_role": "PACKAGING", "is_primary_table": False},
            {"table_name": "TI_HI", "relationship_role": "PACKAGING", "is_primary_table": False},
        ],
        "dependencies": [],
    },
    {
        "code": "REGION",
        "name": "Region",
        "category": "MASTER_DATA",
        "description": "Region and region detail master data.",
        "default_load_order": 250,
        "default_method": "HYBRID",
        "method_options": ["MIGRATION_PROJECT", "FORMULATE_REGION", "CSV"],
        "allow_cutover": True,
        "allow_csvutil": True,
        "tables": [
            {"table_name": "REGION", "relationship_role": "PRIMARY", "is_primary_table": True},
            {"table_name": "REGION_DETAIL", "relationship_role": "DETAIL", "is_primary_table": False},
        ],
        "dependencies": [],
    },
]


def seed_macro_objects(db: Session, dictionary_root: Path) -> None:
    by_code: dict[str, OtmMacroObject] = {}
    for payload in MACRO_OBJECT_SEED:
        code = str(payload["code"])
        macro = db.query(OtmMacroObject).filter(OtmMacroObject.code == code).first()
        if macro is None:
            macro = OtmMacroObject(code=code)
            db.add(macro)
        macro.name = str(payload["name"])
        macro.category = str(payload["category"])
        macro.description = str(payload["description"])
        macro.default_load_order = int(payload["default_load_order"])
        macro.default_method = str(payload["default_method"])
        macro.method_options_json = json.dumps(payload["method_options"], sort_keys=True)
        macro.allow_cutover = bool(payload["allow_cutover"])
        macro.allow_csvutil = bool(payload["allow_csvutil"])
        macro.evidence_required_default = True
        macro.is_active = True
        by_code[code] = macro
    db.flush()

    for macro in by_code.values():
        db.query(OtmMacroObjectTable).filter(OtmMacroObjectTable.macro_object_id == macro.id).delete()
        db.query(OtmMacroObjectDependency).filter(OtmMacroObjectDependency.macro_object_id == macro.id).delete()
    db.flush()

    for payload in MACRO_OBJECT_SEED:
        macro = by_code[str(payload["code"])]
        for table_payload in payload["tables"]:
            table_name = str(table_payload["table_name"]).upper()
            table_definition = safe_load_table(dictionary_root, table_name)
            classification = classify_table(table_name)
            db.add(
                OtmMacroObjectTable(
                    macro_object_id=macro.id,
                    table_name=table_name,
                    relationship_role=str(table_payload["relationship_role"]),
                    is_primary_table=bool(table_payload["is_primary_table"]),
                    is_required=True,
                    data_category=classification.data_category,
                    validated_by_datadict=table_definition is not None,
                    allow_csvutil=classification.allow_csvutil,
                    allow_cutover=classification.allow_cutover,
                )
            )
        for dependency_payload in payload["dependencies"]:
            depends_on = by_code[str(dependency_payload["depends_on_code"])]
            db.add(
                OtmMacroObjectDependency(
                    macro_object_id=macro.id,
                    depends_on_macro_object_id=depends_on.id,
                    dependency_type=str(dependency_payload["dependency_type"]),
                    is_required=True,
                    notes="Seeded dependency from Catalog Core MVP0.",
                )
            )
    db.commit()


def list_macro_objects(db: Session, dictionary_root: Path) -> list[OtmMacroObject]:
    seed_macro_objects(db, dictionary_root)
    return db.query(OtmMacroObject).filter(OtmMacroObject.is_active.is_(True)).order_by(OtmMacroObject.default_load_order).all()


def get_macro_object(db: Session, dictionary_root: Path, code: str) -> OtmMacroObject | None:
    seed_macro_objects(db, dictionary_root)
    return db.query(OtmMacroObject).filter(OtmMacroObject.code == code.upper(), OtmMacroObject.is_active.is_(True)).first()


def macro_object_tables(db: Session, macro: OtmMacroObject) -> list[OtmMacroObjectTable]:
    return (
        db.query(OtmMacroObjectTable)
        .filter(OtmMacroObjectTable.macro_object_id == macro.id)
        .order_by(OtmMacroObjectTable.is_primary_table.desc(), OtmMacroObjectTable.table_name)
        .all()
    )


def macro_object_dependencies(db: Session, macro: OtmMacroObject) -> list[tuple[OtmMacroObjectDependency, OtmMacroObject]]:
    rows = (
        db.query(OtmMacroObjectDependency, OtmMacroObject)
        .join(OtmMacroObject, OtmMacroObjectDependency.depends_on_macro_object_id == OtmMacroObject.id)
        .filter(OtmMacroObjectDependency.macro_object_id == macro.id)
        .order_by(OtmMacroObject.code)
        .all()
    )
    return rows


def serialize_macro_object_table(row: OtmMacroObjectTable) -> dict[str, object]:
    return {
        "id": row.id,
        "table_name": row.table_name,
        "relationship_role": row.relationship_role,
        "is_primary_table": row.is_primary_table,
        "is_required": row.is_required,
        "data_category": row.data_category,
        "validated_by_datadict": row.validated_by_datadict,
        "allow_csvutil": row.allow_csvutil,
        "allow_cutover": row.allow_cutover,
    }


def serialize_macro_object_dependency(row: OtmMacroObjectDependency, depends_on: OtmMacroObject) -> dict[str, object]:
    return {
        "id": row.id,
        "depends_on_code": depends_on.code,
        "depends_on_name": depends_on.name,
        "dependency_type": row.dependency_type,
        "is_required": row.is_required,
        "notes": row.notes,
    }


def serialize_macro_object(db: Session, macro: OtmMacroObject, include_children: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": macro.id,
        "code": macro.code,
        "name": macro.name,
        "category": macro.category,
        "description": macro.description,
        "default_load_order": macro.default_load_order,
        "default_method": macro.default_method,
        "method_options": json.loads(macro.method_options_json or "[]"),
        "allow_cutover": macro.allow_cutover,
        "allow_csvutil": macro.allow_csvutil,
        "evidence_required_default": macro.evidence_required_default,
    }
    if include_children:
        payload["tables"] = [serialize_macro_object_table(row) for row in macro_object_tables(db, macro)]
        payload["dependencies"] = [
            serialize_macro_object_dependency(row, depends_on)
            for row, depends_on in macro_object_dependencies(db, macro)
        ]
    return payload
