import json

from sqlalchemy.orm import Session

from otm_workbench.models import MasterDataTemplate


REGIONS_BASIC_TEMPLATE = {
    "code": "REGIONS_BASIC",
    "name": "Regions Basic",
    "version": 1,
    "status": "PUBLISHED",
    "catalog_macro_object_code": "REGION",
    "data_category": "MASTER_DATA",
    "target_tables": ["REGION", "REGION_DETAIL"],
    "description": "Synthetic starter template for region master data.",
}


def seed_master_data_templates(db: Session) -> None:
    exists = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == REGIONS_BASIC_TEMPLATE["code"]).first()
    if exists:
        return
    db.add(
        MasterDataTemplate(
            code=REGIONS_BASIC_TEMPLATE["code"],
            name=REGIONS_BASIC_TEMPLATE["name"],
            version=REGIONS_BASIC_TEMPLATE["version"],
            status=REGIONS_BASIC_TEMPLATE["status"],
            catalog_macro_object_code=REGIONS_BASIC_TEMPLATE["catalog_macro_object_code"],
            data_category=REGIONS_BASIC_TEMPLATE["data_category"],
            target_tables_json=json.dumps(REGIONS_BASIC_TEMPLATE["target_tables"]),
            description=REGIONS_BASIC_TEMPLATE["description"],
        )
    )
    db.commit()


def serialize_master_data_template(template: MasterDataTemplate) -> dict[str, object]:
    return {
        "id": template.id,
        "code": template.code,
        "name": template.name,
        "version": template.version,
        "status": template.status,
        "catalog_macro_object_code": template.catalog_macro_object_code,
        "data_category": template.data_category,
        "target_tables": json.loads(template.target_tables_json),
        "description": template.description,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }
