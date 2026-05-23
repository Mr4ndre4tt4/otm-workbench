import json
import zipfile

from otm_workbench.models import (
    Artifact,
    Evidence,
    Manifest,
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
    results = (
        db_session.query(MasterDataCoordinateQualityResult)
        .order_by(MasterDataCoordinateQualityResult.location_gid)
        .all()
    )
    assert batch.id == payload["batch_id"]
    assert [result.status for result in results] == ["OK", "CORRECTED"]


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
                    "location_gid": "SYN.LOC_003",
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
                "SYN.LOC_003": {"lat": -23.55, "lon": -46.63, "source": "fake:inline"}
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total_count"] == 1
    assert payload["results"][0]["status"] == "NULL_FILLED"
    assert payload["results"][0]["source"] == "fake:inline"


def test_coordinate_quality_create_batch_endpoint_persists_results(client, admin_header):
    response = client.post(
        "/api/v1/modules/master-data/coordinate-quality/batches",
        headers=admin_header,
        json={
            "records": [
                {
                    "location_gid": "SYN.LOC_004",
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
                "SYN.LOC_004": {"lat": -23.55, "lon": -46.63, "source": "fake:inline"}
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


def test_coordinate_quality_list_batches_returns_recent_state(client, admin_header):
    created = client.post(
        "/api/v1/modules/master-data/coordinate-quality/batches",
        headers=admin_header,
        json={
            "records": [
                {
                    "location_gid": "SYN.LOC_LIST",
                    "location_name": "Synthetic List DC",
                    "address_line": "Rua Quatro 400",
                    "city": "Sao Paulo",
                    "province_code": "SP",
                    "postal_code": "01000-000",
                    "country_code3_gid": "BRA",
                    "lat": None,
                    "lon": None,
                }
            ],
            "fake_candidates": {
                "SYN.LOC_LIST": {"lat": -23.55, "lon": -46.63, "source": "fake:inline"}
            },
        },
    ).json()

    response = client.get(
        "/api/v1/modules/master-data/coordinate-quality/batches",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["batch_id"] == created["batch_id"]
    assert response.json()["items"][0]["summary"]["total_count"] == 1


def test_coordinate_quality_export_creates_client_safe_evidence(client, admin_header, db_session):
    batch_response = client.post(
        "/api/v1/modules/master-data/coordinate-quality/batches",
        headers=admin_header,
        json={
            "records": [
                {
                    "location_gid": "SYN.LOC_005",
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
                "SYN.LOC_005": {"lat": -23.55, "lon": -46.63, "source": "fake:inline"}
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
