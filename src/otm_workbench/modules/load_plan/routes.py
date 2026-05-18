from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import (
    CsvutilBuild,
    LoadPlanPackage,
    LoadPlanReviewItem,
    LoadPlanSequenceSnapshot,
    LoadPlanZipAnalysis,
    RateBatch,
    User,
)
from otm_workbench.modules.load_plan.csvutil import generate_csvutil_build, serialize_csvutil_build
from otm_workbench.modules.load_plan.packages import (
    load_plan_package_summary,
    register_rates_package,
    serialize_load_plan_package,
)
from otm_workbench.modules.load_plan.review_queue import (
    decide_review_item,
    generate_review_queue_from_zip_analysis,
    serialize_review_decision,
    serialize_review_item_with_latest_decision,
)
from otm_workbench.modules.load_plan.sequence import (
    generate_sequence_snapshot,
    latest_sequence_snapshot,
    serialize_sequence_snapshot,
)
from otm_workbench.modules.load_plan.zip_analysis import generate_zip_analysis, serialize_zip_analysis

router = APIRouter(prefix="/api/v1/modules/load-plan", tags=["load-plan"])


class CsvutilBuildRequest(BaseModel):
    package_id: str


class ZipAnalysisRequest(BaseModel):
    package_id: str


class ReviewDecisionRequest(BaseModel):
    decision_status: str
    decision_note: str = ""


class SequenceSnapshotRequest(BaseModel):
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


@router.post("/sequence/snapshots")
def create_sequence_snapshot(
    payload: SequenceSnapshotRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    package = db.query(LoadPlanPackage).filter(LoadPlanPackage.id == payload.package_id).first()
    if package is None:
        raise HTTPException(status_code=404, detail="Load Plan package not found.")
    try:
        snapshot = generate_sequence_snapshot(
            db,
            package=package,
            dictionary_root=Path(get_settings().otm_data_dictionary_root),
            generated_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_sequence_snapshot(snapshot)


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


@router.get("/csvutil/builds")
def list_csvutil_builds(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    builds = db.query(CsvutilBuild).order_by(CsvutilBuild.created_at.desc()).all()
    items = [serialize_csvutil_build(build) for build in builds]
    return PageResponse(items=items, total=len(items))


@router.get("/csvutil/builds/{build_id}")
def get_csvutil_build(
    build_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    build = db.query(CsvutilBuild).filter(CsvutilBuild.id == build_id).first()
    if build is None:
        raise HTTPException(status_code=404, detail="CSVUTIL build not found.")
    return serialize_csvutil_build(build)


@router.post("/zip-analysis")
def run_zip_analysis(
    payload: ZipAnalysisRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    package = db.query(LoadPlanPackage).filter(LoadPlanPackage.id == payload.package_id).first()
    if package is None:
        raise HTTPException(status_code=404, detail="Load Plan package not found.")
    try:
        analysis = generate_zip_analysis(
            db,
            package=package,
            dictionary_root=Path(get_settings().otm_data_dictionary_root),
            analyzed_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_zip_analysis(analysis)


@router.get("/zip-analysis")
def list_zip_analyses(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    analyses = db.query(LoadPlanZipAnalysis).order_by(LoadPlanZipAnalysis.created_at.desc()).all()
    items = [serialize_zip_analysis(analysis) for analysis in analyses]
    return PageResponse(items=items, total=len(items))


@router.get("/zip-analysis/{analysis_id}")
def get_zip_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    analysis = db.query(LoadPlanZipAnalysis).filter(LoadPlanZipAnalysis.id == analysis_id).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="ZIP analysis not found.")
    return serialize_zip_analysis(analysis)


@router.post("/review-queue/from-zip-analysis/{analysis_id}")
def generate_review_queue_from_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    analysis = db.query(LoadPlanZipAnalysis).filter(LoadPlanZipAnalysis.id == analysis_id).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="ZIP analysis not found.")
    try:
        return generate_review_queue_from_zip_analysis(
            db,
            analysis=analysis,
            generated_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/review-queue")
def list_review_queue_items(
    status: str | None = None,
    severity: str | None = None,
    package_id: str | None = None,
    zip_analysis_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(LoadPlanReviewItem)
    if status:
        query = query.filter(LoadPlanReviewItem.status == status)
    if severity:
        query = query.filter(LoadPlanReviewItem.severity == severity)
    if package_id:
        query = query.filter(LoadPlanReviewItem.package_id == package_id)
    if zip_analysis_id:
        query = query.filter(LoadPlanReviewItem.zip_analysis_id == zip_analysis_id)
    items = query.order_by(LoadPlanReviewItem.created_at.desc()).all()
    return PageResponse(items=[serialize_review_item_with_latest_decision(db, item) for item in items], total=len(items))


@router.post("/review-queue/{item_id}/decide")
def decide_review_queue_item(
    item_id: str,
    payload: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    item = db.query(LoadPlanReviewItem).filter(LoadPlanReviewItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Review queue item not found.")
    try:
        decision = decide_review_item(
            db,
            item=item,
            decision_status=payload.decision_status,
            decision_note=payload.decision_note,
            decided_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_review_decision(db, decision)


@router.get("/review-queue/{item_id}")
def get_review_queue_item(
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    item = db.query(LoadPlanReviewItem).filter(LoadPlanReviewItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Review queue item not found.")
    return serialize_review_item_with_latest_decision(db, item)
