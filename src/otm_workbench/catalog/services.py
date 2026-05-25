from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from sqlalchemy.orm import Session

from otm_workbench.catalog.canonical import MASTERDATA_TABLES, RATES_TABLES
from otm_workbench.models import (
    Evidence,
    MacroObjectSchemaLink,
    OtmMacroObject,
    OtmMacroObjectDependency,
    OtmMacroObjectTable,
    SchemaFile,
    SchemaPack,
    SchemaPath,
    SchemaRoot,
    ServiceOperation,
)
from otm_workbench.modules.rates.dictionary import TableDefinition, load_table_definition
from otm_workbench.reference.services import ReferenceContext, allowed_domains, list_reference_options


SENSITIVE_SCHEMA_PATTERNS = (
    re.compile(r"\b(password|passwd|secret|credential|api[_-]?key|token)\b\s*=", re.IGNORECASE),
    re.compile(r"\b(real[-_ ]?client|cliente[-_ ]?real)\b", re.IGNORECASE),
)


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


class SensitiveSchemaContentError(ValueError):
    pass


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


def list_dictionary_tables(dictionary_root: Path, query: str | None = None, limit: int = 50) -> tuple[list[dict[str, object]], int]:
    normalized_query = (query or "").strip().upper()
    max_items = max(1, min(limit, 200))
    items: list[dict[str, object]] = []
    total = 0
    if not dictionary_root.exists():
        return [], 0

    for path in sorted(dictionary_root.glob("*.json")):
        table_name = path.stem.upper()
        try:
            definition = load_table_definition(dictionary_root, table_name)
        except (FileNotFoundError, AttributeError, KeyError, TypeError, json.JSONDecodeError):
            continue
        searchable = f"{definition.table_name} {definition.description}".upper()
        if normalized_query and normalized_query not in searchable:
            continue
        total += 1
        if len(items) >= max_items:
            continue
        classification = classify_table(definition.table_name)
        items.append(
            {
                "table_name": definition.table_name,
                "schema_name": definition.schema_name,
                "description": definition.description,
                "column_count": len(definition.columns),
                "data_category": classification.data_category,
                "is_transactional": classification.is_transactional,
                "allow_cutover": classification.allow_cutover,
                "allow_csvutil": classification.allow_csvutil,
            }
        )
    return items, total


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
    module_id: str | None = None,
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
        "module_id": module_id,
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
    {
        "code": "LOCATION",
        "name": "Location",
        "category": "MASTER_DATA",
        "description": "Location master data and address lines.",
        "default_load_order": 200,
        "default_method": "CSV",
        "method_options": ["CSV"],
        "allow_cutover": True,
        "allow_csvutil": True,
        "tables": [
            {"table_name": "LOCATION", "relationship_role": "PRIMARY", "is_primary_table": True},
            {"table_name": "LOCATION_ADDRESS", "relationship_role": "ADDRESS", "is_primary_table": False},
            {"table_name": "LOCATION_CAPACITY", "relationship_role": "CAPACITY", "is_primary_table": False},
            {"table_name": "LOCATION_ACTIVITY_TIME_DEF", "relationship_role": "ACTIVITY_TIME", "is_primary_table": False},
            {"table_name": "LOCATION_LOAD_UNLOAD_POINT", "relationship_role": "DOCK", "is_primary_table": False},
            {"table_name": "EQUIPMENT_GROUP_PROFILE", "relationship_role": "EQUIPMENT_RESTRICTION", "is_primary_table": False},
            {"table_name": "EQUIPMENT_GROUP_PROFILE_D", "relationship_role": "EQUIPMENT_RESTRICTION_DETAIL", "is_primary_table": False},
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


def serialize_macro_object_load_plan(db: Session, macro: OtmMacroObject) -> dict[str, object]:
    dependencies = macro_object_dependencies(db, macro)
    target_tables = macro_object_tables(db, macro)
    items: list[dict[str, object]] = []

    for dependency, depends_on in dependencies:
        dependency_tables = macro_object_tables(db, depends_on)
        items.append(
            {
                "macro_object_code": depends_on.code,
                "macro_object_name": depends_on.name,
                "dependency_role": "DEPENDENCY",
                "dependency_type": dependency.dependency_type,
                "is_required": dependency.is_required,
                "tables": [row.table_name for row in dependency_tables],
                "table_count": len(dependency_tables),
                "all_tables_validated": all(row.validated_by_datadict for row in dependency_tables),
            }
        )

    items.append(
        {
            "macro_object_code": macro.code,
            "macro_object_name": macro.name,
            "dependency_role": "TARGET",
            "dependency_type": "TARGET",
            "is_required": True,
            "tables": [row.table_name for row in target_tables],
            "table_count": len(target_tables),
            "all_tables_validated": all(row.validated_by_datadict for row in target_tables),
        }
    )
    return {
        "macro_object_code": macro.code,
        "items": items,
        "summary": {
            "step_count": len(items),
            "dependency_count": len(dependencies),
            "target_table_count": len(target_tables),
            "all_target_tables_validated": all(row.validated_by_datadict for row in target_tables),
        },
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
        tables = macro_object_tables(db, macro)
        dependencies = macro_object_dependencies(db, macro)
        validated_table_count = sum(1 for row in tables if row.validated_by_datadict)
        payload["tables"] = [serialize_macro_object_table(row) for row in tables]
        payload["dependencies"] = [
            serialize_macro_object_dependency(row, depends_on) for row, depends_on in dependencies
        ]
        payload["summary"] = {
            "table_count": len(tables),
            "dependency_count": len(dependencies),
            "validated_table_count": validated_table_count,
            "all_tables_validated": validated_table_count == len(tables),
            "csvutil_table_count": sum(1 for row in tables if row.allow_csvutil),
            "cutover_table_count": sum(1 for row in tables if row.allow_cutover),
        }
    return payload


def _json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _direct_children(element: ET.Element, child_name: str) -> list[ET.Element]:
    return [child for child in list(element) if _local_name(child.tag) == child_name]


def _first_direct_child(element: ET.Element, child_name: str) -> ET.Element | None:
    for child in list(element):
        if _local_name(child.tag) == child_name:
            return child
    return None


def _strip_prefix(value: str | None) -> str:
    if not value:
        return ""
    return value.split(":", 1)[-1]


def _documentation(element: ET.Element) -> str:
    annotation = _first_direct_child(element, "annotation")
    if annotation is None:
        return ""
    doc = _first_direct_child(annotation, "documentation")
    if doc is None or doc.text is None:
        return ""
    return " ".join(doc.text.split())


def _domain_area(root_name: str, file_name: str) -> str:
    upper_root = root_name.upper()
    upper_file = file_name.upper()
    if upper_root.startswith("RATE_") or upper_root == "X_LANE" or "RATE" in upper_file:
        return "RATE"
    if upper_root in {"RELEASE", "TRANSORDER", "ORDERMOVEMENT"} or "ORDER" in upper_file:
        return "ORDER"
    if "SHIPMENT" in upper_root or "SHIPMENT" in upper_file:
        return "SHIPMENT"
    if upper_root in {"LOCATION", "CONTACT", "CORPORATION"} or "LOCATION" in upper_file:
        return "MASTER_DATA"
    if upper_root in {"ITEM", "ITEMMASTER", "SKU"} or "ITEM" in upper_file:
        return "MASTER_DATA"
    if upper_root in {"TRANSMISSION", "TRANSMISSIONACK"} or "TRANSMISSION" in upper_file:
        return "TRANSMISSION"
    if upper_root in {"DBOBJECT", "XML2SQL", "SQL2XML", "TRANSACTION_SET"} or "DBXML" in upper_file:
        return "DBXML"
    return "OTHER"


def _root_type(root_name: str) -> str:
    upper = root_name.upper()
    if upper == "TRANSMISSION":
        return "ENVELOPE"
    if upper in {"DBOBJECT", "XML2SQL", "SQL2XML", "TRANSACTION_SET"}:
        return "DBXML"
    if upper.startswith("RATE_") or upper == "X_LANE":
        return "ROWSET"
    return "DOMAIN_ROOT"


def _envelope_role(root_name: str) -> str:
    upper = root_name.upper()
    if upper == "TRANSMISSION":
        return "TRANSMISSION"
    if upper in {"DBOBJECT", "XML2SQL", "SQL2XML", "TRANSACTION_SET"}:
        return "DBXML"
    return "NONE"


def _recommended_modules(root_name: str, file_name: str) -> list[str]:
    area = _domain_area(root_name, file_name)
    upper = root_name.upper()
    if area == "RATE":
        return ["rates"]
    if upper == "RELEASE":
        return ["order_release_generator", "integration_mapping"]
    if area == "SHIPMENT" or upper == "TRANSMISSION":
        return ["integration_mapping"]
    if area == "MASTER_DATA":
        return ["master_data"]
    if area == "DBXML":
        return ["cutover", "assets", "evidence"]
    return []


def _assert_client_safe_schema_content(file_path: Path) -> None:
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    if any(pattern.search(content) for pattern in SENSITIVE_SCHEMA_PATTERNS):
        raise SensitiveSchemaContentError("Schema pack file contains blocked sensitive content.")


def _iter_xsd_nested_elements(element: ET.Element) -> list[ET.Element]:
    nested: list[ET.Element] = []
    for child in list(element):
        name = _local_name(child.tag)
        if name == "element":
            nested.append(child)
        elif name in {"complexType", "sequence", "choice", "complexContent", "extension"}:
            nested.extend(_iter_xsd_nested_elements(child))
    return nested


def _schema_paths_for_root(schema: ET.Element, root_element: ET.Element, file_name: str) -> list[dict[str, object]]:
    complex_types = {
        child.attrib["name"]: child
        for child in _direct_children(schema, "complexType")
        if child.attrib.get("name")
    }
    root_name = str(root_element.attrib["name"])
    rows: list[dict[str, object]] = [
        {
            "parent_path": None,
            "path": f"/{root_name}",
            "node_name": root_name,
            "data_type": _strip_prefix(root_element.attrib.get("type")) or None,
            "min_occurs": root_element.attrib.get("minOccurs", "1"),
            "max_occurs": root_element.attrib.get("maxOccurs", "1"),
            "is_required": root_element.attrib.get("minOccurs", "1") != "0",
            "is_repeatable": root_element.attrib.get("maxOccurs", "1") not in {"0", "1"},
            "documentation": _documentation(root_element),
            "source_file": file_name,
        }
    ]

    def add_children(parent: ET.Element, parent_path: str, visited_types: set[str]) -> None:
        child_source = _first_direct_child(parent, "complexType")
        named_type = _strip_prefix(parent.attrib.get("type"))
        if child_source is None and named_type in complex_types and named_type not in visited_types:
            child_source = complex_types[named_type]
            visited_types = {*visited_types, named_type}
        if child_source is None:
            return
        for child in _iter_xsd_nested_elements(child_source):
            child_name = child.attrib.get("name")
            if not child_name:
                continue
            path = f"{parent_path}/{child_name}"
            max_occurs = child.attrib.get("maxOccurs", "1")
            rows.append(
                {
                    "parent_path": parent_path,
                    "path": path,
                    "node_name": child_name,
                    "data_type": _strip_prefix(child.attrib.get("type")) or None,
                    "min_occurs": child.attrib.get("minOccurs", "1"),
                    "max_occurs": max_occurs,
                    "is_required": child.attrib.get("minOccurs", "1") != "0",
                    "is_repeatable": max_occurs not in {"0", "1"},
                    "documentation": _documentation(child),
                    "source_file": file_name,
                }
            )
            add_children(child, path, visited_types)

    add_children(root_element, f"/{root_name}", set())
    return rows


def create_schema_pack(
    db: Session,
    *,
    code: str,
    name: str,
    otm_version: str,
    source_type: str,
    source_path: str,
    content_hash: str,
    created_by: str | None = None,
    asset_id: str | None = None,
) -> SchemaPack:
    pack = SchemaPack(
        code=code.upper(),
        name=name,
        otm_version=otm_version.upper(),
        source_type=source_type.upper(),
        source_path=source_path,
        content_hash=content_hash,
        asset_id=asset_id,
        created_by=created_by,
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)
    return pack


def list_schema_packs(
    db: Session,
    *,
    otm_version: str | None = None,
    status: str | None = None,
) -> list[SchemaPack]:
    query = db.query(SchemaPack)
    if otm_version:
        query = query.filter(SchemaPack.otm_version == otm_version.upper())
    if status:
        query = query.filter(SchemaPack.status == status.upper())
    return query.order_by(SchemaPack.otm_version, SchemaPack.code).all()


def get_schema_pack(db: Session, schema_pack_id: str) -> SchemaPack | None:
    return db.get(SchemaPack, schema_pack_id)


def serialize_schema_pack(pack: SchemaPack) -> dict[str, object]:
    return {
        "id": pack.id,
        "code": pack.code,
        "name": pack.name,
        "otm_version": pack.otm_version,
        "source_type": pack.source_type,
        "asset_id": pack.asset_id,
        "status": pack.status,
        "namespace_count": pack.namespace_count,
        "root_count": pack.root_count,
        "operation_count": pack.operation_count,
        "content_hash": pack.content_hash,
        "created_by": pack.created_by,
        "created_at": pack.created_at.isoformat() if pack.created_at else None,
        "updated_at": pack.updated_at.isoformat() if pack.updated_at else None,
    }


def list_schema_roots(
    db: Session,
    *,
    schema_pack_id: str | None = None,
    root_name: str | None = None,
    domain_area: str | None = None,
    recommended_module: str | None = None,
) -> list[SchemaRoot]:
    query = db.query(SchemaRoot)
    if schema_pack_id:
        query = query.filter(SchemaRoot.schema_pack_id == schema_pack_id)
    if root_name:
        query = query.filter(SchemaRoot.root_name == root_name)
    if domain_area:
        query = query.filter(SchemaRoot.domain_area == domain_area.upper())
    roots = query.order_by(SchemaRoot.domain_area, SchemaRoot.root_name).all()
    if recommended_module:
        module = recommended_module.lower()
        roots = [root for root in roots if module in [item.lower() for item in _json_list(root.recommended_modules_json)]]
    return roots


def get_schema_root(db: Session, schema_root_id: str) -> SchemaRoot | None:
    return db.get(SchemaRoot, schema_root_id)


def serialize_schema_root(root: SchemaRoot) -> dict[str, object]:
    return {
        "id": root.id,
        "schema_pack_id": root.schema_pack_id,
        "schema_file_id": root.schema_file_id,
        "root_name": root.root_name,
        "namespace": root.namespace,
        "domain_area": root.domain_area,
        "root_type": root.root_type,
        "envelope_role": root.envelope_role,
        "recommended_modules": _json_list(root.recommended_modules_json),
        "documentation": root.documentation,
    }


def list_schema_paths(
    db: Session,
    *,
    schema_root_id: str,
    query_text: str | None = None,
) -> list[SchemaPath]:
    query = db.query(SchemaPath).filter(SchemaPath.schema_root_id == schema_root_id)
    if query_text:
        like = f"%{query_text}%"
        query = query.filter(SchemaPath.path.like(like))
    return query.order_by(SchemaPath.sequence_index, SchemaPath.path).all()


def serialize_schema_path(path: SchemaPath) -> dict[str, object]:
    return {
        "id": path.id,
        "schema_root_id": path.schema_root_id,
        "parent_path": path.parent_path,
        "path": path.path,
        "node_name": path.node_name,
        "data_type": path.data_type,
        "min_occurs": path.min_occurs,
        "max_occurs": path.max_occurs,
        "is_required": path.is_required,
        "is_repeatable": path.is_repeatable,
        "documentation": path.documentation,
        "source_file": path.source_file,
        "sequence_index": path.sequence_index,
    }


def list_service_operations(
    db: Session,
    *,
    schema_pack_id: str | None = None,
    service_name: str | None = None,
) -> list[ServiceOperation]:
    query = db.query(ServiceOperation)
    if schema_pack_id:
        query = query.filter(ServiceOperation.schema_pack_id == schema_pack_id)
    if service_name:
        query = query.filter(ServiceOperation.service_name == service_name)
    return query.order_by(ServiceOperation.service_name, ServiceOperation.operation_name).all()


def serialize_service_operation(operation: ServiceOperation) -> dict[str, object]:
    return {
        "id": operation.id,
        "schema_pack_id": operation.schema_pack_id,
        "schema_file_id": operation.schema_file_id,
        "service_name": operation.service_name,
        "operation_name": operation.operation_name,
        "input_message": operation.input_message,
        "output_message": operation.output_message,
        "fault_message": operation.fault_message,
        "target_namespace": operation.target_namespace,
        "related_roots": _json_list(operation.related_roots_json),
    }


def list_macro_object_schema_links(db: Session, macro_object_code: str) -> list[tuple[MacroObjectSchemaLink, SchemaRoot, SchemaPack, SchemaFile]]:
    return (
        db.query(MacroObjectSchemaLink, SchemaRoot, SchemaPack, SchemaFile)
        .join(SchemaRoot, MacroObjectSchemaLink.schema_root_id == SchemaRoot.id)
        .join(SchemaPack, SchemaRoot.schema_pack_id == SchemaPack.id)
        .join(SchemaFile, SchemaRoot.schema_file_id == SchemaFile.id)
        .filter(MacroObjectSchemaLink.macro_object_code == macro_object_code.upper())
        .order_by(MacroObjectSchemaLink.confidence, SchemaRoot.root_name)
        .all()
    )


def serialize_macro_object_schema_link(
    row: MacroObjectSchemaLink,
    root: SchemaRoot,
    pack: SchemaPack,
    schema_file: SchemaFile,
) -> dict[str, object]:
    return {
        "id": row.id,
        "macro_object_code": row.macro_object_code,
        "schema_root_id": root.id,
        "schema_pack_id": pack.id,
        "schema_pack_code": pack.code,
        "otm_version": pack.otm_version,
        "schema_file": schema_file.file_name,
        "root_name": root.root_name,
        "domain_area": root.domain_area,
        "root_type": root.root_type,
        "relationship_role": row.relationship_role,
        "confidence": row.confidence,
        "notes": row.notes,
    }


def _clear_schema_pack_index(db: Session, pack: SchemaPack) -> None:
    root_ids = [row.id for row in db.query(SchemaRoot).filter(SchemaRoot.schema_pack_id == pack.id).all()]
    file_ids = [row.id for row in db.query(SchemaFile).filter(SchemaFile.schema_pack_id == pack.id).all()]
    if root_ids:
        db.query(MacroObjectSchemaLink).filter(MacroObjectSchemaLink.schema_root_id.in_(root_ids)).delete(
            synchronize_session=False
        )
        db.query(SchemaPath).filter(SchemaPath.schema_root_id.in_(root_ids)).delete(synchronize_session=False)
    db.query(ServiceOperation).filter(ServiceOperation.schema_pack_id == pack.id).delete(synchronize_session=False)
    if root_ids:
        db.query(SchemaRoot).filter(SchemaRoot.id.in_(root_ids)).delete(synchronize_session=False)
    if file_ids:
        db.query(SchemaFile).filter(SchemaFile.id.in_(file_ids)).delete(synchronize_session=False)


def _index_xsd_file(db: Session, pack: SchemaPack, file_path: Path, source_root: Path) -> dict[str, int]:
    tree = ET.parse(file_path)
    schema = tree.getroot()
    target_namespace = schema.attrib.get("targetNamespace", "")
    imports = _direct_children(schema, "import") + _direct_children(schema, "include")
    top_level_elements = [element for element in _direct_children(schema, "element") if element.attrib.get("name")]
    complex_types = _direct_children(schema, "complexType")
    schema_file = SchemaFile(
        schema_pack_id=pack.id,
        file_name=file_path.name,
        relative_path=str(file_path.relative_to(source_root)),
        file_type="XSD",
        namespace=target_namespace,
        import_count=len(imports),
        top_level_element_count=len(top_level_elements),
        complex_type_count=len(complex_types),
        status="PARSED",
    )
    db.add(schema_file)
    db.flush()

    paths_created = 0
    for element in top_level_elements:
        root_name = str(element.attrib["name"])
        root = SchemaRoot(
            schema_pack_id=pack.id,
            schema_file_id=schema_file.id,
            root_name=root_name,
            namespace=target_namespace,
            domain_area=_domain_area(root_name, file_path.name),
            root_type=_root_type(root_name),
            envelope_role=_envelope_role(root_name),
            recommended_modules_json=json.dumps(_recommended_modules(root_name, file_path.name), sort_keys=True),
            documentation=_documentation(element),
        )
        db.add(root)
        db.flush()
        for index, path_payload in enumerate(_schema_paths_for_root(schema, element, file_path.name), start=1):
            db.add(
                SchemaPath(
                    schema_root_id=root.id,
                    sequence_index=index,
                    **path_payload,
                )
            )
            paths_created += 1

    return {
        "files_parsed": 1,
        "roots_created": len(top_level_elements),
        "paths_created": paths_created,
        "operations_created": 0,
    }


def _index_wsdl_file(db: Session, pack: SchemaPack, file_path: Path, source_root: Path) -> dict[str, int]:
    tree = ET.parse(file_path)
    definitions = tree.getroot()
    target_namespace = definitions.attrib.get("targetNamespace", "")
    service = _first_direct_child(definitions, "service")
    service_name = service.attrib.get("name", file_path.stem) if service is not None else file_path.stem
    operations = []
    for port_type in _direct_children(definitions, "portType"):
        operations.extend(_direct_children(port_type, "operation"))
    schema_file = SchemaFile(
        schema_pack_id=pack.id,
        file_name=file_path.name,
        relative_path=str(file_path.relative_to(source_root)),
        file_type="WSDL",
        namespace=target_namespace,
        import_count=len(_direct_children(definitions, "import")),
        top_level_element_count=0,
        complex_type_count=0,
        status="PARSED",
    )
    db.add(schema_file)
    db.flush()

    for operation in operations:
        input_node = _first_direct_child(operation, "input")
        output_node = _first_direct_child(operation, "output")
        fault_node = _first_direct_child(operation, "fault")
        db.add(
            ServiceOperation(
                schema_pack_id=pack.id,
                schema_file_id=schema_file.id,
                service_name=service_name,
                operation_name=operation.attrib.get("name", ""),
                input_message=_strip_prefix(input_node.attrib.get("message")) if input_node is not None else "",
                output_message=_strip_prefix(output_node.attrib.get("message")) if output_node is not None else "",
                fault_message=_strip_prefix(fault_node.attrib.get("message")) if fault_node is not None else "",
                target_namespace=target_namespace,
                related_roots_json="[]",
            )
        )

    return {
        "files_parsed": 1,
        "roots_created": 0,
        "paths_created": 0,
        "operations_created": len(operations),
    }


def index_schema_pack(db: Session, pack: SchemaPack, *, created_by: str | None = None) -> dict[str, object]:
    source_root = Path(pack.source_path)
    if pack.source_type != "LOCAL_FOLDER" or not source_root.exists() or not source_root.is_dir():
        raise FileNotFoundError("Schema pack source folder was not found.")

    _clear_schema_pack_index(db, pack)
    pack.status = "INDEXING"
    db.flush()

    totals = {
        "files_seen": 0,
        "files_parsed": 0,
        "files_failed": 0,
        "roots_created": 0,
        "paths_created": 0,
        "operations_created": 0,
    }
    namespaces: set[str] = set()
    hasher = sha256()
    for file_path in sorted([*source_root.rglob("*.xsd"), *source_root.rglob("*.wsdl")]):
        totals["files_seen"] += 1
        _assert_client_safe_schema_content(file_path)
        hasher.update(file_path.name.encode("utf-8"))
        hasher.update(file_path.read_bytes())
        try:
            if file_path.suffix.lower() == ".xsd":
                result = _index_xsd_file(db, pack, file_path, source_root)
            else:
                result = _index_wsdl_file(db, pack, file_path, source_root)
        except ET.ParseError as exc:
            db.add(
                SchemaFile(
                    schema_pack_id=pack.id,
                    file_name=file_path.name,
                    relative_path=str(file_path.relative_to(source_root)),
                    file_type=file_path.suffix.upper().lstrip(".") or "OTHER",
                    status="FAILED",
                    parse_error=str(exc),
                )
            )
            totals["files_failed"] += 1
            continue
        totals["files_parsed"] += int(result["files_parsed"])
        totals["roots_created"] += int(result["roots_created"])
        totals["paths_created"] += int(result["paths_created"])
        totals["operations_created"] += int(result["operations_created"])

    for schema_file in db.query(SchemaFile).filter(SchemaFile.schema_pack_id == pack.id).all():
        if schema_file.namespace:
            namespaces.add(schema_file.namespace)

    pack.status = "READY" if totals["files_failed"] == 0 else "FAILED"
    pack.namespace_count = len(namespaces)
    pack.root_count = int(totals["roots_created"])
    pack.operation_count = int(totals["operations_created"])
    pack.content_hash = hasher.hexdigest() if totals["files_seen"] else pack.content_hash

    summary = {
        "schema_pack_id": pack.id,
        "schema_pack_code": pack.code,
        "otm_version": pack.otm_version,
        "content_hash": pack.content_hash,
        "status": pack.status,
        **totals,
    }
    evidence = Evidence(
        source_module="catalog",
        evidence_type="schema_pack_index",
        status=pack.status,
        summary_json=json.dumps(summary, sort_keys=True),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.commit()
    db.refresh(pack)
    db.refresh(evidence)
    return {
        **summary,
        "evidence_id": evidence.id,
        "created_by": created_by,
    }
