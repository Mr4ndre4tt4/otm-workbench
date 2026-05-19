from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import MasterDataTemplate, User
from otm_workbench.modules.master_data.templates import (
    seed_master_data_templates,
    serialize_master_data_template,
)

router = APIRouter(prefix="/api/v1/modules/master-data", tags=["master-data"])


@router.get("/health")
def master_data_health(user: User = Depends(require_user)):
    return {"status": "ok", "module": "master_data", "catalog_macro_object_code": "REGION"}


@router.get("/templates")
def list_master_data_templates(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    templates = db.query(MasterDataTemplate).order_by(MasterDataTemplate.code).all()
    items = [serialize_master_data_template(template) for template in templates]
    return PageResponse(items=items, total=len(items))
