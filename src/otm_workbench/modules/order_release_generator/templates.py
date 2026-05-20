import json

from sqlalchemy.orm import Session

from otm_workbench.models import OrderReleaseTemplate


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


def seed_order_release_templates(db: Session) -> None:
    existing = db.query(OrderReleaseTemplate).filter(OrderReleaseTemplate.code == SYNTHETIC_TL_TEMPLATE["code"]).first()
    if existing is not None:
        return
    db.add(
        OrderReleaseTemplate(
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
        "code": template.code,
        "name": template.name,
        "version": template.version,
        "status": template.status,
        "macro_object_code": template.macro_object_code,
        "description": template.description,
        "required_columns": parse_json_list(template.required_columns_json),
        "optional_columns": parse_json_list(template.optional_columns_json),
        "defaults": parse_json_object(template.defaults_json),
        "created_by": template.created_by,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }
