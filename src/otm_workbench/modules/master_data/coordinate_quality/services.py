import json
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.models import (
    Artifact,
    AuditLog,
    Evidence,
    Manifest,
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
from otm_workbench.platform.services import file_sha256


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


def build_fake_provider(fake_candidates: Mapping[str, Mapping[str, object]] | None) -> GeocoderProvider:
    from otm_workbench.modules.master_data.coordinate_quality.providers import FakeGeocoderProvider
    from otm_workbench.modules.master_data.coordinate_quality.schemas import CoordinateCandidate

    candidates = {
        location_gid: CoordinateCandidate(
            lat=float(candidate["lat"]),
            lon=float(candidate["lon"]),
            source=str(candidate.get("source") or "fake:inline"),
        )
        for location_gid, candidate in (fake_candidates or {}).items()
    }
    return FakeGeocoderProvider(candidates)


def preview_coordinate_quality(
    records_payload: Sequence[Mapping[str, object]],
    provider: GeocoderProvider,
) -> dict[str, object]:
    input_payloads = [dict(payload) for payload in records_payload]
    records = [normalize_location_record(payload) for payload in input_payloads]
    results = [process_location_record(record, provider) for record in records]
    return {
        "summary": _count_results(results),
        "results": [result.to_dict() for result in results],
    }


def serialize_coordinate_quality_batch(batch: MasterDataCoordinateQualityBatch) -> dict[str, object]:
    return {
        "batch_id": batch.id,
        "status": batch.status,
        "provider_mode": batch.provider_mode,
        "summary": json.loads(batch.summary_json),
        "issues": json.loads(batch.issues_json),
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
    }


def list_coordinate_quality_results(db: Session, batch_id: str) -> PageResponse:
    rows = (
        db.query(MasterDataCoordinateQualityResult)
        .filter(MasterDataCoordinateQualityResult.batch_id == batch_id)
        .order_by(MasterDataCoordinateQualityResult.created_at, MasterDataCoordinateQualityResult.location_gid)
        .all()
    )
    items = [
        {
            "id": row.id,
            "batch_id": row.batch_id,
            "location_gid": row.location_gid,
            "location_name": row.location_name,
            "address": json.loads(row.address_json),
            "country_code3_gid": row.country_code3_gid,
            "province_code": row.province_code,
            "postal_code": row.postal_code,
            "lat_orig": row.lat_orig,
            "lon_orig": row.lon_orig,
            "lat_new": row.lat_new,
            "lon_new": row.lon_new,
            "status": row.status,
            "source": row.source,
            "diff_lat": row.diff_lat,
            "diff_lon": row.diff_lon,
            "orig_valid_uf": row.orig_valid_uf,
            "new_valid_uf": row.new_valid_uf,
            "issue": json.loads(row.issue_json),
        }
        for row in rows
    ]
    return PageResponse(items=items, total=len(items))


def export_coordinate_quality_batch(
    db: Session,
    batch: MasterDataCoordinateQualityBatch,
    artifact_root: Path,
    generated_by: str,
) -> dict[str, object]:
    results_page = list_coordinate_quality_results(db, batch.id)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    export_dir = artifact_root / "master_data" / "coordinate_quality" / batch.id / timestamp
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"coordinate_quality_batch_{batch.id}.zip"

    results_payload = {
        "batch_id": batch.id,
        "summary": json.loads(batch.summary_json),
        "results": results_page.items,
    }
    manifest_payload = {
        "schema_version": "coordinate-quality-export-manifest/v1",
        "manifest_type": "coordinate_quality_export",
        "source_module": "master_data",
        "source_entity_type": "coordinate_quality_batch",
        "source_entity_id": batch.id,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "generated_by": generated_by,
        "result_count": results_page.total,
    }

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest_payload, indent=2, sort_keys=True))
        archive.writestr("results.json", json.dumps(results_payload, indent=2, sort_keys=True))

    digest, size = file_sha256(str(zip_path))
    artifact = Artifact(
        source_module="master_data",
        artifact_type="coordinate_quality_export_zip",
        file_path=str(zip_path),
        file_name=zip_path.name,
        content_type="application/zip",
        sha256=digest,
        size_bytes=size,
        sensitivity_level="client_safe",
    )
    db.add(artifact)
    db.flush()

    manifest = Manifest(
        source_module="master_data",
        status="CREATED",
        manifest_json=json.dumps(manifest_payload, indent=2, sort_keys=True),
    )
    db.add(manifest)
    db.flush()

    evidence = Evidence(
        source_module="master_data",
        evidence_type="coordinate_quality_export",
        summary_json=json.dumps(
            {
                "source_entity_type": "coordinate_quality_batch",
                "source_entity_id": batch.id,
                "result_count": results_page.total,
                "artifact_type": "coordinate_quality_export_zip",
            },
            sort_keys=True,
        ),
        artifact_id=artifact.id,
        manifest_id=manifest.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    db.add(
        AuditLog(
            actor_user_id=generated_by,
            action="master_data.coordinate_quality.export",
            target_type="coordinate_quality_batch",
            target_id=batch.id,
            metadata_json=json.dumps(
                {
                    "artifact_id": artifact.id,
                    "manifest_id": manifest.id,
                    "evidence_id": evidence.id,
                    "result_count": results_page.total,
                },
                sort_keys=True,
            ),
        )
    )
    db.commit()

    return {
        "batch_id": batch.id,
        "artifact_id": artifact.id,
        "manifest_id": manifest.id,
        "evidence_id": evidence.id,
        "file_name": artifact.file_name,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
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
