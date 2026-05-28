import json

from sqlalchemy import inspect

from otm_workbench.models import AuditLog, DomainEvent


def draft_asset_payload(**overrides):
    payload = {
        "name": "Synthetic OTM Mapping Spec",
        "description": "Client-safe synthetic support asset.",
        "asset_type": "SPEC",
        "category": "INTEGRATION",
        "visibility": "PROJECT",
        "scope_type": "PROJECT",
        "sensitivity": "INTERNAL",
        "project_id": "project_demo",
        "profile_id": "profile_demo",
        "environment_id": "env_demo",
        "domain_name": "otm1",
        "access_policy_id": "policy_assets_demo",
        "module_id": "assets",
        "macro_object_code": "RATE_RECORD",
        "otm_table_name": "RATE_GEO_COST",
        "tags": ["SYNTHETIC", "MVP0"],
    }
    payload.update(overrides)
    return payload


def create_project_environment(client, admin_header, *, name_suffix=""):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": f"Synthetic Assets Workspace{name_suffix}"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": f"Synthetic Assets Project{name_suffix}"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "UAT", "environment_type": "UAT"},
        headers=admin_header,
    ).json()
    return project["id"], environment["id"]


def set_active_context(
    client,
    admin_header,
    *,
    project_id,
    environment_id,
    domain_name,
    can_view_all_domains=False,
):
    response = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project_id,
            "environment_id": environment_id,
            "domain_name": domain_name,
            "can_view_all_domains": can_view_all_domains,
        },
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def test_assets_table_exists_after_metadata_reset(db_session):
    table_names = inspect(db_session.bind).get_table_names()

    assert "assets" in table_names


def test_create_draft_asset_records_metadata_audit_and_event(client, admin_header, db_session):
    response = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    )

    assert response.status_code == 200
    asset = response.json()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "assets.asset.create").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "assets.asset.created").one()

    assert asset["status"] == "DRAFT"
    assert asset["asset_type"] == "SPEC"
    assert asset["category"] == "INTEGRATION"
    assert asset["visibility"] == "PROJECT"
    assert asset["scope_type"] == "PROJECT"
    assert asset["sensitivity"] == "INTERNAL"
    assert asset["project_id"] == "project_demo"
    assert asset["profile_id"] == "profile_demo"
    assert asset["environment_id"] == "env_demo"
    assert asset["domain_name"] == "OTM1"
    assert asset["access_policy_id"] == "policy_assets_demo"
    assert asset["tags"] == ["SYNTHETIC", "MVP0"]
    actions = {action["key"]: action for action in asset["available_actions"]}
    assert actions["asset.update"]["disabled"] is False
    assert actions["asset.upload_version"]["disabled"] is False
    assert actions["asset.create_link"]["disabled"] is False
    assert actions["asset.download_current"]["disabled"] is True
    assert actions["asset.download_current"]["disabled_reason"] == "NO_CURRENT_VERSION"
    assert actions["asset.archive"]["requires_confirmation"] is True
    assert json.loads(audit.metadata_json)["asset_id"] == asset["id"]
    assert json.loads(event.payload_json)["asset_id"] == asset["id"]

    combined = "\n".join([json.dumps(asset, sort_keys=True), audit.metadata_json, event.payload_json])
    assert "customer" not in combined.lower()
    assert "cliente" not in combined.lower()


def test_create_asset_inherits_active_context_when_scope_is_omitted(client, admin_header):
    project_id, environment_id = create_project_environment(client, admin_header, name_suffix=" Create Scope")
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )

    response = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            project_id=None,
            profile_id=None,
            environment_id=None,
            domain_name=None,
            access_policy_id=None,
        ),
        headers=admin_header,
    )

    assert response.status_code == 200
    asset = response.json()
    detail = client.get(f"/api/v1/modules/assets/assets/{asset['id']}", headers=admin_header)

    assert asset["project_id"] == project_id
    assert asset["environment_id"] == environment_id
    assert asset["domain_name"] == "OTM1"
    assert detail.status_code == 200
    assert detail.json()["id"] == asset["id"]


def test_create_draft_asset_rejects_unknown_classification(client, admin_header):
    response = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(asset_type="UNKNOWN"),
        headers=admin_header,
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "ASSET_CLASSIFICATION_INVALID"
    assert "asset_type" in payload["message"]
    assert payload["details"]["field_name"] == "asset_type"
    assert payload["details"]["classification_type"] == "asset_type"
    assert "SPEC" in payload["details"]["allowed_codes"]
    assert "UNKNOWN" not in json.dumps(payload)


def test_create_global_asset_rejects_secret_like_metadata(client, admin_header):
    response = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            scope_type="GLOBAL",
            description="Synthetic example with password=ChangeMe123!",
        ),
        headers=admin_header,
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "ASSET_SECRET_RISK"
    assert "secret" in payload["message"].lower()
    assert "ChangeMe123" not in payload["message"]


def test_create_draft_asset_rejects_invalid_otm_references(client, admin_header):
    invalid_macro = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(macro_object_code="NOT_A_MACRO_OBJECT"),
        headers=admin_header,
    )
    invalid_table = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(macro_object_code="RATE_RECORD", otm_table_name="NOT_A_REAL_OTM_TABLE"),
        headers=admin_header,
    )

    assert invalid_macro.status_code == 400
    macro_payload = invalid_macro.json()
    assert macro_payload["code"] == "ASSET_METADATA_INVALID"
    assert macro_payload["details"]["field_name"] == "macro_object_code"
    assert "macro object" in macro_payload["message"].lower()

    assert invalid_table.status_code == 400
    table_payload = invalid_table.json()
    assert table_payload["code"] == "ASSET_METADATA_INVALID"
    assert table_payload["details"]["field_name"] == "otm_table_name"
    assert "data dictionary" in table_payload["message"].lower()


def test_list_and_detail_assets_with_filters(client, admin_header):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(name="Synthetic Test Template", asset_type="TEMPLATE", category="TESTING"),
        headers=admin_header,
    )

    listed = client.get(
        "/api/v1/modules/assets/assets",
        params={"asset_type": "SPEC", "category": "INTEGRATION", "status": "DRAFT"},
        headers=admin_header,
    )
    detail = client.get(f"/api/v1/modules/assets/assets/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert detail.status_code == 200
    assert detail.json()["id"] == created["id"]


def test_asset_routes_follow_active_context_scope(client, admin_header):
    project_id, environment_id = create_project_environment(client, admin_header)
    other_project_id, other_environment_id = create_project_environment(client, admin_header, name_suffix=" Other")
    visible = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            project_id=project_id,
            environment_id=environment_id,
            domain_name="OTM1",
        ),
        headers=admin_header,
    ).json()
    hidden_domain = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic Hidden Domain Asset",
            project_id=project_id,
            environment_id=environment_id,
            domain_name="OTM2",
        ),
        headers=admin_header,
    ).json()
    hidden_project = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic Hidden Project Asset",
            project_id=other_project_id,
            environment_id=other_environment_id,
            domain_name="OTM1",
        ),
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic Hidden Environment Asset",
            project_id=project_id,
            environment_id="env_dev",
            domain_name="OTM1",
        ),
        headers=admin_header,
    )
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )

    listed = client.get("/api/v1/modules/assets/assets", headers=admin_header)
    visible_detail = client.get(f"/api/v1/modules/assets/assets/{visible['id']}", headers=admin_header)
    hidden_detail = client.get(f"/api/v1/modules/assets/assets/{hidden_domain['id']}", headers=admin_header)
    hidden_update = client.patch(
        f"/api/v1/modules/assets/assets/{hidden_domain['id']}",
        json={"name": "Synthetic Hidden Domain Asset Updated"},
        headers=admin_header,
    )
    hidden_archive = client.post(
        f"/api/v1/modules/assets/assets/{hidden_domain['id']}/archive",
        headers=admin_header,
    )
    hidden_link_create = client.post(
        f"/api/v1/modules/assets/assets/{hidden_domain['id']}/links",
        json={"link_type": "OTM_TABLE", "target_id": "RATE_GEO_COST", "target_label": "Rate Geo Cost"},
        headers=admin_header,
    )
    hidden_link_list = client.get(
        f"/api/v1/modules/assets/assets/{hidden_domain['id']}/links",
        headers=admin_header,
    )
    hidden_version_upload = client.post(
        f"/api/v1/modules/assets/assets/{hidden_domain['id']}/versions",
        files={"file": ("hidden.md", b"# hidden synthetic asset\n", "text/markdown")},
        headers=admin_header,
    )
    hidden_version_list = client.get(
        f"/api/v1/modules/assets/assets/{hidden_domain['id']}/versions",
        headers=admin_header,
    )
    hidden_download = client.get(
        f"/api/v1/modules/assets/assets/{hidden_domain['id']}/download",
        headers=admin_header,
    )
    hidden_project_detail = client.get(
        f"/api/v1/modules/assets/assets/{hidden_project['id']}",
        headers=admin_header,
    )
    hidden_project_link_list = client.get(
        f"/api/v1/modules/assets/assets/{hidden_project['id']}/links",
        headers=admin_header,
    )
    hidden_project_version_list = client.get(
        f"/api/v1/modules/assets/assets/{hidden_project['id']}/versions",
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [visible["id"]]
    assert visible_detail.status_code == 200
    assert visible_detail.json()["id"] == visible["id"]
    assert hidden_detail.status_code == 404
    assert hidden_update.status_code == 404
    assert hidden_archive.status_code == 404
    assert hidden_link_create.status_code == 404
    assert hidden_link_list.status_code == 404
    assert hidden_version_upload.status_code == 404
    assert hidden_version_list.status_code == 404
    assert hidden_download.status_code == 404
    assert hidden_project_detail.status_code == 404
    assert hidden_project_link_list.status_code == 404
    assert hidden_project_version_list.status_code == 404


def test_asset_routes_hide_operational_assets_for_non_admin_without_active_context(
    client,
    admin_header,
    auth_header,
):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/assets/assets", headers=auth_header)
    detail = client.get(f"/api/v1/modules/assets/assets/{created['id']}", headers=auth_header)
    links = client.get(f"/api/v1/modules/assets/assets/{created['id']}/links", headers=auth_header)
    versions = client.get(f"/api/v1/modules/assets/assets/{created['id']}/versions", headers=auth_header)
    download = client.get(f"/api/v1/modules/assets/assets/{created['id']}/download", headers=auth_header)

    assert listed.status_code == 200
    assert listed.json()["items"] == []
    assert listed.json()["total"] == 0
    assert detail.status_code == 404
    assert detail.json()["code"] == "ASSET_NOT_FOUND"
    assert links.status_code == 404
    assert versions.status_code == 404
    assert download.status_code == 404


def test_asset_dba_context_can_see_all_domains_in_active_environment(client, admin_header):
    project_id, environment_id = create_project_environment(client, admin_header)
    otm1 = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic OTM1 Asset",
            project_id=project_id,
            environment_id=environment_id,
            domain_name="OTM1",
        ),
        headers=admin_header,
    ).json()
    otm2 = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic OTM2 Asset",
            project_id=project_id,
            environment_id=environment_id,
            domain_name="OTM2",
        ),
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic Other Environment Asset",
            project_id=project_id,
            environment_id="env_dev",
            domain_name="OTM3",
        ),
        headers=admin_header,
    )
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
        can_view_all_domains=True,
    )

    listed = client.get("/api/v1/modules/assets/assets", headers=admin_header)

    assert listed.status_code == 200
    assert {item["id"] for item in listed.json()["items"]} == {otm1["id"], otm2["id"]}


def test_list_assets_filters_by_scope_tag_and_module(client, admin_header):
    matching = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic Mapping Payload",
            scope_type="MODULE",
            module_id="integration_mapping",
            tags=["PAYLOAD", "SYNTHETIC"],
        ),
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic Master Data Template",
            scope_type="PROJECT",
            module_id="master_data",
            tags=["TEMPLATE"],
        ),
        headers=admin_header,
    )

    response = client.get(
        "/api/v1/modules/assets/assets",
        params={"scope_type": "module", "tag": "payload", "module_id": "integration_mapping"},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == matching["id"]


def test_list_assets_filters_by_macro_object_and_otm_table(client, admin_header):
    matching = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic Rate Table Notes",
            macro_object_code="RATE_RECORD",
            otm_table_name="RATE_GEO_COST",
        ),
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic Order Release Notes",
            macro_object_code="REGION",
            otm_table_name="REGION",
        ),
        headers=admin_header,
    )

    response = client.get(
        "/api/v1/modules/assets/assets",
        params={"macro_object_code": "rate_record", "otm_table_name": "rate_geo_cost"},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == matching["id"]


def test_update_asset_metadata_records_audit_and_event(client, admin_header, db_session):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()

    response = client.patch(
        f"/api/v1/modules/assets/assets/{created['id']}",
        json={
            "name": "Synthetic Updated Mapping Spec",
            "category": "TESTING",
            "sensitivity": "PUBLIC",
            "tags": ["UPDATED", "SYNTHETIC"],
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "assets.asset.update").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "assets.asset.updated").one()
    assert payload["name"] == "Synthetic Updated Mapping Spec"
    assert payload["category"] == "TESTING"
    assert payload["sensitivity"] == "PUBLIC"
    assert payload["tags"] == ["UPDATED", "SYNTHETIC"]
    assert json.loads(audit.metadata_json)["asset_id"] == created["id"]
    assert json.loads(event.payload_json)["changed_fields"] == [
        "category",
        "name",
        "sensitivity",
        "tags",
    ]

    combined = "\n".join([json.dumps(payload, sort_keys=True), audit.metadata_json, event.payload_json])
    assert "customer" not in combined.lower()
    assert "cliente" not in combined.lower()


def test_update_asset_metadata_rejects_unknown_classification(client, admin_header):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()

    response = client.patch(
        f"/api/v1/modules/assets/assets/{created['id']}",
        json={"category": "UNKNOWN"},
        headers=admin_header,
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "ASSET_METADATA_INVALID"
    assert "category" in payload["message"]
    assert payload["details"]["field_name"] == "category"
    assert payload["details"]["classification_type"] == "asset_category"
    assert "INTEGRATION" in payload["details"]["allowed_codes"]
    assert "UNKNOWN" not in json.dumps(payload)


def test_update_global_asset_rejects_secret_like_metadata(client, admin_header):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(scope_type="PROJECT", description="Synthetic safe metadata."),
        headers=admin_header,
    ).json()

    response = client.patch(
        f"/api/v1/modules/assets/assets/{created['id']}",
        json={"scope_type": "GLOBAL", "description": "Synthetic token=abcd1234abcd1234abcd1234"},
        headers=admin_header,
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "ASSET_SECRET_RISK"
    assert "abcd1234" not in payload["message"]


def test_update_asset_metadata_rejects_invalid_otm_references(client, admin_header):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()

    invalid_macro = client.patch(
        f"/api/v1/modules/assets/assets/{created['id']}",
        json={"macro_object_code": "NOT_A_MACRO_OBJECT"},
        headers=admin_header,
    )
    invalid_table = client.patch(
        f"/api/v1/modules/assets/assets/{created['id']}",
        json={"otm_table_name": "NOT_A_REAL_OTM_TABLE"},
        headers=admin_header,
    )

    assert invalid_macro.status_code == 400
    assert invalid_macro.json()["code"] == "ASSET_METADATA_INVALID"
    assert invalid_macro.json()["details"]["field_name"] == "macro_object_code"

    assert invalid_table.status_code == 400
    assert invalid_table.json()["code"] == "ASSET_METADATA_INVALID"
    assert invalid_table.json()["details"]["field_name"] == "otm_table_name"


def test_archive_asset_preserves_record_and_records_audit_event(client, admin_header, db_session):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()

    response = client.post(
        f"/api/v1/modules/assets/assets/{created['id']}/archive",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "assets.asset.archive").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "assets.asset.archived").one()
    assert payload["id"] == created["id"]
    assert payload["status"] == "ARCHIVED"
    actions = {action["key"]: action for action in payload["available_actions"]}
    assert actions["asset.update"]["disabled"] is True
    assert actions["asset.update"]["disabled_reason"] == "ASSET_ARCHIVED"
    assert actions["asset.upload_version"]["disabled"] is True
    assert actions["asset.create_link"]["disabled"] is True
    assert actions["asset.archive"]["disabled"] is True
    assert json.loads(audit.metadata_json)["asset_id"] == created["id"]
    assert json.loads(event.payload_json)["status"] == "ARCHIVED"


def test_update_archived_asset_metadata_is_rejected(client, admin_header):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()
    client.post(f"/api/v1/modules/assets/assets/{created['id']}/archive", headers=admin_header)

    response = client.patch(
        f"/api/v1/modules/assets/assets/{created['id']}",
        json={"name": "Synthetic Archived Asset Update"},
        headers=admin_header,
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["code"] == "ASSET_ARCHIVED"
    assert "archived" in payload["message"].lower()
