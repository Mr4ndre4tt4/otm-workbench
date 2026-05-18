from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import ReferenceObject, User
from otm_workbench.modules.rates.dictionary import (
    RATES_LOAD_SEQUENCE,
    load_table_definition,
    validate_load_sequence,
)

router = APIRouter(prefix="/api/v1/modules/rates", tags=["rates"])


class LoadSequenceRequest(BaseModel):
    tables: list[str] = RATES_LOAD_SEQUENCE


@router.get("/dictionary/tables")
def list_rates_dictionary_tables(user: User = Depends(require_user)):
    items = [{"table_name": item} for item in RATES_LOAD_SEQUENCE]
    return PageResponse(items=items, total=len(items))


@router.get("/dictionary/tables/{table_name}")
def get_rates_dictionary_table(
    table_name: str,
    user: User = Depends(require_user),
):
    definition = load_table_definition(Path(get_settings().otm_data_dictionary_root), table_name)
    return {
        "table_name": definition.table_name,
        "schema_name": definition.schema_name,
        "description": definition.description,
        "primary_key": definition.primary_key,
        "required_columns": definition.required_columns,
        "date_columns": definition.date_columns,
        "foreign_keys": [item.__dict__ for item in definition.foreign_keys],
    }


@router.post("/dictionary/validate-load-sequence")
def validate_rates_load_sequence(
    payload: LoadSequenceRequest,
    user: User = Depends(require_user),
):
    result = validate_load_sequence(Path(get_settings().otm_data_dictionary_root), payload.tables)
    return {
        "valid": result.valid,
        "known_tables": result.known_tables,
        "missing_tables": result.missing_tables,
        "issues": [item.__dict__ for item in result.issues],
    }


@router.get("/reference/rate-offerings")
def list_rate_offerings(
    servprov_gid: str | None = None,
    transport_mode_gid: str | None = None,
    rate_service_gid: str | None = None,
    equipment_group_profile_gid: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(ReferenceObject).filter(ReferenceObject.object_type == "RATE_OFFERING")
    for key, value in {
        "servprov_gid": servprov_gid,
        "transport_mode_gid": transport_mode_gid,
        "rate_service_gid": rate_service_gid,
        "equipment_group_profile_gid": equipment_group_profile_gid,
    }.items():
        if value:
            query = query.filter(ReferenceObject.metadata_json.contains(f'"{key}": "{value}"'))
    objects = query.order_by(ReferenceObject.gid).all()
    items = [
        {
            "gid": item.gid,
            "xid": item.xid,
            "domain_name": item.domain_name,
            "display_name": item.display_name,
            "metadata_json": item.metadata_json,
        }
        for item in objects
    ]
    return PageResponse(items=items, total=len(items))
