from fastapi import APIRouter, Depends

from otm_workbench.dependencies import require_user
from otm_workbench.models import User


router = APIRouter(prefix="/api/v1/modules/integration-mapping", tags=["integration-mapping"])


@router.get("/health")
def integration_mapping_health(user: User = Depends(require_user)):
    return {
        "status": "ok",
        "module": "integration_mapping",
        "mode": "specification_first",
    }
