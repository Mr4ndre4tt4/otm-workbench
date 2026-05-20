from collections.abc import Mapping

from otm_workbench.modules.master_data.coordinate_quality.schemas import (
    CoordinateCandidate,
    CoordinateQualityRecord,
    CoordinateQualityResult,
    CoordinateQualityStatus,
)

DEFAULT_DIFF_THRESHOLD_DEGREES = 0.5

UF_BBOX = {
    "AC": (-11.2, -7.0, -74.1, -66.6),
    "AL": (-10.6, -8.8, -38.3, -35.1),
    "AM": (-9.9, 2.3, -73.8, -56.0),
    "AP": (-1.3, 4.5, -54.9, -49.8),
    "BA": (-18.4, -8.5, -46.8, -37.2),
    "CE": (-7.9, -2.7, -41.5, -37.2),
    "DF": (-16.1, -15.5, -48.3, -47.3),
    "ES": (-21.4, -17.8, -41.9, -39.6),
    "GO": (-19.6, -12.4, -53.3, -45.9),
    "MA": (-10.3, -1.0, -48.8, -41.8),
    "MG": (-22.9, -14.0, -51.1, -39.8),
    "MS": (-24.1, -17.0, -58.2, -50.9),
    "MT": (-18.1, -7.0, -61.7, -50.2),
    "PA": (-9.9, 2.8, -58.9, -46.0),
    "PB": (-8.4, -6.0, -38.8, -34.7),
    "PE": (-9.6, -7.2, -41.4, -34.7),
    "PI": (-10.9, -2.5, -45.9, -40.3),
    "PR": (-26.8, -22.3, -54.7, -48.0),
    "RJ": (-23.4, -20.7, -44.9, -40.9),
    "RN": (-6.9, -4.8, -38.7, -34.9),
    "RO": (-13.8, -7.9, -66.9, -59.7),
    "RR": (-1.7, 5.3, -64.8, -58.8),
    "RS": (-33.9, -27.0, -57.7, -49.6),
    "SC": (-29.4, -25.9, -53.9, -48.3),
    "SE": (-11.6, -9.5, -38.3, -36.3),
    "SP": (-25.4, -19.7, -53.2, -44.0),
    "TO": (-13.5, -5.0, -50.8, -45.6),
}


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clean_upper(value: object) -> str | None:
    text = _clean_text(value)
    return text.upper() if text else None


def _clean_float(value: object) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)


def _round_diff(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def validate_coords(lat: float | None, lon: float | None, uf: str | None) -> bool:
    if lat is None or lon is None or not uf:
        return False
    bbox = UF_BBOX.get(uf.upper())
    if bbox is None:
        return False
    min_lat, max_lat, min_lon, max_lon = bbox
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def normalize_location_record(payload: Mapping[str, object]) -> CoordinateQualityRecord:
    return CoordinateQualityRecord(
        location_gid=str(payload["location_gid"]).strip(),
        location_name=_clean_text(payload.get("location_name")),
        address_line=_clean_text(payload.get("address_line") or payload.get("full_address")),
        city=_clean_text(payload.get("city")),
        province_code=_clean_upper(payload.get("province_code")),
        postal_code=_clean_text(payload.get("postal_code")),
        country_code3_gid=_clean_upper(payload.get("country_code3_gid")),
        lat=_clean_float(payload.get("lat")),
        lon=_clean_float(payload.get("lon")),
    )


def classify_coordinate_quality(
    record: CoordinateQualityRecord,
    candidate: CoordinateCandidate | None,
    diff_threshold_degrees: float = DEFAULT_DIFF_THRESHOLD_DEGREES,
) -> CoordinateQualityResult:
    orig_valid = validate_coords(record.lat, record.lon, record.province_code)
    lat_new = candidate.lat if candidate else None
    lon_new = candidate.lon if candidate else None
    new_valid = validate_coords(lat_new, lon_new, record.province_code)
    diff_lat = _diff(record.lat, lat_new)
    diff_lon = _diff(record.lon, lon_new)
    status, issue_code = _classify_status(
        candidate=candidate,
        record=record,
        orig_valid=orig_valid,
        new_valid=new_valid,
        diff_lat=diff_lat,
        diff_lon=diff_lon,
        diff_threshold_degrees=diff_threshold_degrees,
    )

    return CoordinateQualityResult(
        location_gid=record.location_gid,
        location_name=record.location_name,
        address={"address_line": record.address_line, "city": record.city},
        country_code3_gid=record.country_code3_gid,
        province_code=record.province_code,
        postal_code=record.postal_code,
        lat_orig=record.lat,
        lon_orig=record.lon,
        lat_new=lat_new,
        lon_new=lon_new,
        status=status,
        source=candidate.source if candidate else None,
        diff_lat=diff_lat,
        diff_lon=diff_lon,
        orig_valid_uf=orig_valid,
        new_valid_uf=new_valid,
        issue={
            "code": issue_code,
            "severity": "INFO" if status == CoordinateQualityStatus.OK else "WARNING",
        },
    )


def _diff(original: float | None, candidate: float | None) -> float | None:
    if original is None or candidate is None:
        return None
    return _round_diff(abs(original - candidate))


def _classify_status(
    candidate: CoordinateCandidate | None,
    record: CoordinateQualityRecord,
    orig_valid: bool,
    new_valid: bool,
    diff_lat: float | None,
    diff_lon: float | None,
    diff_threshold_degrees: float,
) -> tuple[CoordinateQualityStatus, str]:
    if candidate is None:
        return CoordinateQualityStatus.GEOCODE_FAILED, "COORDINATE_GEOCODE_FAILED"
    if record.lat is None or record.lon is None:
        return CoordinateQualityStatus.NULL_FILLED, "COORDINATE_NULL_FILLED"
    if (
        orig_valid
        and new_valid
        and (diff_lat or 0) <= diff_threshold_degrees
        and (diff_lon or 0) <= diff_threshold_degrees
    ):
        return CoordinateQualityStatus.OK, "COORDINATE_OK"
    if not orig_valid and new_valid:
        return CoordinateQualityStatus.CORRECTED, "COORDINATE_CORRECTED"
    if orig_valid and new_valid:
        return CoordinateQualityStatus.REVIEW, "COORDINATE_REVIEW"
    return CoordinateQualityStatus.DIVERGENT, "COORDINATE_DIVERGENT"
