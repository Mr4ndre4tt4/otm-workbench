import json

from sqlalchemy import inspect

from otm_workbench.models import AuditLog, CutoverChecklist, CutoverChecklistTemplate, DomainEvent, LoadPlanPackage


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


def create_synthetic_load_plan_package(
    db_session,
    *,
    project_id="project_demo",
    environment_id="env_demo",
    profile_id="profile_demo",
    domain_name="OTM1",
    suffix="",
):
    package = LoadPlanPackage(
        project_id=project_id,
        environment_id=environment_id,
        profile_id=profile_id,
        domain_name=domain_name,
        source_module="rates",
        source_entity_type="rate_batch",
        source_entity_id=f"rate_batch_demo{suffix}",
        package_type="RATES",
        status="REGISTERED",
        summary_json=json.dumps({"scenario_code": f"RATE_GEO_ONLY{suffix}"}),
        created_by="admin@example.com",
    )
    db_session.add(package)
    db_session.flush()
    return package


def create_synthetic_cutover_checklist(db_session, package, *, suffix=""):
    template = CutoverChecklistTemplate(
        code=f"SYNTHETIC_ASSETS_TEMPLATE{suffix}",
        name=f"Synthetic Assets Template{suffix}",
        version=1,
        status="PUBLISHED",
        description="Synthetic checklist template for Assets link tests.",
    )
    db_session.add(template)
    db_session.flush()
    checklist = CutoverChecklist(
        project_id=package.project_id,
        environment_id=package.environment_id,
        profile_id=package.profile_id,
        template_id=template.id,
        package_id=package.id,
        status="DRAFT",
        package_type=package.package_type,
        catalog_macro_object_code="RATE_RECORD",
        summary_json=json.dumps({"package_id": package.id}),
        created_by="admin@example.com",
    )
    db_session.add(checklist)
    db_session.flush()
    return checklist


def test_assets_table_exists_after_metadata_reset(db_session):
    inspector = inspect(db_session.bind)
    table_names = inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("assets")}

    assert "assets" in table_names
    assert "target_otm_version" in columns


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


def test_asset_target_otm_version_create_update_and_search(client, admin_header):
    matching = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(name="Synthetic 26A Asset", target_otm_version="26a"),
        headers=admin_header,
    ).json()
    secondary = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(name="Synthetic 26B Asset", target_otm_version="26B"),
        headers=admin_header,
    ).json()

    exact = client.get(
        "/api/v1/modules/assets/assets",
        params={"target_otm_version": "26A"},
        headers=admin_header,
    )
    one_of = client.get(
        "/api/v1/modules/assets/assets",
        params={"target_otm_version": "26A,26B", "target_otm_version_operator": "one_of"},
        headers=admin_header,
    )
    not_one_of = client.get(
        "/api/v1/modules/assets/assets",
        params={"target_otm_version": "26B", "target_otm_version_operator": "not_one_of"},
        headers=admin_header,
    )
    update = client.patch(
        f"/api/v1/modules/assets/assets/{matching['id']}",
        json={"target_otm_version": "26b"},
        headers=admin_header,
    )
    clear = client.patch(
        f"/api/v1/modules/assets/assets/{matching['id']}",
        json={"target_otm_version": ""},
        headers=admin_header,
    )

    assert matching["target_otm_version"] == "26A"
    assert exact.status_code == 200
    assert [item["id"] for item in exact.json()["items"]] == [matching["id"]]
    assert one_of.status_code == 200
    assert {item["id"] for item in one_of.json()["items"]} == {matching["id"], secondary["id"]}
    assert not_one_of.status_code == 200
    assert [item["id"] for item in not_one_of.json()["items"]] == [matching["id"]]
    assert update.status_code == 200
    assert update.json()["target_otm_version"] == "26B"
    assert clear.status_code == 200
    assert clear.json()["target_otm_version"] is None


def test_asset_target_otm_version_rejects_unclassified_values(client, admin_header):
    invalid_create = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(name="Synthetic Unsupported OTM Version Asset", target_otm_version="27A"),
        headers=admin_header,
    )
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(name="Synthetic Supported OTM Version Asset", target_otm_version="26A"),
        headers=admin_header,
    ).json()
    invalid_update = client.patch(
        f"/api/v1/modules/assets/assets/{created['id']}",
        json={"target_otm_version": "27A"},
        headers=admin_header,
    )
    classifications = client.get("/api/v1/modules/assets/classifications", headers=admin_header)

    assert invalid_create.status_code == 400
    create_payload = invalid_create.json()
    assert create_payload["code"] == "ASSET_CLASSIFICATION_INVALID"
    assert create_payload["details"]["field_name"] == "target_otm_version"
    assert create_payload["details"]["classification_type"] == "asset_target_otm_version"
    assert "27A" not in json.dumps(create_payload)

    assert invalid_update.status_code == 400
    update_payload = invalid_update.json()
    assert update_payload["code"] == "ASSET_METADATA_INVALID"
    assert update_payload["details"]["field_name"] == "target_otm_version"
    assert "27A" not in json.dumps(update_payload)

    version_group = next(
        group for group in classifications.json()["items"] if group["classification_type"] == "asset_target_otm_version"
    )
    assert {item["code"] for item in version_group["items"]} == {"26A", "26B"}


def test_list_assets_supports_backend_search_operators(client, admin_header):
    alpha = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic Alpha Rate Playbook",
            description="Reusable rating payload sample.",
            module_id="rates",
            macro_object_code="RATE_RECORD",
            otm_table_name="RATE_GEO_COST",
        ),
        headers=admin_header,
    ).json()
    beta = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic Beta Integration Payload",
            description="Reusable integration payload sample.",
            module_id="integration_mapping",
            macro_object_code="RATE_RECORD",
            otm_table_name="RATE_GEO_COST",
        ),
        headers=admin_header,
    ).json()
    gamma = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(
            name="Synthetic Gamma Location Notes",
            description="Location setup notes.",
            module_id="master_data",
            macro_object_code="REGION",
            otm_table_name="REGION",
        ),
        headers=admin_header,
    ).json()

    contains = client.get(
        "/api/v1/modules/assets/assets",
        params={"description": "integration payload", "description_operator": "contains"},
        headers=admin_header,
    )
    begins_with = client.get(
        "/api/v1/modules/assets/assets",
        params={"name": "synthetic gamma", "name_operator": "begins_with"},
        headers=admin_header,
    )
    one_of = client.get(
        "/api/v1/modules/assets/assets",
        params={"module_id": "rates,master_data", "module_id_operator": "one_of"},
        headers=admin_header,
    )
    not_one_of = client.get(
        "/api/v1/modules/assets/assets",
        params={"otm_table_name": "REGION", "otm_table_name_operator": "not_one_of"},
        headers=admin_header,
    )

    assert contains.status_code == 200
    assert [item["id"] for item in contains.json()["items"]] == [beta["id"]]
    assert begins_with.status_code == 200
    assert [item["id"] for item in begins_with.json()["items"]] == [gamma["id"]]
    assert one_of.status_code == 200
    assert {item["id"] for item in one_of.json()["items"]} == {alpha["id"], gamma["id"]}
    assert not_one_of.status_code == 200
    assert {item["id"] for item in not_one_of.json()["items"]} == {alpha["id"], beta["id"]}


def test_list_assets_returns_pagination_metadata(client, admin_header):
    created_ids = []
    for index in range(3):
        created = client.post(
            "/api/v1/modules/assets/assets",
            json=draft_asset_payload(name=f"Synthetic Paginated Asset {index}"),
            headers=admin_header,
        ).json()
        created_ids.append(created["id"])

    first_page = client.get(
        "/api/v1/modules/assets/assets",
        params={"page": 1, "page_size": 2},
        headers=admin_header,
    )
    second_page = client.get(
        "/api/v1/modules/assets/assets",
        params={"page": 2, "page_size": 2},
        headers=admin_header,
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert first_page.json()["total"] == 3
    assert first_page.json()["page"] == 1
    assert first_page.json()["page_size"] == 2
    assert len(first_page.json()["items"]) == 2
    assert second_page.json()["total"] == 3
    assert second_page.json()["page"] == 2
    assert second_page.json()["page_size"] == 2
    assert len(second_page.json()["items"]) == 1
    assert {item["id"] for item in first_page.json()["items"] + second_page.json()["items"]} == set(created_ids)


def test_list_assets_rejects_invalid_search_operator(client, admin_header):
    client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(name="Synthetic Operator Guard Asset"),
        headers=admin_header,
    )

    response = client.get(
        "/api/v1/modules/assets/assets",
        params={"name": "synthetic", "name_operator": "regex"},
        headers=admin_header,
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "ASSET_SEARCH_INVALID_OPERATOR"
    assert payload["details"]["field_name"] == "name"


def test_list_assets_filters_by_linked_target_type(client, admin_header):
    module_linked = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(name="Synthetic Module Linked Asset"),
        headers=admin_header,
    ).json()
    table_linked = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(name="Synthetic Table Linked Asset"),
        headers=admin_header,
    ).json()
    unlinked = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(name="Synthetic Unlinked Asset"),
        headers=admin_header,
    ).json()
    client.post(
        f"/api/v1/modules/assets/assets/{module_linked['id']}/links",
        json={"link_type": "MODULE", "target_id": "assets", "target_label": "Assets Library"},
        headers=admin_header,
    )
    client.post(
        f"/api/v1/modules/assets/assets/{table_linked['id']}/links",
        json={"link_type": "OTM_TABLE", "target_id": "RATE_GEO_COST", "target_label": "Rate Geo Cost"},
        headers=admin_header,
    )

    module_response = client.get(
        "/api/v1/modules/assets/assets",
        params={"linked_target_type": "module"},
        headers=admin_header,
    )
    one_of_response = client.get(
        "/api/v1/modules/assets/assets",
        params={"linked_target_type": "module,otm_table", "linked_target_type_operator": "one_of"},
        headers=admin_header,
    )
    not_one_of_response = client.get(
        "/api/v1/modules/assets/assets",
        params={"linked_target_type": "otm_table", "linked_target_type_operator": "not_one_of"},
        headers=admin_header,
    )

    assert module_response.status_code == 200
    assert [item["id"] for item in module_response.json()["items"]] == [module_linked["id"]]
    assert one_of_response.status_code == 200
    assert {item["id"] for item in one_of_response.json()["items"]} == {module_linked["id"], table_linked["id"]}
    assert not_one_of_response.status_code == 200
    assert {item["id"] for item in not_one_of_response.json()["items"]} == {module_linked["id"], unlinked["id"]}


def test_list_assets_rejects_invalid_linked_target_type_operator(client, admin_header):
    response = client.get(
        "/api/v1/modules/assets/assets",
        params={"linked_target_type": "module", "linked_target_type_operator": "regex"},
        headers=admin_header,
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "ASSET_SEARCH_INVALID_OPERATOR"
    assert payload["details"]["field_name"] == "linked_target_type"


def test_batch_and_checklist_link_targets_are_backend_owned(client, admin_header, db_session):
    asset = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()
    package = create_synthetic_load_plan_package(db_session)
    checklist = create_synthetic_cutover_checklist(db_session, package)
    db_session.commit()

    batch_link = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/links",
        json={"link_type": "BATCH", "target_id": package.id, "target_label": "Synthetic load package"},
        headers=admin_header,
    )
    checklist_link = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/links",
        json={"link_type": "CHECKLIST", "target_id": checklist.id, "target_label": "Synthetic cutover checklist"},
        headers=admin_header,
    )
    classifications = client.get("/api/v1/modules/assets/classifications", headers=admin_header)

    assert batch_link.status_code == 200
    assert batch_link.json()["link_type"] == "BATCH"
    assert batch_link.json()["target_id"] == package.id
    assert checklist_link.status_code == 200
    assert checklist_link.json()["link_type"] == "CHECKLIST"
    link_types = next(group for group in classifications.json()["items"] if group["classification_type"] == "asset_link_type")
    assert {"BATCH", "CHECKLIST"}.issubset({item["code"] for item in link_types["items"]})


def test_batch_and_checklist_link_targets_are_rejected_when_outside_scope(client, admin_header, db_session):
    project_id, environment_id = create_project_environment(client, admin_header, name_suffix=" Visible Links")
    other_project_id, other_environment_id = create_project_environment(client, admin_header, name_suffix=" Hidden Links")
    set_active_context(
        client,
        admin_header,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )
    asset = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(project_id=None, environment_id=None, profile_id=None, domain_name=None),
        headers=admin_header,
    ).json()
    hidden_package = create_synthetic_load_plan_package(
        db_session,
        project_id=other_project_id,
        environment_id=other_environment_id,
        profile_id=None,
        domain_name="OTM2",
        suffix="_hidden",
    )
    hidden_checklist = create_synthetic_cutover_checklist(db_session, hidden_package, suffix="_hidden")
    db_session.commit()

    hidden_batch_link = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/links",
        json={"link_type": "BATCH", "target_id": hidden_package.id, "target_label": "Hidden load package"},
        headers=admin_header,
    )
    hidden_checklist_link = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/links",
        json={"link_type": "CHECKLIST", "target_id": hidden_checklist.id, "target_label": "Hidden cutover checklist"},
        headers=admin_header,
    )

    assert hidden_batch_link.status_code == 400
    assert hidden_batch_link.json()["code"] == "ASSET_LINK_INVALID_BATCH"
    assert hidden_package.id not in hidden_batch_link.text
    assert "Hidden" not in hidden_batch_link.text
    assert hidden_checklist_link.status_code == 400
    assert hidden_checklist_link.json()["code"] == "ASSET_LINK_INVALID_CHECKLIST"
    assert hidden_checklist.id not in hidden_checklist_link.text
    assert "Hidden" not in hidden_checklist_link.text


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


def test_route_optimized_asset_detail_includes_versions_links_actions_and_archive_impact(
    client,
    admin_header,
):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()
    client.post(
        f"/api/v1/modules/assets/assets/{created['id']}/versions",
        files={"file": ("synthetic_mapping_spec.md", b"# synthetic asset\n", "text/markdown")},
        headers=admin_header,
    )
    client.post(
        f"/api/v1/modules/assets/assets/{created['id']}/links",
        json={"link_type": "MODULE", "target_id": "assets", "target_label": "Assets Library"},
        headers=admin_header,
    )

    response = client.get(
        f"/api/v1/modules/assets/assets/{created['id']}/detail",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["asset"]["id"] == created["id"]
    assert payload["current_version"]["file_name"] == "synthetic_mapping_spec.md"
    assert payload["versions"][0]["file_name"] == "synthetic_mapping_spec.md"
    assert payload["links"][0]["target_label"] == "Assets Library"
    assert {action["key"] for action in payload["available_actions"]} >= {
        "asset.update",
        "asset.upload_version",
        "asset.create_link",
        "asset.download_current",
        "asset.archive",
    }
    impact = payload["archive_impact"]
    assert impact["eligible"] is True
    assert impact["disabled_reason"] is None
    assert impact["impacted_versions"] == 1
    assert impact["current_version_id"] == payload["current_version"]["id"]
    assert impact["impacted_links"] == 1
    assert impact["linked_target_types"] == ["MODULE"]
    assert impact["will_disable_actions"] == [
        "asset.update",
        "asset.upload_version",
        "asset.create_link",
        "asset.archive",
    ]
    assert "storage_path" not in str(payload)


def test_archive_impact_reports_disabled_facts_for_archived_asset(client, admin_header):
    created = client.post(
        "/api/v1/modules/assets/assets",
        json=draft_asset_payload(),
        headers=admin_header,
    ).json()
    active_impact = client.get(
        f"/api/v1/modules/assets/assets/{created['id']}/archive-impact",
        headers=admin_header,
    )
    client.post(f"/api/v1/modules/assets/assets/{created['id']}/archive", headers=admin_header)
    archived_impact = client.get(
        f"/api/v1/modules/assets/assets/{created['id']}/archive-impact",
        headers=admin_header,
    )

    assert active_impact.status_code == 200
    assert active_impact.json()["eligible"] is True
    assert active_impact.json()["archive_action"]["disabled"] is False

    assert archived_impact.status_code == 200
    payload = archived_impact.json()
    assert payload["eligible"] is False
    assert payload["disabled_reason"] == "ASSET_ARCHIVED"
    assert payload["blocked_reasons"] == ["ASSET_ARCHIVED"]
    assert payload["archive_action"]["disabled"] is True
    assert payload["archive_action"]["disabled_reason"] == "ASSET_ARCHIVED"


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
