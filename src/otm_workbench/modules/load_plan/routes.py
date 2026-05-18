from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import CsvutilBuild, LoadPlanPackage, RateBatch, User
from otm_workbench.modules.load_plan.csvutil import generate_csvutil_build, serialize_csvutil_build
from otm_workbench.modules.load_plan.packages import (
    load_plan_package_summary,
    register_rates_package,
    serialize_load_plan_package,
)

router = APIRouter(prefix="/api/v1/modules/load-plan", tags=["load-plan"])


class CsvutilBuildRequest(BaseModel):
    package_id: str


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


@router.post("/csvutil/build")
def build_csvutil_artifacts(
    payload: CsvutilBuildRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    package = db.query(LoadPlanPackage).filter(LoadPlanPackage.id == payload.package_id).first()
    if package is None:
        raise HTTPException(status_code=404, detail="Load Plan package not found.")
    try:
        build = generate_csvutil_build(
            db,
            package=package,
            artifact_root=Path(get_settings().artifact_root),
            built_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_csvutil_build(build)
