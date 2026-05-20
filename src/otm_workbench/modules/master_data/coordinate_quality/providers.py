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
