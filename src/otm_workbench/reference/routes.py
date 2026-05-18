from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_admin, require_user
from otm_workbench.models import ReferenceObjectType, User
from otm_workbench.reference.services import (
    ReferenceContext,
    import_reference_records,
    list_reference_options,
    seed_reference_object_types,
    validate_reference_value,
)

router = APIRouter(prefix="/api/v1/reference", tags=["reference"])


class ReferenceImportRequest(BaseModel):
    source_type: str = "json"
    source_description: str = ""
    records: list[dict[str, object]]


class ReferenceOptionResponse(BaseModel):
    object_type: str
    gid: str
    xid: str
    domain_name: str
    display_name: str


class ReferenceValidateRequest(BaseModel):
    module_id: str
    field_name: str
    value: str
    domain_name: str = "OTM1"


@router.get("/object-types")
def list_object_types(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_reference_object_types(db)
    items = [
        {"code": item.code, "name": item.name, "description": item.description}
        for item in db.query(ReferenceObjectType).order_by(ReferenceObjectType.code).all()
    ]
    return PageResponse(items=items, total=len(items))


@router.post("/import-batches")
def create_import_batch(
    payload: ReferenceImportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    batch = import_reference_records(
        db=db,
        records=payload.records,
        source_type=payload.source_type,
        source_description=payload.source_description,
        actor_user_id=user.id,
    )
    return {
        "id": batch.id,
        "status": batch.status,
        "records_received": batch.records_received,
        "records_inserted": batch.records_inserted,
        "records_updated": batch.records_updated,
        "records_rejected": batch.records_rejected,
    }


@router.get("/options", response_model=PageResponse[ReferenceOptionResponse])
def reference_options(
    object_type: str,
    domain_name: str = "OTM1",
    view_all_domains: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
) -> PageResponse[ReferenceOptionResponse]:
    context = ReferenceContext(
        project_id=None,
        environment_id=None,
        profile_id=None,
        domain_name=domain_name,
        can_view_all_domains=bool(user.is_admin and view_all_domains),
    )
    objects = list_reference_options(db, context, object_type)
    items = [
        ReferenceOptionResponse(
            object_type=item.object_type,
            gid=item.gid,
            xid=item.xid,
            domain_name=item.domain_name,
            display_name=item.display_name,
        )
        for item in objects
    ]
    return PageResponse(items=items, total=len(items))


@router.post("/validate")
def validate_reference(
    payload: ReferenceValidateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    context = ReferenceContext(
        project_id=None,
        environment_id=None,
        profile_id=None,
        domain_name=payload.domain_name,
        can_view_all_domains=False,
    )
    result = validate_reference_value(
        db,
        context,
        payload.module_id,
        payload.field_name,
        payload.value,
    )
    return result.__dict__
