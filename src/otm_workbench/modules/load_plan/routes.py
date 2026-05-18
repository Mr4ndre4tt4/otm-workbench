from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import LoadPlanPackage, RateBatch, User
from otm_workbench.modules.load_plan.packages import (
    load_plan_package_summary,
    register_rates_package,
    serialize_load_plan_package,
)

router = APIRouter(prefix="/api/v1/modules/load-plan", tags=["load-plan"])


@router.post("/packages/from-rates/{batch_id}")
def register_load_plan_package_from_rates(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    try:
        package = register_rates_package(db, batch=batch, created_by=user.email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_load_plan_package(package)


@router.get("/packages")
def list_load_plan_packages(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    packages = db.query(LoadPlanPackage).order_by(LoadPlanPackage.created_at.desc()).all()
    items = [serialize_load_plan_package(package) for package in packages]
    return PageResponse(items=items, total=len(items))


@router.get("/packages/{package_id}")
def get_load_plan_package(
    package_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    package = db.query(LoadPlanPackage).filter(LoadPlanPackage.id == package_id).first()
    if package is None:
        raise HTTPException(status_code=404, detail="Load Plan package not found.")
    return serialize_load_plan_package(package)


@router.get("/summary")
def get_load_plan_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    return load_plan_package_summary(db)
