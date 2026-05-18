import json
from pathlib import Path
import zipfile


def create_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    return client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic export batch", "domain_name": "OTM1"},
        headers=admin_header,
    ).json()


def add_accessorial_table(client, admin_header, batch_id):
    return client.post(
        f"/api/v1/modules/rates/batches/{batch_id}/tables",
        json={
            "tables": [
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": "OTM1.ACC_COST_001",
                            "ACCESSORIAL_COST_XID": "ACC_COST_001",
                        }
                    ],
                }
            ]
        },
        headers=admin_header,
    )


def test_export_rejects_unvalidated_batch(client, admin_header):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "validated" in response.json()["message"].lower()


def test_export_rejects_batch_with_error_issues(client, admin_header):
    batch = create_batch(client, admin_header, scenario_code="RATE_GEO_ONLY")
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "error" in response.json()["message"].lower()


def test_export_creates_zip_with_manifest_and_csv(client, admin_header):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    preview = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview",
        headers=admin_header,
    )
    assert preview.status_code == 200

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    zip_path = Path(payload["file_path"])
    assert zip_path.exists()
    assert payload["file_name"].endswith(".zip")
    assert payload["tables"] == ["ACCESSORIAL_COST"]

    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        assert "manifest.json" in names
        assert "csv/001_ACCESSORIAL_COST.csv" in names
        csv_text = archive.read("csv/001_ACCESSORIAL_COST.csv").decode("utf-8")
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

    assert csv_text.splitlines()[0] == "ACCESSORIAL_COST"
    assert csv_text.splitlines()[1].startswith("ACCESSORIAL_COST_GID")
    assert manifest["manifest_type"] == "rates_csv_export"
    assert manifest["batch"]["id"] == batch["id"]
    assert "OTM1.ACC_COST_001" not in json.dumps(manifest)
