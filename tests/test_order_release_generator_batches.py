import json

from sqlalchemy import inspect

from otm_workbench.models import Artifact, Evidence
from tests.test_integration_mapping_definitions import create_project_with_environments, set_active_context


def valid_rows():
    return [
        {
            "release_gid": "OTM1.OR_SYN_001",
            "source_location_gid": "OTM1.SOURCE_A",
            "destination_location_gid": "OTM1.DEST_A",
            "early_pickup_date": "2026-05-20 08:00:00",
            "late_delivery_date": "2026-05-21 17:00:00",
            "item_gid": "OTM1.ITEM_A",
            "packaged_item_gid": "OTM1.PACK_A",
            "weight": "100",
            "weight_uom": "KG",
        },
        {
            "release_gid": "OTM1.OR_SYN_001",
            "source_location_gid": "OTM1.SOURCE_A",
            "destination_location_gid": "OTM1.DEST_A",
            "early_pickup_date": "2026-05-20 08:00:00",
            "late_delivery_date": "2026-05-21 17:00:00",
            "item_gid": "OTM1.ITEM_B",
            "packaged_item_gid": "OTM1.PACK_B",
            "weight": "55",
            "weight_uom": "KG",
        },
        {
            "release_gid": "OTM1.OR_SYN_002",
            "source_location_gid": "OTM1.SOURCE_B",
            "destination_location_gid": "OTM1.DEST_B",
            "early_pickup_date": "2026-05-22 08:00:00",
            "late_delivery_date": "2026-05-23 17:00:00",
            "item_gid": "OTM1.ITEM_C",
            "packaged_item_gid": "OTM1.PACK_C",
            "weight": "75",
            "weight_uom": "KG",
        },
    ]


def test_order_release_batch_tables_exist_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "order_release_batches" in table_names
    assert "order_release_batch_rows" in table_names


def test_create_order_release_batch_normalizes_rows_and_summary(client, admin_header):
    templates = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()
    template_id = templates["items"][0]["id"]

    response = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "synthetic_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["template_id"] == template_id
    assert payload["status"] == "VALID"
    assert payload["row_count"] == 3
    assert payload["release_count"] == 2
    assert payload["issue_count"] == 0
    assert payload["rows"][0]["row_number"] == 1
    assert payload["rows"][0]["release_gid"] == "OTM1.OR_SYN_001"
    assert payload["rows"][0]["normalized_json"]["weight_uom"] == "KG"


def test_create_order_release_batch_records_missing_required_columns_as_issues(client, admin_header):
    templates = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()
    template_id = templates["items"][0]["id"]
    rows = valid_rows()
    rows[0].pop("release_gid")

    response = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "synthetic_or.xlsx", "rows": rows},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "INVALID"
    assert payload["row_count"] == 3
    assert payload["release_count"] == 2
    assert payload["issue_count"] == 1
    assert payload["rows"][0]["status"] == "INVALID"
    assert payload["rows"][0]["issues"][0]["code"] == "MISSING_REQUIRED_COLUMN"
    assert payload["rows"][0]["issues"][0]["column"] == "release_gid"
    combined = str(payload)
    assert "cliente" not in combined.lower()
    assert "customer" not in combined.lower()


def test_get_order_release_batch_detail(client, admin_header):
    template_id = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()["items"][0]["id"]
    created = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "synthetic_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    ).json()

    response = client.get(f"/api/v1/modules/order-release-generator/batches/{created['id']}", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created["id"]
    assert len(payload["rows"]) == 3


def test_list_order_release_batches_returns_recent_backend_state(client, admin_header):
    template_id = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()["items"][0]["id"]
    created = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "synthetic_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    ).json()

    response = client.get("/api/v1/modules/order-release-generator/batches", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == created["id"]
    assert payload["items"][0]["status"] == "VALID"
    assert "rows" not in payload["items"][0]


def test_order_release_batches_follow_active_context_scope(client, admin_header):
    project_id, uat_id, dev_id = create_project_with_environments(client, admin_header)
    other_project_id, other_uat_id, _ = create_project_with_environments(client, admin_header, name_suffix=" OR Batch Other")
    template_id = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()["items"][0]["id"]
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
    )
    visible = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "visible_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    ).json()
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM2",
    )
    hidden_domain = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "hidden_domain_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    ).json()
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=dev_id,
        domain_name="OTM1",
    )
    client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "hidden_env_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    )
    set_active_context(
        client,
        admin_header,
        project_id=other_project_id,
        environment_id=other_uat_id,
        domain_name="OTM1",
    )
    hidden_project = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "hidden_project_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    ).json()
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
    )

    listed = client.get("/api/v1/modules/order-release-generator/batches", headers=admin_header)
    visible_detail = client.get(
        f"/api/v1/modules/order-release-generator/batches/{visible['id']}",
        headers=admin_header,
    )
    hidden_detail = client.get(
        f"/api/v1/modules/order-release-generator/batches/{hidden_domain['id']}",
        headers=admin_header,
    )
    hidden_preview = client.post(
        f"/api/v1/modules/order-release-generator/batches/{hidden_domain['id']}/preview-xml",
        headers=admin_header,
    )
    hidden_submit = client.post(
        f"/api/v1/modules/order-release-generator/batches/{hidden_domain['id']}/submit-otm",
        headers=admin_header,
    )
    hidden_project_detail = client.get(
        f"/api/v1/modules/order-release-generator/batches/{hidden_project['id']}",
        headers=admin_header,
    )
    hidden_project_preview = client.post(
        f"/api/v1/modules/order-release-generator/batches/{hidden_project['id']}/preview-xml",
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [visible["id"]]
    assert visible_detail.status_code == 200
    assert visible_detail.json()["project_id"] == project_id
    assert visible_detail.json()["environment_id"] == uat_id
    assert visible_detail.json()["domain_name"] == "OTM1"
    assert hidden_detail.status_code == 404
    assert hidden_preview.status_code == 404
    assert hidden_submit.status_code == 404
    assert hidden_project_detail.status_code == 404
    assert hidden_project_preview.status_code == 404


def test_order_release_batches_require_active_context_for_non_admin_access_and_create(
    client,
    admin_header,
    auth_header,
):
    template_id = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()["items"][0]["id"]
    created = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "admin_no_context_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/order-release-generator/batches", headers=auth_header)
    detail = client.get(
        f"/api/v1/modules/order-release-generator/batches/{created['id']}",
        headers=auth_header,
    )
    preview = client.post(
        f"/api/v1/modules/order-release-generator/batches/{created['id']}/preview-xml",
        headers=auth_header,
    )
    create = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "user_no_context_or.xlsx", "rows": valid_rows()},
        headers=auth_header,
    )

    assert listed.status_code == 200
    assert listed.json()["items"] == []
    assert listed.json()["total"] == 0
    assert detail.status_code == 404
    assert detail.json()["code"] == "ORDER_RELEASE_BATCH_NOT_FOUND"
    assert preview.status_code == 404
    assert create.status_code == 403
    assert create.json()["code"] == "ACTIVE_CONTEXT_REQUIRED"


def test_order_release_batch_dba_context_can_see_all_domains_in_active_environment(client, admin_header):
    project_id, uat_id, dev_id = create_project_with_environments(client, admin_header)
    template_id = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()["items"][0]["id"]
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
    )
    otm1 = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "dba_otm1_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    ).json()
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM2",
    )
    otm2 = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "dba_otm2_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    ).json()
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=dev_id,
        domain_name="OTM1",
    )
    client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "dba_other_env_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    )
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
        can_view_all_domains=True,
    )

    listed = client.get("/api/v1/modules/order-release-generator/batches", headers=admin_header)

    assert listed.status_code == 200
    assert {item["id"] for item in listed.json()["items"]} == {otm1["id"], otm2["id"]}


def test_order_release_xml_artifact_inherits_batch_scope(client, admin_header, db_session):
    project_id, uat_id, _ = create_project_with_environments(client, admin_header)
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=uat_id,
        domain_name="OTM1",
    )
    template_id = client.get("/api/v1/modules/order-release-generator/templates", headers=admin_header).json()["items"][0]["id"]
    batch = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": template_id, "file_name": "scoped_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    ).json()

    response = client.post(
        f"/api/v1/modules/order-release-generator/batches/{batch['id']}/generate-xml-artifact",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    artifact = db_session.query(Artifact).filter(Artifact.id == payload["artifact_id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    summary = json.loads(evidence.summary_json)
    listed = client.get(
        f"/api/v1/modules/order-release-generator/batches/{batch['id']}/artifacts",
        headers=admin_header,
    )

    assert artifact.project_id == project_id
    assert artifact.profile_id == batch["profile_id"]
    assert artifact.environment_id == uat_id
    assert artifact.domain_name == "OTM1"
    assert artifact.visibility == "PROJECT"
    assert evidence.project_id == project_id
    assert evidence.profile_id == batch["profile_id"]
    assert evidence.environment_id == uat_id
    assert evidence.domain_name == "OTM1"
    assert evidence.visibility == "PROJECT"
    assert evidence.artifact_id == artifact.id
    assert summary["source_entity_id"] == batch["id"]
    assert summary["release_count"] == 2
    assert listed.status_code == 200
    assert listed.json()["items"][0]["id"] == artifact.id


def test_create_order_release_batch_rejects_missing_template(client, admin_header):
    response = client.post(
        "/api/v1/modules/order-release-generator/batches",
        json={"template_id": "missing-template", "file_name": "synthetic_or.xlsx", "rows": valid_rows()},
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "ORDER_RELEASE_TEMPLATE_NOT_FOUND"
