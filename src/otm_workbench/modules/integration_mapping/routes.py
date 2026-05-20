from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import IntegrationDefinition, User
from otm_workbench.modules.integration_mapping.definitions import (
    create_integration_definition,
    serialize_integration_definition,
)


router = APIRouter(prefix="/api/v1/modules/integration-mapping", tags=["integration-mapping"])


class IntegrationDefinitionCreateRequest(BaseModel):
    code: str
    name: str
    description: str = ""
    source_system: str
    target_system: str
    source_format: str
    target_format: str
    status: str | None = None


@router.get("/health")
def integration_mapping_health(user: User = Depends(require_user)):
    return {
        "status": "ok",
        "module": "integration_mapping",
        "mode": "specification_first",
    }


@router.post("/definitions")
def create_definition(
    payload: IntegrationDefinitionCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    try:
        definition = create_integration_definition(db, payload=payload.model_dump(), user=user)
    except IntegrityError as exc:
        db.rollback()
        raise api_error(
            409,
            "INTEGRATION_DEFINITION_CODE_EXISTS",
            "Integration definition code already exists.",
        ) from exc
    return serialize_integration_definition(definition)


@router.get("/definitions")
def list_definitions(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definitions = db.query(IntegrationDefinition).order_by(IntegrationDefinition.created_at.desc()).all()
    items = [serialize_integration_definition(definition) for definition in definitions]
    return PageResponse(items=items, total=len(items))


@router.get("/definitions/{definition_id}")
def get_definition(
    definition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    definition = db.get(IntegrationDefinition, definition_id)
    if definition is None:
        raise api_error(404, "INTEGRATION_DEFINITION_NOT_FOUND", "Integration definition not found.")
    return serialize_integration_definition(definition)
