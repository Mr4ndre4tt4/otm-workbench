from otm_workbench.modules.master_data.coordinate_quality.engine import (
    classify_coordinate_quality,
    normalize_location_record,
    validate_coords,
)
from otm_workbench.modules.master_data.coordinate_quality.schemas import (
    CoordinateCandidate,
    CoordinateQualityRecord,
    CoordinateQualityStatus,
)


def test_validate_coords_uses_brazil_uf_bbox():
    assert validate_coords(-23.55, -46.63, "SP") is True
    assert validate_coords(-3.73, -38.52, "SP") is False
    assert validate_coords(None, -46.63, "SP") is False
    assert validate_coords(-23.55, None, "SP") is False


def test_classification_ok_when_original_valid_and_movement_below_threshold():
    record = CoordinateQualityRecord(
        location_gid="SYN.LOC_001",
        location_name="Synthetic Sao Paulo DC",
        address_line="Avenida Paulista 1000",
        city="Sao Paulo",
        province_code="SP",
        postal_code="01310-100",
        country_code3_gid="BRA",
        lat=-23.55,
        lon=-46.63,
    )
    candidate = CoordinateCandidate(lat=-23.56, lon=-46.64, source="fake")

    result = classify_coordinate_quality(record, candidate)

    assert result.status == CoordinateQualityStatus.OK
    assert result.diff_lat == 0.01
    assert result.diff_lon == 0.01
    assert result.orig_valid_uf is True
    assert result.new_valid_uf is True


def test_classification_corrected_when_original_outside_uf_and_candidate_inside():
    record = CoordinateQualityRecord(
        location_gid="SYN.LOC_002",
        location_name="Synthetic Corrected DC",
        address_line="Rua Teste 123",
        city="Sao Paulo",
        province_code="SP",
        postal_code="01000-000",
        country_code3_gid="BRA",
        lat=-3.73,
        lon=-38.52,
    )
    candidate = CoordinateCandidate(lat=-23.55, lon=-46.63, source="fake")

    result = classify_coordinate_quality(record, candidate)

    assert result.status == CoordinateQualityStatus.CORRECTED
    assert result.orig_valid_uf is False
    assert result.new_valid_uf is True


def test_classification_review_when_both_valid_but_movement_exceeds_threshold():
    record = CoordinateQualityRecord(
        location_gid="SYN.LOC_003",
        location_name="Synthetic Review DC",
        address_line="Rua Teste 456",
        city="Sao Paulo",
        province_code="SP",
        postal_code="01000-000",
        country_code3_gid="BRA",
        lat=-23.55,
        lon=-46.63,
    )
    candidate = CoordinateCandidate(lat=-22.70, lon=-45.90, source="fake")

    result = classify_coordinate_quality(record, candidate)

    assert result.status == CoordinateQualityStatus.REVIEW
    assert result.orig_valid_uf is True
    assert result.new_valid_uf is True


def test_classification_divergent_when_original_and_candidate_outside_uf():
    record = CoordinateQualityRecord(
        location_gid="SYN.LOC_004",
        location_name="Synthetic Divergent DC",
        address_line="Rua Teste 789",
        city="Sao Paulo",
        province_code="SP",
        postal_code="01000-000",
        country_code3_gid="BRA",
        lat=-3.73,
        lon=-38.52,
    )
    candidate = CoordinateCandidate(lat=-8.05, lon=-34.90, source="fake")

    result = classify_coordinate_quality(record, candidate)

    assert result.status == CoordinateQualityStatus.DIVERGENT


def test_classification_geocode_failed_when_provider_has_no_candidate():
    record = CoordinateQualityRecord(
        location_gid="SYN.LOC_005",
        location_name="Synthetic Missing Candidate",
        address_line="Unknown address",
        city="Sao Paulo",
        province_code="SP",
        postal_code="01000-000",
        country_code3_gid="BRA",
        lat=-23.55,
        lon=-46.63,
    )

    result = classify_coordinate_quality(record, None)

    assert result.status == CoordinateQualityStatus.GEOCODE_FAILED
    assert result.lat_new is None
    assert result.lon_new is None


def test_classification_null_filled_when_original_coordinate_is_missing():
    record = CoordinateQualityRecord(
        location_gid="SYN.LOC_006",
        location_name="Synthetic Null Filled DC",
        address_line="Rua Teste 999",
        city="Sao Paulo",
        province_code="SP",
        postal_code="01000-000",
        country_code3_gid="BRA",
        lat=None,
        lon=None,
    )
    candidate = CoordinateCandidate(lat=-23.55, lon=-46.63, source="fake")

    result = classify_coordinate_quality(record, candidate)

    assert result.status == CoordinateQualityStatus.NULL_FILLED
    assert result.lat_new == -23.55
    assert result.lon_new == -46.63


def test_normalize_location_record_accepts_location_template_payload():
    record = normalize_location_record(
        {
            "location_gid": "SYN.LOC_007",
            "location_name": "Synthetic Normalized DC",
            "address_line": "Rua Teste 100",
            "city": "Sao Paulo",
            "province_code": "sp",
            "postal_code": "01310-100",
            "country_code3_gid": "bra",
            "lat": "-23.55",
            "lon": "-46.63",
        }
    )

    assert record.location_gid == "SYN.LOC_007"
    assert record.province_code == "SP"
    assert record.country_code3_gid == "BRA"
    assert record.lat == -23.55
    assert record.lon == -46.63
