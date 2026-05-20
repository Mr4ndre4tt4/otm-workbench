from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import MasterDataCoordinateQualityBatch, User
from otm_workbench.modules.master_data.coordinate_quality.services import (
    build_fake_provider,
    create_coordinate_quality_batch,
    list_coordinate_quality_results,
    preview_coordinate_quality,
    serialize_coordinate_quality_batch,
)

router = APIRouter(prefix="/coordinate-quality", tags=["master-data-coordinate-quality"])


class CoordinateQualityRequest(BaseModel):
    records: list[dict[str, Any]] = Field(default_factory=list)
    fake_candidates: dict[str, dict[str, Any]] = Field(default_factory=dict)
    source_type: str = "api"
    source_batch_id: str | None = None


@router.get("/health")
def coordinate_quality_health(user: User = Depends(require_user)):
    return {
        "status": "ok",
        "module": "master_data.coordinate_quality",
        "provider_modes": ["fake"],
    }


@router.post("/validate")
def validate_coordinate_quality_preview(
    request: CoordinateQualityRequest,
    user: User = Depends(require_user),
):
    provider = build_fake_provider(request.fake_candidates)
    return preview_coordinate_quality(request.records, provider)


@router.post("/batches")
def create_coordinate_quality_batch_endpoint(
    request: CoordinateQualityRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    provider = build_fake_provider(request.fake_candidates)
    return create_coordinate_quality_batch(
        db,
        request.records,
        provider=provider,
        source_type=request.source_type,
        source_batch_id=request.source_batch_id,
    )


@router.get("/batches/{batch_id}")
def get_coordinate_quality_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = (
        db.query(MasterDataCoordinateQualityBatch)
        .filter(MasterDataCoordinateQualityBatch.id == batch_id)
        .first()
    )
    if batch is None:
        raise api_error(404, "COORDINATE_QUALITY_BATCH_NOT_FOUND", "Coordinate Quality batch not found.")
    return serialize_coordinate_quality_batch(batch)


@router.get("/batches/{batch_id}/results")
def get_coordinate_quality_results(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = (
        db.query(MasterDataCoordinateQualityBatch)
        .filter(MasterDataCoordinateQualityBatch.id == batch_id)
        .first()
    )
    if batch is None:
        raise api_error(404, "COORDINATE_QUALITY_BATCH_NOT_FOUND", "Coordinate Quality batch not found.")
    return list_coordinate_quality_results(db, batch_id)
