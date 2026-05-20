from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import OrderReleaseTemplate, User
from otm_workbench.modules.order_release_generator.templates import (
    seed_order_release_templates,
    serialize_order_release_template,
)


router = APIRouter(prefix="/api/v1/modules/order-release-generator", tags=["order-release-generator"])


@router.get("/health")
def order_release_generator_health(user: User = Depends(require_user)):
    return {"status": "ok", "module": "order_release_generator"}


@router.get("/templates")
def list_order_release_templates(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_order_release_templates(db)
    templates = (
        db.query(OrderReleaseTemplate)
        .order_by(OrderReleaseTemplate.code, OrderReleaseTemplate.version.desc())
        .all()
    )
    items = [serialize_order_release_template(template) for template in templates]
    return PageResponse(items=items, total=len(items))
