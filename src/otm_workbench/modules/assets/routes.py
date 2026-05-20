from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import User
from otm_workbench.modules.assets.classifications import grouped_asset_classifications


router = APIRouter(prefix="/api/v1/modules/assets", tags=["assets"])


@router.get("/health")
def assets_health(user: User = Depends(require_user)):
    return {"status": "ok", "module": "assets"}


@router.get("/classifications")
def list_asset_classifications(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    items = grouped_asset_classifications(db)
    return PageResponse(items=items, total=len(items))
