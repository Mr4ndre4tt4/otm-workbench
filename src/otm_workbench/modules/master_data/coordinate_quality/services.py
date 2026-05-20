import json
from collections.abc import Mapping, Sequence

from sqlalchemy.orm import Session

from otm_workbench.models import (
    MasterDataCoordinateQualityBatch,
    MasterDataCoordinateQualityResult,
)
from otm_workbench.modules.master_data.coordinate_quality.engine import (
    normalize_location_record,
    process_location_record,
)
from otm_workbench.modules.master_data.coordinate_quality.providers import GeocoderProvider
from otm_workbench.modules.master_data.coordinate_quality.schemas import (
    CoordinateQualityResult,
    CoordinateQualityStatus,
)


def create_coordinate_quality_batch(
    db: Session,
    records_payload: Sequence[Mapping[str, object]],
    provider: GeocoderProvider,
    source_type: str,
    source_batch_id: str | None = None,
    geocoder_base_url: str | None = None,
) -> dict[str, object]:
    input_payloads = [dict(payload) for payload in records_payload]
    records = [normalize_location_record(payload) for payload in input_payloads]
    results = [process_location_record(record, provider) for record in records]
    summary = _count_results(results)
    issues = [
        result.issue
        for result in results
        if result.status != CoordinateQualityStatus.OK
    ]

    batch = MasterDataCoordinateQualityBatch(
        source_type=source_type,
        source_batch_id=source_batch_id,
        status="PROCESSED",
        geocoder_base_url=geocoder_base_url,
        provider_mode=provider.provider_mode,
        total_count=summary["total_count"],
        processed_count=summary["processed_count"],
        ok_count=summary["ok_count"],
        corrected_count=summary["corrected_count"],
        review_count=summary["review_count"],
        divergent_count=summary["divergent_count"],
        failed_count=summary["failed_count"],
        input_json=json.dumps(input_payloads, sort_keys=True),
        summary_json=json.dumps(summary, sort_keys=True),
        issues_json=json.dumps(issues, sort_keys=True),
    )
    db.add(batch)
    db.flush()

    for result in results:
        db.add(
            MasterDataCoordinateQualityResult(
                batch_id=batch.id,
                location_gid=result.location_gid,
                location_name=result.location_name,
                address_json=json.dumps(result.address, sort_keys=True),
                country_code3_gid=result.country_code3_gid,
                province_code=result.province_code,
                postal_code=result.postal_code,
                lat_orig=_string_float(result.lat_orig),
                lon_orig=_string_float(result.lon_orig),
                lat_new=_string_float(result.lat_new),
                lon_new=_string_float(result.lon_new),
                status=result.status.value,
                source=result.source,
                diff_lat=_string_float(result.diff_lat),
                diff_lon=_string_float(result.diff_lon),
                orig_valid_uf=result.orig_valid_uf,
                new_valid_uf=result.new_valid_uf,
                issue_json=json.dumps(result.issue, sort_keys=True),
            )
        )
    db.commit()
    db.refresh(batch)

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "provider_mode": batch.provider_mode,
        "summary": summary,
        "issues": issues,
    }


def _count_results(results: Sequence[CoordinateQualityResult]) -> dict[str, int]:
    return {
        "total_count": len(results),
        "processed_count": len(results),
        "ok_count": sum(result.status == CoordinateQualityStatus.OK for result in results),
        "corrected_count": sum(result.status == CoordinateQualityStatus.CORRECTED for result in results),
        "review_count": sum(result.status == CoordinateQualityStatus.REVIEW for result in results),
        "divergent_count": sum(result.status == CoordinateQualityStatus.DIVERGENT for result in results),
        "failed_count": sum(result.status == CoordinateQualityStatus.GEOCODE_FAILED for result in results),
    }


def _string_float(value: float | None) -> str | None:
    return None if value is None else str(value)
