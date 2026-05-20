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
