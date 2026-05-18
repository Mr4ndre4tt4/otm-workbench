from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import User
from otm_workbench.catalog.services import (
    get_macro_object,
    list_macro_objects,
    macro_object_tables,
    reference_options_payload,
    safe_load_table,
    serialize_columns,
    serialize_macro_object,
    serialize_macro_object_table,
    serialize_table_definition,
    validate_column,
    validate_table,
)
from otm_workbench.reference.services import ReferenceContext, validate_reference_value

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


class ValidateTableRequest(BaseModel):
    table_name: str
    usage: str | None = None


class ValidateColumnRequest(BaseModel):
    table_name: str
    column_name: str


class ValidateReferenceRequest(BaseModel):
    module_id: str
    field_name: str
    value: str
    domain_name: str = "OTM1"
    project_id: str | None = None
    environment_id: str | None = None
    profile_id: str | None = None
    can_view_all_domains: bool = False


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


@router.get("/macro-objects")
def list_catalog_macro_objects(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    items = [serialize_macro_object(db, item) for item in list_macro_objects(db, dictionary_root())]
    return PageResponse(items=items, total=len(items))


@router.get("/macro-objects/{macro_object_code}")
def get_catalog_macro_object(
    macro_object_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    macro = get_macro_object(db, dictionary_root(), macro_object_code)
    if macro is None:
        raise api_error(404, "CATALOG_MACRO_OBJECT_NOT_FOUND", "Catalog macro-object not found.")
    return serialize_macro_object(db, macro, include_children=True)


@router.get("/macro-objects/{macro_object_code}/tables")
def list_catalog_macro_object_tables(
    macro_object_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    macro = get_macro_object(db, dictionary_root(), macro_object_code)
    if macro is None:
        raise api_error(404, "CATALOG_MACRO_OBJECT_NOT_FOUND", "Catalog macro-object not found.")
    items = [serialize_macro_object_table(row) for row in macro_object_tables(db, macro)]
    return PageResponse(items=items, total=len(items))


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


@router.post("/validate/reference")
def validate_catalog_reference(
    payload: ValidateReferenceRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    context = ReferenceContext(
        project_id=payload.project_id,
        environment_id=payload.environment_id,
        profile_id=payload.profile_id,
        domain_name=payload.domain_name,
        can_view_all_domains=payload.can_view_all_domains,
    )
    result = validate_reference_value(
        db,
        context,
        payload.module_id,
        payload.field_name,
        payload.value,
    )
    return result.__dict__
