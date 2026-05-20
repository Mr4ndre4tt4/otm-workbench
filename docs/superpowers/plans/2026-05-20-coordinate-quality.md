# Coordinate Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the backend-first Coordinate Quality module for OTM `LOCATION` latitude/longitude validation, deterministic geocoding suggestions, persisted batch results, and client-safe evidence export.

**Architecture:** The pure engine lives under `src/otm_workbench/modules/master_data/coordinate_quality/` and does not import FastAPI, SQLAlchemy, or HTTP clients. The service layer owns persistence, summary counts, and artifact/evidence creation, while the route layer exposes the API under `/api/v1/modules/master-data/coordinate-quality`. Tests use deterministic fake providers only; no public geocoder, Docker, GUI, Excel helper, or real client data is required.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, Alembic, pytest, `httpx` only for optional future HTTP providers, OTM Workbench Artifact/Manifest/Evidence/AuditLog models.

---

## File Structure

- Create `src/otm_workbench/modules/master_data/coordinate_quality/__init__.py`: package marker and public exports.
- Create `src/otm_workbench/modules/master_data/coordinate_quality/schemas.py`: dataclasses, status enum, normalized input/output records.
- Create `src/otm_workbench/modules/master_data/coordinate_quality/engine.py`: UF bounding boxes, country helpers, coordinate validation, status classification, and record normalization.
- Create `src/otm_workbench/modules/master_data/coordinate_quality/providers.py`: provider protocol and deterministic fake provider used by tests and local MVP0 requests.
- Create `src/otm_workbench/modules/master_data/coordinate_quality/services.py`: batch orchestration, database persistence, summary counters, and evidence package export.
- Create `src/otm_workbench/modules/master_data/coordinate_quality/routes.py`: FastAPI endpoints mounted by the Master Data router.
- Modify `src/otm_workbench/modules/master_data/routes.py`: include the Coordinate Quality router.
- Modify `src/otm_workbench/models.py`: add `MasterDataCoordinateQualityBatch` and `MasterDataCoordinateQualityResult`.
- Create `migrations/versions/<revision>_coordinate_quality_batches.py`: create batch/result tables.
- Create `tests/test_coordinate_quality_engine.py`: pure engine and fake-provider tests.
- Create `tests/test_coordinate_quality_api.py`: API, persistence, and evidence export tests.

## Task 1: Pure Engine Foundation

**Files:**
- Create: `src/otm_workbench/modules/master_data/coordinate_quality/__init__.py`
- Create: `src/otm_workbench/modules/master_data/coordinate_quality/schemas.py`
- Create: `src/otm_workbench/modules/master_data/coordinate_quality/engine.py`
- Test: `tests/test_coordinate_quality_engine.py`

- [ ] **Step 1: Write failing enum, bbox, and status tests**

Add this file:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_coordinate_quality_engine.py -q
```

Expected: FAIL during import because `otm_workbench.modules.master_data.coordinate_quality` does not exist.

- [ ] **Step 3: Create schemas**

Add `src/otm_workbench/modules/master_data/coordinate_quality/__init__.py`:

```python
from otm_workbench.modules.master_data.coordinate_quality.engine import (
    classify_coordinate_quality,
    normalize_location_record,
    validate_coords,
)
from otm_workbench.modules.master_data.coordinate_quality.schemas import (
    CoordinateCandidate,
    CoordinateQualityRecord,
    CoordinateQualityResult,
    CoordinateQualityStatus,
)

__all__ = [
    "CoordinateCandidate",
    "CoordinateQualityRecord",
    "CoordinateQualityResult",
    "CoordinateQualityStatus",
    "classify_coordinate_quality",
    "normalize_location_record",
    "validate_coords",
]
```

Add `src/otm_workbench/modules/master_data/coordinate_quality/schemas.py`:

```python
from dataclasses import asdict, dataclass
from enum import StrEnum


class CoordinateQualityStatus(StrEnum):
    OK = "OK"
    CORRECTED = "CORRECTED"
    REVIEW = "REVIEW"
    DIVERGENT = "DIVERGENT"
    GEOCODE_FAILED = "GEOCODE_FAILED"
    NULL_FILLED = "NULL_FILLED"


@dataclass(frozen=True)
class CoordinateQualityRecord:
    location_gid: str
    location_name: str | None = None
    address_line: str | None = None
    city: str | None = None
    province_code: str | None = None
    postal_code: str | None = None
    country_code3_gid: str | None = None
    lat: float | None = None
    lon: float | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CoordinateCandidate:
    lat: float
    lon: float
    source: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CoordinateQualityResult:
    location_gid: str
    location_name: str | None
    address: dict[str, object]
    country_code3_gid: str | None
    province_code: str | None
    postal_code: str | None
    lat_orig: float | None
    lon_orig: float | None
    lat_new: float | None
    lon_new: float | None
    status: CoordinateQualityStatus
    source: str | None
    diff_lat: float | None
    diff_lon: float | None
    orig_valid_uf: bool
    new_valid_uf: bool
    issue: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload
```

- [ ] **Step 4: Implement engine**

Add `src/otm_workbench/modules/master_data/coordinate_quality/engine.py`:

```python
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
    diff_lat = _round_diff(abs(record.lat - lat_new)) if record.lat is not None and lat_new is not None else None
    diff_lon = _round_diff(abs(record.lon - lon_new)) if record.lon is not None and lon_new is not None else None

    if candidate is None:
        status = CoordinateQualityStatus.GEOCODE_FAILED
        issue_code = "COORDINATE_GEOCODE_FAILED"
    elif record.lat is None or record.lon is None:
        status = CoordinateQualityStatus.NULL_FILLED
        issue_code = "COORDINATE_NULL_FILLED"
    elif orig_valid and new_valid and (diff_lat or 0) <= diff_threshold_degrees and (diff_lon or 0) <= diff_threshold_degrees:
        status = CoordinateQualityStatus.OK
        issue_code = "COORDINATE_OK"
    elif not orig_valid and new_valid:
        status = CoordinateQualityStatus.CORRECTED
        issue_code = "COORDINATE_CORRECTED"
    elif orig_valid and new_valid:
        status = CoordinateQualityStatus.REVIEW
        issue_code = "COORDINATE_REVIEW"
    else:
        status = CoordinateQualityStatus.DIVERGENT
        issue_code = "COORDINATE_DIVERGENT"

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
```

- [ ] **Step 5: Run engine tests**

Run:

```bash
python -m pytest tests/test_coordinate_quality_engine.py -q
```

Expected: PASS for all engine tests.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/modules/master_data/coordinate_quality tests/test_coordinate_quality_engine.py
git commit -m "Add coordinate quality engine"
```

## Task 2: Fake Provider And Record Processing

**Files:**
- Create: `src/otm_workbench/modules/master_data/coordinate_quality/providers.py`
- Modify: `src/otm_workbench/modules/master_data/coordinate_quality/engine.py`
- Test: `tests/test_coordinate_quality_engine.py`

- [ ] **Step 1: Add failing fake-provider processing test**

Append to `tests/test_coordinate_quality_engine.py`:

```python
from otm_workbench.modules.master_data.coordinate_quality.engine import process_location_record
from otm_workbench.modules.master_data.coordinate_quality.providers import FakeGeocoderProvider


def test_process_location_record_uses_fake_provider_candidate():
    provider = FakeGeocoderProvider(
        {
            "SYN.LOC_008": CoordinateCandidate(lat=-23.55, lon=-46.63, source="fake:fixture")
        }
    )
    record = CoordinateQualityRecord(
        location_gid="SYN.LOC_008",
        location_name="Synthetic Provider DC",
        address_line="Rua Teste 123",
        city="Sao Paulo",
        province_code="SP",
        postal_code="01000-000",
        country_code3_gid="BRA",
        lat=None,
        lon=None,
    )

    result = process_location_record(record, provider)

    assert result.status == CoordinateQualityStatus.NULL_FILLED
    assert result.source == "fake:fixture"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_coordinate_quality_engine.py::test_process_location_record_uses_fake_provider_candidate -q
```

Expected: FAIL because `providers.py` and `process_location_record` are missing.

- [ ] **Step 3: Add provider protocol and fake provider**

Create `src/otm_workbench/modules/master_data/coordinate_quality/providers.py`:

```python
from typing import Protocol

from otm_workbench.modules.master_data.coordinate_quality.schemas import (
    CoordinateCandidate,
    CoordinateQualityRecord,
)


class GeocoderProvider(Protocol):
    provider_mode: str

    def geocode(self, record: CoordinateQualityRecord) -> CoordinateCandidate | None:
        """Return a deterministic candidate or None when no coordinate is available."""


class FakeGeocoderProvider:
    provider_mode = "fake"

    def __init__(self, candidates_by_location_gid: dict[str, CoordinateCandidate] | None = None):
        self.candidates_by_location_gid = candidates_by_location_gid or {}

    def geocode(self, record: CoordinateQualityRecord) -> CoordinateCandidate | None:
        return self.candidates_by_location_gid.get(record.location_gid)
```

- [ ] **Step 4: Add processing function**

Append to `src/otm_workbench/modules/master_data/coordinate_quality/engine.py`:

```python
from otm_workbench.modules.master_data.coordinate_quality.providers import GeocoderProvider


def process_location_record(
    record: CoordinateQualityRecord,
    provider: GeocoderProvider,
) -> CoordinateQualityResult:
    return classify_coordinate_quality(record, provider.geocode(record))
```

- [ ] **Step 5: Run engine tests**

Run:

```bash
python -m pytest tests/test_coordinate_quality_engine.py -q
```

Expected: PASS for all engine tests.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/modules/master_data/coordinate_quality tests/test_coordinate_quality_engine.py
git commit -m "Add coordinate quality fake provider"
```

## Task 3: Persistence Models And Migration

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `migrations/versions/c3a8f7b2d9e4_coordinate_quality_batches.py`
- Test: `tests/test_database.py`

- [ ] **Step 1: Add failing migration/model smoke assertion**

Append to `tests/test_database.py`:

```python
def test_coordinate_quality_tables_exist(db_session):
    batch_rows = db_session.execute(
        text("select count(*) from master_data_coordinate_quality_batches")
    ).scalar()
    result_rows = db_session.execute(
        text("select count(*) from master_data_coordinate_quality_results")
    ).scalar()

    assert batch_rows == 0
    assert result_rows == 0
```

If `tests/test_database.py` does not already import `text`, add:

```python
from sqlalchemy import text
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_database.py::test_coordinate_quality_tables_exist -q
```

Expected: FAIL because the tables do not exist.

- [ ] **Step 3: Add SQLAlchemy models**

Append near the other Master Data models in `src/otm_workbench/models.py`:

```python
class MasterDataCoordinateQualityBatch(Base, TimestampMixin):
    __tablename__ = "master_data_coordinate_quality_batches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    source_type: Mapped[str] = mapped_column(String, default="api")
    source_batch_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, default="PROCESSED", index=True)
    geocoder_base_url: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_mode: Mapped[str] = mapped_column(String, default="fake")
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    ok_count: Mapped[int] = mapped_column(Integer, default=0)
    corrected_count: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    divergent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    input_json: Mapped[str] = mapped_column(Text, default="[]")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    issues_json: Mapped[str] = mapped_column(Text, default="[]")


class MasterDataCoordinateQualityResult(Base, TimestampMixin):
    __tablename__ = "master_data_coordinate_quality_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(
        ForeignKey("master_data_coordinate_quality_batches.id"), index=True
    )
    location_gid: Mapped[str] = mapped_column(String, index=True)
    location_name: Mapped[str | None] = mapped_column(String, nullable=True)
    address_json: Mapped[str] = mapped_column(Text, default="{}")
    country_code3_gid: Mapped[str | None] = mapped_column(String, nullable=True)
    province_code: Mapped[str | None] = mapped_column(String, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String, nullable=True)
    lat_orig: Mapped[str | None] = mapped_column(String, nullable=True)
    lon_orig: Mapped[str | None] = mapped_column(String, nullable=True)
    lat_new: Mapped[str | None] = mapped_column(String, nullable=True)
    lon_new: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    diff_lat: Mapped[str | None] = mapped_column(String, nullable=True)
    diff_lon: Mapped[str | None] = mapped_column(String, nullable=True)
    orig_valid_uf: Mapped[bool] = mapped_column(Boolean, default=False)
    new_valid_uf: Mapped[bool] = mapped_column(Boolean, default=False)
    issue_json: Mapped[str] = mapped_column(Text, default="{}")
```

- [ ] **Step 4: Add migration**

Create `migrations/versions/c3a8f7b2d9e4_coordinate_quality_batches.py`:

```python
"""coordinate quality batches

Revision ID: c3a8f7b2d9e4
Revises: f9c1e7a4d2b8
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3a8f7b2d9e4"
down_revision: str | None = "f9c1e7a4d2b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "master_data_coordinate_quality_batches",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_batch_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("geocoder_base_url", sa.String(), nullable=True),
        sa.Column("provider_mode", sa.String(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("processed_count", sa.Integer(), nullable=False),
        sa.Column("ok_count", sa.Integer(), nullable=False),
        sa.Column("corrected_count", sa.Integer(), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("divergent_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("issues_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_master_data_coordinate_quality_batches_source_batch_id",
        "master_data_coordinate_quality_batches",
        ["source_batch_id"],
    )
    op.create_index(
        "ix_master_data_coordinate_quality_batches_status",
        "master_data_coordinate_quality_batches",
        ["status"],
    )
    op.create_table(
        "master_data_coordinate_quality_results",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("location_gid", sa.String(), nullable=False),
        sa.Column("location_name", sa.String(), nullable=True),
        sa.Column("address_json", sa.Text(), nullable=False),
        sa.Column("country_code3_gid", sa.String(), nullable=True),
        sa.Column("province_code", sa.String(), nullable=True),
        sa.Column("postal_code", sa.String(), nullable=True),
        sa.Column("lat_orig", sa.String(), nullable=True),
        sa.Column("lon_orig", sa.String(), nullable=True),
        sa.Column("lat_new", sa.String(), nullable=True),
        sa.Column("lon_new", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("diff_lat", sa.String(), nullable=True),
        sa.Column("diff_lon", sa.String(), nullable=True),
        sa.Column("orig_valid_uf", sa.Boolean(), nullable=False),
        sa.Column("new_valid_uf", sa.Boolean(), nullable=False),
        sa.Column("issue_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["master_data_coordinate_quality_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_master_data_coordinate_quality_results_batch_id",
        "master_data_coordinate_quality_results",
        ["batch_id"],
    )
    op.create_index(
        "ix_master_data_coordinate_quality_results_location_gid",
        "master_data_coordinate_quality_results",
        ["location_gid"],
    )
    op.create_index(
        "ix_master_data_coordinate_quality_results_status",
        "master_data_coordinate_quality_results",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_master_data_coordinate_quality_results_status",
        table_name="master_data_coordinate_quality_results",
    )
    op.drop_index(
        "ix_master_data_coordinate_quality_results_location_gid",
        table_name="master_data_coordinate_quality_results",
    )
    op.drop_index(
        "ix_master_data_coordinate_quality_results_batch_id",
        table_name="master_data_coordinate_quality_results",
    )
    op.drop_table("master_data_coordinate_quality_results")
    op.drop_index(
        "ix_master_data_coordinate_quality_batches_status",
        table_name="master_data_coordinate_quality_batches",
    )
    op.drop_index(
        "ix_master_data_coordinate_quality_batches_source_batch_id",
        table_name="master_data_coordinate_quality_batches",
    )
    op.drop_table("master_data_coordinate_quality_batches")
```

- [ ] **Step 5: Run migration checks**

Run:

```bash
python -m alembic heads
python -m pytest tests/test_database.py::test_coordinate_quality_tables_exist -q
```

Expected: one Alembic head and PASS for the table smoke test.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/models.py migrations/versions/c3a8f7b2d9e4_coordinate_quality_batches.py tests/test_database.py
git commit -m "Add coordinate quality persistence"
```

## Task 4: Batch Service

**Files:**
- Create: `src/otm_workbench/modules/master_data/coordinate_quality/services.py`
- Test: `tests/test_coordinate_quality_api.py`

- [ ] **Step 1: Add failing service persistence test**

Create `tests/test_coordinate_quality_api.py`:

```python
from otm_workbench.models import (
    MasterDataCoordinateQualityBatch,
    MasterDataCoordinateQualityResult,
)
from otm_workbench.modules.master_data.coordinate_quality.providers import FakeGeocoderProvider
from otm_workbench.modules.master_data.coordinate_quality.schemas import CoordinateCandidate
from otm_workbench.modules.master_data.coordinate_quality.services import create_coordinate_quality_batch


def test_create_coordinate_quality_batch_persists_summary_and_results(db_session):
    provider = FakeGeocoderProvider(
        {
            "SYN.LOC_001": CoordinateCandidate(lat=-23.55, lon=-46.63, source="fake:fixture"),
            "SYN.LOC_002": CoordinateCandidate(lat=-23.55, lon=-46.63, source="fake:fixture"),
        }
    )

    payload = create_coordinate_quality_batch(
        db_session,
        [
            {
                "location_gid": "SYN.LOC_001",
                "location_name": "Synthetic OK DC",
                "address_line": "Rua Um 100",
                "city": "Sao Paulo",
                "province_code": "SP",
                "postal_code": "01000-000",
                "country_code3_gid": "BRA",
                "lat": -23.55,
                "lon": -46.63,
            },
            {
                "location_gid": "SYN.LOC_002",
                "location_name": "Synthetic Corrected DC",
                "address_line": "Rua Dois 200",
                "city": "Sao Paulo",
                "province_code": "SP",
                "postal_code": "01000-000",
                "country_code3_gid": "BRA",
                "lat": -3.73,
                "lon": -38.52,
            },
        ],
        provider=provider,
        source_type="api",
    )

    assert payload["status"] == "PROCESSED"
    assert payload["summary"] == {
        "total_count": 2,
        "processed_count": 2,
        "ok_count": 1,
        "corrected_count": 1,
        "review_count": 0,
        "divergent_count": 0,
        "failed_count": 0,
    }

    batch = db_session.query(MasterDataCoordinateQualityBatch).one()
    results = db_session.query(MasterDataCoordinateQualityResult).order_by(
        MasterDataCoordinateQualityResult.location_gid
    ).all()
    assert batch.id == payload["batch_id"]
    assert [result.status for result in results] == ["OK", "CORRECTED"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_coordinate_quality_api.py::test_create_coordinate_quality_batch_persists_summary_and_results -q
```

Expected: FAIL because `services.py` does not exist.

- [ ] **Step 3: Implement batch service**

Create `src/otm_workbench/modules/master_data/coordinate_quality/services.py`:

```python
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


def create_coordinate_quality_batch(
    db: Session,
    records_payload: Sequence[Mapping[str, object]],
    provider: GeocoderProvider,
    source_type: str,
    source_batch_id: str | None = None,
    geocoder_base_url: str | None = None,
) -> dict[str, object]:
    records = [normalize_location_record(payload) for payload in records_payload]
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
        input_json=json.dumps(list(records_payload), sort_keys=True),
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
```

- [ ] **Step 4: Run service test**

Run:

```bash
python -m pytest tests/test_coordinate_quality_api.py::test_create_coordinate_quality_batch_persists_summary_and_results -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/otm_workbench/modules/master_data/coordinate_quality/services.py tests/test_coordinate_quality_api.py
git commit -m "Add coordinate quality batch service"
```

## Task 5: API Routes

**Files:**
- Create: `src/otm_workbench/modules/master_data/coordinate_quality/routes.py`
- Modify: `src/otm_workbench/modules/master_data/routes.py`
- Modify: `src/otm_workbench/modules/master_data/coordinate_quality/services.py`
- Test: `tests/test_coordinate_quality_api.py`

- [ ] **Step 1: Add failing route tests**

Append to `tests/test_coordinate_quality_api.py`:

```python
def test_coordinate_quality_health(client, admin_header):
    response = client.get(
        "/api/v1/modules/master-data/coordinate-quality/health",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "master_data.coordinate_quality",
        "provider_modes": ["fake"],
    }


def test_coordinate_quality_validate_preview_uses_inline_fake_candidates(client, admin_header):
    response = client.post(
        "/api/v1/modules/master-data/coordinate-quality/validate",
        headers=admin_header,
        json={
            "records": [
                {
                    "location_gid": "SYN.LOC_001",
                    "location_name": "Synthetic Preview DC",
                    "address_line": "Rua Um 100",
                    "city": "Sao Paulo",
                    "province_code": "SP",
                    "postal_code": "01000-000",
                    "country_code3_gid": "BRA",
                    "lat": None,
                    "lon": None,
                }
            ],
            "fake_candidates": {
                "SYN.LOC_001": {"lat": -23.55, "lon": -46.63, "source": "fake:inline"}
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total_count"] == 1
    assert payload["results"][0]["status"] == "NULL_FILLED"
    assert payload["results"][0]["source"] == "fake:inline"


def test_coordinate_quality_create_batch_endpoint_persists_results(client, admin_header, db_session):
    response = client.post(
        "/api/v1/modules/master-data/coordinate-quality/batches",
        headers=admin_header,
        json={
            "records": [
                {
                    "location_gid": "SYN.LOC_002",
                    "location_name": "Synthetic Batch DC",
                    "address_line": "Rua Dois 200",
                    "city": "Sao Paulo",
                    "province_code": "SP",
                    "postal_code": "01000-000",
                    "country_code3_gid": "BRA",
                    "lat": -3.73,
                    "lon": -38.52,
                }
            ],
            "fake_candidates": {
                "SYN.LOC_002": {"lat": -23.55, "lon": -46.63, "source": "fake:inline"}
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "PROCESSED"
    assert payload["summary"]["corrected_count"] == 1

    list_response = client.get(
        f"/api/v1/modules/master-data/coordinate-quality/batches/{payload['batch_id']}/results",
        headers=admin_header,
    )
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["status"] == "CORRECTED"
```

- [ ] **Step 2: Run route tests to verify failure**

Run:

```bash
python -m pytest tests/test_coordinate_quality_api.py::test_coordinate_quality_health tests/test_coordinate_quality_api.py::test_coordinate_quality_validate_preview_uses_inline_fake_candidates tests/test_coordinate_quality_api.py::test_coordinate_quality_create_batch_endpoint_persists_results -q
```

Expected: FAIL with 404 for the new endpoints.

- [ ] **Step 3: Add preview helpers to service**

Append to `src/otm_workbench/modules/master_data/coordinate_quality/services.py`:

```python
from otm_workbench.contracts import PageResponse


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
    records = [normalize_location_record(payload) for payload in records_payload]
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
```

- [ ] **Step 4: Add route file**

Create `src/otm_workbench/modules/master_data/coordinate_quality/routes.py`:

```python
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
```

- [ ] **Step 5: Mount route**

Modify `src/otm_workbench/modules/master_data/routes.py`:

```python
from otm_workbench.modules.master_data.coordinate_quality.routes import router as coordinate_quality_router
```

Then add after `router = APIRouter(...)`:

```python
router.include_router(coordinate_quality_router)
```

- [ ] **Step 6: Run route tests**

Run:

```bash
python -m pytest tests/test_coordinate_quality_api.py -q
```

Expected: PASS for service and API tests.

- [ ] **Step 7: Commit**

```bash
git add src/otm_workbench/modules/master_data tests/test_coordinate_quality_api.py
git commit -m "Expose coordinate quality API"
```

## Task 6: Evidence Export

**Files:**
- Modify: `src/otm_workbench/modules/master_data/coordinate_quality/services.py`
- Modify: `src/otm_workbench/modules/master_data/coordinate_quality/routes.py`
- Test: `tests/test_coordinate_quality_api.py`

- [ ] **Step 1: Add failing evidence export test**

Append to `tests/test_coordinate_quality_api.py`:

```python
import json
import zipfile

from otm_workbench.models import Artifact, Evidence, Manifest


def test_coordinate_quality_export_creates_client_safe_evidence(client, admin_header, db_session):
    batch_response = client.post(
        "/api/v1/modules/master-data/coordinate-quality/batches",
        headers=admin_header,
        json={
            "records": [
                {
                    "location_gid": "SYN.LOC_003",
                    "location_name": "Synthetic Export DC",
                    "address_line": "Rua Tres 300",
                    "city": "Sao Paulo",
                    "province_code": "SP",
                    "postal_code": "01000-000",
                    "country_code3_gid": "BRA",
                    "lat": None,
                    "lon": None,
                }
            ],
            "fake_candidates": {
                "SYN.LOC_003": {"lat": -23.55, "lon": -46.63, "source": "fake:inline"}
            },
        },
    )
    batch_id = batch_response.json()["batch_id"]

    response = client.post(
        f"/api/v1/modules/master-data/coordinate-quality/batches/{batch_id}/export",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"] == batch_id
    assert payload["file_name"].endswith(".zip")

    artifact = db_session.query(Artifact).filter(Artifact.id == payload["artifact_id"]).one()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    assert artifact.source_module == "master_data"
    assert artifact.artifact_type == "coordinate_quality_export_zip"
    assert artifact.sensitivity_level == "client_safe"
    assert evidence.evidence_type == "coordinate_quality_export"
    assert evidence.client_safe is True

    with zipfile.ZipFile(artifact.file_path) as archive:
        names = sorted(archive.namelist())
        assert names == ["manifest.json", "results.json"]
        manifest_payload = json.loads(archive.read("manifest.json").decode("utf-8"))
        results_payload = json.loads(archive.read("results.json").decode("utf-8"))

    assert manifest_payload["manifest_type"] == "coordinate_quality_export"
    assert manifest_payload["source_entity_id"] == batch_id
    assert results_payload["summary"]["total_count"] == 1
    assert json.loads(manifest.manifest_json)["manifest_type"] == "coordinate_quality_export"
```

- [ ] **Step 2: Run export test to verify failure**

Run:

```bash
python -m pytest tests/test_coordinate_quality_api.py::test_coordinate_quality_export_creates_client_safe_evidence -q
```

Expected: FAIL with 404 or missing export service.

- [ ] **Step 3: Implement export service**

Append to `src/otm_workbench/modules/master_data/coordinate_quality/services.py`:

```python
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from otm_workbench.models import Artifact, AuditLog, Evidence, Manifest
from otm_workbench.platform.services import file_sha256


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
```

- [ ] **Step 4: Add export route**

Modify imports in `src/otm_workbench/modules/master_data/coordinate_quality/routes.py`:

```python
from pathlib import Path

from otm_workbench.config import get_settings
from otm_workbench.modules.master_data.coordinate_quality.services import export_coordinate_quality_batch
```

Append route:

```python
@router.post("/batches/{batch_id}/export")
def export_coordinate_quality_batch_endpoint(
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
    return export_coordinate_quality_batch(
        db,
        batch,
        Path(get_settings().artifact_root),
        user.id,
    )
```

- [ ] **Step 5: Run export test**

Run:

```bash
python -m pytest tests/test_coordinate_quality_api.py::test_coordinate_quality_export_creates_client_safe_evidence -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/modules/master_data/coordinate_quality tests/test_coordinate_quality_api.py
git commit -m "Add coordinate quality evidence export"
```

## Task 7: Final Verification And PR

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run focused tests**

```bash
python -m pytest tests/test_coordinate_quality_engine.py tests/test_coordinate_quality_api.py tests/test_master_data_templates.py::test_master_data_locations_template_detail_and_validation tests/test_database.py -q
```

Expected: PASS.

- [ ] **Step 2: Run migration and diff checks**

```bash
python -m alembic heads
git diff --check
```

Expected: a single Alembic head and no whitespace errors.

- [ ] **Step 3: Inspect git status**

```bash
git status --short
```

Expected: tracked implementation changes only, plus the pre-existing untracked `OTM_RESOURCES/` directory that must remain unstaged.

- [ ] **Step 4: Push and open PR**

```bash
git push -u origin codex/coordinate-quality-engine
```

Open a PR linked to Linear `OTM-8` with:

```markdown
## Summary
- Adds backend-first Coordinate Quality engine for OTM LOCATION Lat/Lon validation.
- Adds fake-provider batch API and persisted result records.
- Adds client-safe evidence export package.

## Verification
- python -m pytest tests/test_coordinate_quality_engine.py tests/test_coordinate_quality_api.py tests/test_master_data_templates.py::test_master_data_locations_template_detail_and_validation tests/test_database.py -q
- python -m alembic heads
- git diff --check

Linear: OTM-8
```

## Self-Review

- Spec coverage: engine validation, UF bbox checks, fake provider, persisted batches/results, API endpoints, and evidence export are mapped to tasks. GUI, exe, Excel helpers, direct OTM mutation, Docker, and public geocoder calls remain out of scope.
- Data dictionary alignment: MVP0 reads and validates the existing `LOCATION` fields already present in the `LOCATIONS_BASIC` template (`LOCATION_GID`, `LOCATION_NAME`, `CITY`, `PROVINCE_CODE`, `POSTAL_CODE`, `COUNTRY_CODE3_GID`, `LAT`, `LON`) and `LOCATION_ADDRESS.ADDRESS_LINE`; no new OTM table assumptions are introduced.
- Completion-marker scan: this plan contains no unresolved future-work markers or open-ended validation instructions.
- Type consistency: `CoordinateQualityRecord`, `CoordinateCandidate`, `CoordinateQualityResult`, and `CoordinateQualityStatus` are introduced before they are referenced by services and routes.
