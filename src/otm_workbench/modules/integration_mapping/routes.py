from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import IntegrationDefinition, IntegrationEndpoint, IntegrationSystem, User
from otm_workbench.modules.integration_mapping.definitions import (
    create_integration_definition,
    serialize_integration_definition,
)
from otm_workbench.modules.integration_mapping.systems import (
    create_integration_endpoint,
    create_integration_system,
    serialize_integration_endpoint,
    serialize_integration_system,
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


class IntegrationSystemCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str
    name: str
    system_type: str
    base_url: str = ""
    description: str = ""


class IntegrationEndpointCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    system_id: str | None = None
    code: str
    name: str
    path: str
    method: str
    payload_format: str
    description: str = ""


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


@router.post("/systems")
def create_system(
    payload: IntegrationSystemCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    try:
        system = create_integration_system(db, payload=payload.model_dump(), user=user)
    except IntegrityError as exc:
        db.rollback()
        raise api_error(409, "INTEGRATION_SYSTEM_CODE_EXISTS", "Integration system code already exists.") from exc
    except ValueError as exc:
        raise api_error(400, "INTEGRATION_SECRET_RISK", str(exc)) from exc
    return serialize_integration_system(system)


@router.get("/systems")
def list_systems(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    systems = db.query(IntegrationSystem).order_by(IntegrationSystem.created_at.desc()).all()
    items = [serialize_integration_system(system) for system in systems]
    return PageResponse(items=items, total=len(items))


@router.post("/systems/{system_id}/endpoints")
def create_endpoint(
    system_id: str,
    payload: IntegrationEndpointCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    system = db.get(IntegrationSystem, system_id)
    if system is None:
        raise api_error(404, "INTEGRATION_SYSTEM_NOT_FOUND", "Integration system not found.")
    try:
        endpoint = create_integration_endpoint(db, system=system, payload=payload.model_dump(), user=user)
    except ValueError as exc:
        raise api_error(400, "INTEGRATION_SECRET_RISK", str(exc)) from exc
    return serialize_integration_endpoint(endpoint)


@router.get("/systems/{system_id}/endpoints")
def list_endpoints(
    system_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    system = db.get(IntegrationSystem, system_id)
    if system is None:
        raise api_error(404, "INTEGRATION_SYSTEM_NOT_FOUND", "Integration system not found.")
    endpoints = (
        db.query(IntegrationEndpoint)
        .filter(IntegrationEndpoint.system_id == system.id)
        .order_by(IntegrationEndpoint.created_at.desc())
        .all()
    )
    items = [serialize_integration_endpoint(endpoint) for endpoint in endpoints]
    return PageResponse(items=items, total=len(items))
