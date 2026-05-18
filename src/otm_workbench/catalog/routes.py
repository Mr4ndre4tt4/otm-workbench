from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import User
from otm_workbench.catalog.services import (
    reference_options_payload,
    safe_load_table,
    serialize_columns,
    serialize_table_definition,
    validate_column,
    validate_table,
)

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


class ValidateTableRequest(BaseModel):
    table_name: str
    usage: str | None = None


class ValidateColumnRequest(BaseModel):
    table_name: str
    column_name: str


def dictionary_root() -> Path:
    return Path(get_settings().otm_data_dictionary_root)


@router.get("/health")
def catalog_health(user: User = Depends(require_user)):
    return {"status": "ok", "module": "catalog"}


@router.get("/tables/{table_name}")
def get_catalog_table(table_name: str, user: User = Depends(require_user)):
    definition = safe_load_table(dictionary_root(), table_name)
    if definition is None:
        raise api_error(404, "CATALOG_TABLE_NOT_FOUND", "Catalog table not found.")
    return serialize_table_definition(definition)


@router.get("/tables/{table_name}/columns")
def list_catalog_table_columns(table_name: str, user: User = Depends(require_user)):
    definition = safe_load_table(dictionary_root(), table_name)
    if definition is None:
        raise api_error(404, "CATALOG_TABLE_NOT_FOUND", "Catalog table not found.")
    items = serialize_columns(definition)
    return PageResponse(items=items, total=len(items))


@router.get("/reference/options")
def list_catalog_reference_options(
    object_type: str,
    domain_name: str = "OTM1",
    project_id: str | None = None,
    environment_id: str | None = None,
    profile_id: str | None = None,
    can_view_all_domains: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    return reference_options_payload(
        db,
        object_type=object_type,
        domain_name=domain_name,
        project_id=project_id,
        environment_id=environment_id,
        profile_id=profile_id,
        can_view_all_domains=can_view_all_domains,
    )


@router.post("/validate/table")
def validate_catalog_table(
    payload: ValidateTableRequest,
    user: User = Depends(require_user),
):
    return validate_table(dictionary_root(), payload.table_name, payload.usage)


@router.post("/validate/column")
def validate_catalog_column(
    payload: ValidateColumnRequest,
    user: User = Depends(require_user),
):
    return validate_column(dictionary_root(), payload.table_name, payload.column_name)
