from sqlalchemy.orm import Session

from otm_workbench.models import IntegrationTransformType


TRANSFORM_TYPE_SEEDS = (
    {
        "code": "DIRECT",
        "name": "Direct copy",
        "description": "Copy source value to target path without expression metadata.",
        "requires_expression": False,
        "sequence_index": 10,
    },
    {
        "code": "CONSTANT",
        "name": "Constant value",
        "description": "Use a controlled constant value as mapping metadata.",
        "requires_expression": True,
        "sequence_index": 20,
    },
    {
        "code": "CONCAT",
        "name": "Concatenate",
        "description": "Join values through a future expression model.",
        "requires_expression": True,
        "sequence_index": 30,
    },
    {
        "code": "DATE_FORMAT",
        "name": "Date format",
        "description": "Declare date format conversion metadata without executing transformation.",
        "requires_expression": True,
        "sequence_index": 40,
    },
)


def seed_integration_transform_types(db: Session) -> None:
    for seed in TRANSFORM_TYPE_SEEDS:
        existing = db.query(IntegrationTransformType).filter(IntegrationTransformType.code == seed["code"]).first()
        if existing:
            existing.name = str(seed["name"])
            existing.description = str(seed["description"])
            existing.requires_expression = bool(seed["requires_expression"])
            existing.sequence_index = int(seed["sequence_index"])
            existing.status = "ACTIVE"
            existing.system_seeded = True
            continue
        db.add(
            IntegrationTransformType(
                code=str(seed["code"]),
                name=str(seed["name"]),
                description=str(seed["description"]),
                requires_expression=bool(seed["requires_expression"]),
                sequence_index=int(seed["sequence_index"]),
                status="ACTIVE",
                system_seeded=True,
            )
        )
    db.commit()


def normalize_transform_type_code(value: object) -> str:
    return str(value or "DIRECT").strip().upper()


def transform_type_is_active(db: Session, code: str) -> bool:
    seed_integration_transform_types(db)
    return (
        db.query(IntegrationTransformType)
        .filter(
            IntegrationTransformType.code == code,
            IntegrationTransformType.status == "ACTIVE",
        )
        .first()
        is not None
    )


def list_active_transform_types(db: Session) -> list[IntegrationTransformType]:
    seed_integration_transform_types(db)
    return (
        db.query(IntegrationTransformType)
        .filter(IntegrationTransformType.status == "ACTIVE")
        .order_by(IntegrationTransformType.sequence_index, IntegrationTransformType.code)
        .all()
    )


def serialize_transform_type(transform_type: IntegrationTransformType) -> dict[str, object]:
    return {
        "id": transform_type.id,
        "code": transform_type.code,
        "name": transform_type.name,
        "description": transform_type.description,
        "requires_expression": transform_type.requires_expression,
        "status": transform_type.status,
        "sequence_index": transform_type.sequence_index,
        "system_seeded": transform_type.system_seeded,
        "created_at": transform_type.created_at.isoformat() if transform_type.created_at else None,
        "updated_at": transform_type.updated_at.isoformat() if transform_type.updated_at else None,
    }
