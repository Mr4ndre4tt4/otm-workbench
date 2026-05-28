import json
import re

from sqlalchemy.orm import Session

from otm_workbench.models import OrderReleaseTemplate, SchemaRoot


SYNTHETIC_TL_TEMPLATE = {
    "code": "TL_ORDER_RELEASE_MVP0",
    "name": "Synthetic TL Order Release",
    "version": 1,
    "status": "ACTIVE",
    "macro_object_code": "ORDER_RELEASE",
    "description": "Client-safe synthetic template for TL Order Release XML generation tests.",
    "required_columns": [
        "release_gid",
        "source_location_gid",
        "destination_location_gid",
        "early_pickup_date",
        "late_delivery_date",
        "item_gid",
        "packaged_item_gid",
        "weight",
        "weight_uom",
    ],
    "optional_columns": [
        "transport_mode",
        "service_provider_gid",
        "refnum_qualifier",
        "refnum_value",
        "remarks",
    ],
    "defaults": {
        "domain_name": "OTM1",
        "release_method": "ONE_TO_ONE",
        "transport_mode": "TL",
    },
}

TEMPLATE_CODE_PATTERN = re.compile(r"^[A-Z0-9_]+$")


class UnknownOrderReleaseSchemaRoot(ValueError):
    def __init__(self, *, field: str, schema_root_id: str) -> None:
        self.field = field
        self.schema_root_id = schema_root_id
        super().__init__(f"{field} references an unknown schema root.")


def normalize_columns(columns: list[str]) -> list[str]:
    normalized: list[str] = []
    for column in columns:
        value = str(column).strip()
        if value:
            normalized.append(value)
    return normalized


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates


def normalize_schema_root_id(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def require_schema_root(db: Session, *, schema_root_id: str | None, field: str) -> None:
    if schema_root_id is None:
        return
    if db.get(SchemaRoot, schema_root_id) is None:
        raise UnknownOrderReleaseSchemaRoot(field=field, schema_root_id=schema_root_id)


def validate_template_contract(
    *,
    code: str,
    name: str,
    required_columns: list[str],
    optional_columns: list[str],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    if not TEMPLATE_CODE_PATTERN.fullmatch(code):
        issues.append({"code": "INVALID_TEMPLATE_CODE", "field": "code", "severity": "ERROR"})
    if not name:
        issues.append({"code": "MISSING_TEMPLATE_NAME", "field": "name", "severity": "ERROR"})
    if not required_columns:
        issues.append({"code": "MISSING_REQUIRED_COLUMNS", "field": "required_columns", "severity": "ERROR"})
    if "release_gid" not in required_columns:
        issues.append({"code": "MISSING_RELEASE_GID", "field": "required_columns", "severity": "ERROR"})
    for column in duplicate_values(required_columns):
        issues.append({"code": "DUPLICATE_REQUIRED_COLUMN", "field": "required_columns", "column": column, "severity": "ERROR"})
    for column in duplicate_values(optional_columns):
        issues.append({"code": "DUPLICATE_OPTIONAL_COLUMN", "field": "optional_columns", "column": column, "severity": "ERROR"})
    overlap = sorted(set(required_columns).intersection(optional_columns))
    for column in overlap:
        issues.append({"code": "COLUMN_IN_REQUIRED_AND_OPTIONAL", "field": "columns", "column": column, "severity": "ERROR"})
    return issues


def seed_order_release_templates(db: Session) -> None:
    existing = db.query(OrderReleaseTemplate).filter(OrderReleaseTemplate.code == SYNTHETIC_TL_TEMPLATE["code"]).first()
    if existing is not None:
        return
    db.add(
        OrderReleaseTemplate(
            domain_name="PUBLIC",
            code=str(SYNTHETIC_TL_TEMPLATE["code"]),
            name=str(SYNTHETIC_TL_TEMPLATE["name"]),
            version=int(SYNTHETIC_TL_TEMPLATE["version"]),
            status=str(SYNTHETIC_TL_TEMPLATE["status"]),
            macro_object_code=str(SYNTHETIC_TL_TEMPLATE["macro_object_code"]),
            description=str(SYNTHETIC_TL_TEMPLATE["description"]),
            required_columns_json=json.dumps(SYNTHETIC_TL_TEMPLATE["required_columns"], sort_keys=True),
            optional_columns_json=json.dumps(SYNTHETIC_TL_TEMPLATE["optional_columns"], sort_keys=True),
            defaults_json=json.dumps(SYNTHETIC_TL_TEMPLATE["defaults"], sort_keys=True),
            created_by="system",
        )
    )
    db.commit()


def create_order_release_template(
    db: Session,
    *,
    code: str,
    name: str,
    description: str,
    required_columns: list[str],
    optional_columns: list[str],
    defaults: dict[str, object],
    created_by: str,
    transmission_schema_root_id: str | None = None,
    release_schema_root_id: str | None = None,
    scope: dict[str, object] | None = None,
) -> tuple[OrderReleaseTemplate | None, list[dict[str, object]]]:
    normalized_code = code.strip().upper()
    normalized_name = name.strip()
    normalized_required = normalize_columns(required_columns)
    normalized_optional = normalize_columns(optional_columns)
    issues = validate_template_contract(
        code=normalized_code,
        name=normalized_name,
        required_columns=normalized_required,
        optional_columns=normalized_optional,
    )
    if db.query(OrderReleaseTemplate).filter(OrderReleaseTemplate.code == normalized_code).first() is not None:
        issues.append({"code": "TEMPLATE_CODE_ALREADY_EXISTS", "field": "code", "severity": "ERROR"})
    if issues:
        return None, issues
    normalized_transmission_schema_root_id = normalize_schema_root_id(transmission_schema_root_id)
    normalized_release_schema_root_id = normalize_schema_root_id(release_schema_root_id)
    require_schema_root(
        db,
        schema_root_id=normalized_transmission_schema_root_id,
        field="transmission_schema_root_id",
    )
    require_schema_root(db, schema_root_id=normalized_release_schema_root_id, field="release_schema_root_id")

    template = OrderReleaseTemplate(
        project_id=str(scope.get("project_id") or "").strip() or None if scope else None,
        environment_id=str(scope.get("environment_id") or "").strip() or None if scope else None,
        profile_id=str(scope.get("profile_id") or "").strip() or None if scope else None,
        domain_name=str(scope.get("domain_name") or "").strip().upper() or None if scope else None,
        code=normalized_code,
        name=normalized_name,
        version=1,
        status="ACTIVE",
        macro_object_code="ORDER_RELEASE",
        description=description.strip(),
        required_columns_json=json.dumps(normalized_required, sort_keys=True),
        optional_columns_json=json.dumps(normalized_optional, sort_keys=True),
        defaults_json=json.dumps(defaults, sort_keys=True),
        transmission_schema_root_id=normalized_transmission_schema_root_id,
        release_schema_root_id=normalized_release_schema_root_id,
        created_by=created_by,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template, []


def create_order_release_template_version(
    db: Session,
    *,
    source_template: OrderReleaseTemplate,
    name: str,
    description: str,
    required_columns: list[str],
    optional_columns: list[str],
    defaults: dict[str, object],
    created_by: str,
    transmission_schema_root_id: str | None = None,
    release_schema_root_id: str | None = None,
) -> tuple[OrderReleaseTemplate | None, list[dict[str, object]]]:
    normalized_name = name.strip()
    normalized_required = normalize_columns(required_columns)
    normalized_optional = normalize_columns(optional_columns)
    issues = validate_template_contract(
        code=source_template.code,
        name=normalized_name,
        required_columns=normalized_required,
        optional_columns=normalized_optional,
    )
    if issues:
        return None, issues
    normalized_transmission_schema_root_id = normalize_schema_root_id(
        transmission_schema_root_id if transmission_schema_root_id is not None else source_template.transmission_schema_root_id
    )
    normalized_release_schema_root_id = normalize_schema_root_id(
        release_schema_root_id if release_schema_root_id is not None else source_template.release_schema_root_id
    )
    require_schema_root(
        db,
        schema_root_id=normalized_transmission_schema_root_id,
        field="transmission_schema_root_id",
    )
    require_schema_root(db, schema_root_id=normalized_release_schema_root_id, field="release_schema_root_id")

    latest_version = (
        db.query(OrderReleaseTemplate.version)
        .filter(OrderReleaseTemplate.code == source_template.code)
        .order_by(OrderReleaseTemplate.version.desc())
        .first()
    )
    next_version = int(latest_version[0] if latest_version else source_template.version) + 1
    template = OrderReleaseTemplate(
        project_id=source_template.project_id,
        environment_id=source_template.environment_id,
        profile_id=source_template.profile_id,
        domain_name=source_template.domain_name,
        code=source_template.code,
        name=normalized_name,
        version=next_version,
        status="ACTIVE",
        macro_object_code=source_template.macro_object_code,
        description=description.strip(),
        required_columns_json=json.dumps(normalized_required, sort_keys=True),
        optional_columns_json=json.dumps(normalized_optional, sort_keys=True),
        defaults_json=json.dumps(defaults, sort_keys=True),
        transmission_schema_root_id=normalized_transmission_schema_root_id,
        release_schema_root_id=normalized_release_schema_root_id,
        created_by=created_by,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template, []


def parse_json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def parse_json_object(value: str) -> dict[str, object]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def serialize_order_release_template(template: OrderReleaseTemplate) -> dict[str, object]:
    return {
        "id": template.id,
        "project_id": template.project_id,
        "environment_id": template.environment_id,
        "profile_id": template.profile_id,
        "domain_name": template.domain_name,
        "code": template.code,
        "name": template.name,
        "version": template.version,
        "status": template.status,
        "macro_object_code": template.macro_object_code,
        "description": template.description,
        "required_columns": parse_json_list(template.required_columns_json),
        "optional_columns": parse_json_list(template.optional_columns_json),
        "defaults": parse_json_object(template.defaults_json),
        "transmission_schema_root_id": template.transmission_schema_root_id,
        "release_schema_root_id": template.release_schema_root_id,
        "created_by": template.created_by,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }
