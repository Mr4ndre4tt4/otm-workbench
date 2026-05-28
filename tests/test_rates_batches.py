from otm_workbench.models import (
    Capability,
    RateBatch,
    RateBatchIssue,
    RateBatchRow,
    RateBatchTable,
    Role,
    RoleCapability,
    SessionToken,
    UserProjectRole,
)


def test_rate_batch_models_persist(db_session):
    batch = RateBatch(
        project_id="project_otm1",
        environment_id="uat",
        profile_id="profile_otm1",
        scenario_code="RATE_GEO_ONLY",
        name="Synthetic rate geo batch",
        domain_name="OTM1",
        source_type="api",
        created_by="codex",
    )
    db_session.add(batch)
    db_session.flush()

    table = RateBatchTable(
        batch_id=batch.id,
        table_name="RATE_GEO",
        sequence_index=4,
        requirement_level="REQUIRED",
        row_count=1,
        status="PENDING",
    )
    db_session.add(table)
    db_session.flush()

    row = RateBatchRow(
        batch_id=batch.id,
        batch_table_id=table.id,
        table_name="RATE_GEO",
        row_index=1,
        row_payload_json='{"RATE_GEO_GID": "OTM1.RG_DEMO_001"}',
        normalized_payload_json='{"RATE_GEO_GID": "OTM1.RG_DEMO_001"}',
        row_hash="hash",
        status="PENDING",
    )
    db_session.add(row)
    db_session.flush()

    issue = RateBatchIssue(
        batch_id=batch.id,
        batch_table_id=table.id,
        batch_row_id=row.id,
        severity="INFO",
        issue_code="ROW_ACCEPTED",
        table_name="RATE_GEO",
        column_name="RATE_GEO_GID",
        message="Row accepted.",
        details_json="{}",
    )
    db_session.add(issue)
    db_session.commit()

    assert db_session.query(RateBatch).count() == 1
    assert db_session.query(RateBatchTable).count() == 1
    assert db_session.query(RateBatchRow).count() == 1
    assert db_session.query(RateBatchIssue).count() == 1


def test_create_rate_batch_api(client, admin_header):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": "RATE_GEO_ONLY",
            "name": "Synthetic rate geo package",
            "domain_name": "OTM1",
            "project_id": "project_otm1",
            "environment_id": "uat",
            "profile_id": "profile_otm1",
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_code"] == "RATE_GEO_ONLY"
    assert payload["status"] == "DRAFT"
    assert payload["domain_name"] == "OTM1"


def test_add_rate_batch_tables_api_sorts_by_rates_sequence(client, admin_header):
    created = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": "RATE_GEO_ONLY",
            "name": "Synthetic rate geo package",
            "domain_name": "OTM1",
        },
        headers=admin_header,
    ).json()

    response = client.post(
        f"/api/v1/modules/rates/batches/{created['id']}/tables",
        json={
            "tables": [
                {
                    "table_name": "RATE_GEO_COST",
                    "rows": [
                        {
                            "RATE_GEO_COST_GROUP_GID": "OTM1.RGCG_001",
                            "CHARGE_AMOUNT": 10,
                        }
                    ],
                },
                {
                    "table_name": "X_LANE",
                    "rows": [{"X_LANE_GID": "OTM1.RG_001", "X_LANE_XID": "RG_001"}],
                },
            ]
        },
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["batch_id"] == created["id"]
    assert response.json()["catalog_macro_object_code"] == "RATE_RECORD"
    assert response.json()["catalog_load_plan_path"] == "/api/v1/catalog/macro-objects/RATE_RECORD/load-plan"
    assert [item["table_name"] for item in response.json()["tables"]] == [
        "X_LANE",
        "RATE_GEO_COST",
    ]


def create_project_environment_context(
    client,
    admin_header,
    *,
    domain_name,
    can_view_all_domains=False,
    name_suffix="",
    set_context=True,
):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": f"Synthetic Rates Workspace{name_suffix}"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": f"Synthetic Rates Project{name_suffix}"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "UAT", "environment_type": "UAT"},
        headers=admin_header,
    ).json()
    if set_context:
        context = client.post(
            "/api/v1/platform/active-context",
            json={
                "project_id": project["id"],
                "environment_id": environment["id"],
                "domain_name": domain_name,
                "can_view_all_domains": can_view_all_domains,
            },
            headers=admin_header,
        )
        assert context.status_code == 200
    return project["id"], environment["id"]


def create_scoped_rate_batch(client, admin_header, *, name, project_id, environment_id, domain_name):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": "RATE_GEO_ONLY",
            "name": name,
            "domain_name": domain_name,
            "project_id": project_id,
            "environment_id": environment_id,
        },
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def test_rate_batches_list_and_detail_follow_active_context_scope(client, admin_header):
    project_id, environment_id = create_project_environment_context(
        client,
        admin_header,
        domain_name="OTM1",
    )
    visible = create_scoped_rate_batch(
        client,
        admin_header,
        name="Visible scoped rates",
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )
    hidden_domain = create_scoped_rate_batch(
        client,
        admin_header,
        name="Hidden domain rates",
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM2",
    )
    other_project_id, other_environment_id = create_project_environment_context(
        client,
        admin_header,
        domain_name="OTM1",
        name_suffix=" Other",
        set_context=False,
    )
    hidden_project = create_scoped_rate_batch(
        client,
        admin_header,
        name="Hidden project rates",
        project_id=other_project_id,
        environment_id=other_environment_id,
        domain_name="OTM1",
    )
    create_scoped_rate_batch(
        client,
        admin_header,
        name="Hidden environment rates",
        project_id=project_id,
        environment_id="env_dev",
        domain_name="OTM1",
    )

    listed = client.get("/api/v1/modules/rates/batches", headers=admin_header)
    visible_detail = client.get(
        f"/api/v1/modules/rates/batches/{visible['id']}",
        headers=admin_header,
    )
    hidden_detail = client.get(f"/api/v1/modules/rates/batches/{hidden_domain['id']}", headers=admin_header)
    hidden_readiness = client.get(
        f"/api/v1/modules/rates/batches/{hidden_domain['id']}/readiness",
        headers=admin_header,
    )
    hidden_issues = client.get(
        f"/api/v1/modules/rates/batches/{hidden_domain['id']}/issues",
        headers=admin_header,
    )
    hidden_tables = client.post(
        f"/api/v1/modules/rates/batches/{hidden_domain['id']}/tables",
        json={
            "tables": [
                {
                    "table_name": "X_LANE",
                    "rows": [{"X_LANE_GID": "OTM2.RG_001", "X_LANE_XID": "RG_001"}],
                }
            ]
        },
        headers=admin_header,
    )
    hidden_project_detail = client.get(f"/api/v1/modules/rates/batches/{hidden_project['id']}", headers=admin_header)
    hidden_project_readiness = client.get(
        f"/api/v1/modules/rates/batches/{hidden_project['id']}/readiness",
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [visible["id"]]
    assert visible_detail.status_code == 200
    assert visible_detail.json()["id"] == visible["id"]
    assert hidden_detail.status_code == 404
    assert hidden_readiness.status_code == 404
    assert hidden_issues.status_code == 404
    assert hidden_tables.status_code == 404
    assert hidden_project_detail.status_code == 404
    assert hidden_project_readiness.status_code == 404


def test_rate_batches_same_name_are_isolated_by_domain_and_environment(client, admin_header):
    project_id, environment_id = create_project_environment_context(
        client,
        admin_header,
        domain_name="OTM1",
    )
    other_environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project_id, "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    shared_name = "Shared tariff upload"
    visible = create_scoped_rate_batch(
        client,
        admin_header,
        name=shared_name,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )
    hidden_domain = create_scoped_rate_batch(
        client,
        admin_header,
        name=shared_name,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM2",
    )
    hidden_environment = create_scoped_rate_batch(
        client,
        admin_header,
        name=shared_name,
        project_id=project_id,
        environment_id=other_environment["id"],
        domain_name="OTM1",
    )

    listed = client.get("/api/v1/modules/rates/batches", headers=admin_header)
    visible_detail = client.get(
        f"/api/v1/modules/rates/batches/{visible['id']}",
        headers=admin_header,
    )
    hidden_domain_detail = client.get(
        f"/api/v1/modules/rates/batches/{hidden_domain['id']}",
        headers=admin_header,
    )
    hidden_environment_detail = client.get(
        f"/api/v1/modules/rates/batches/{hidden_environment['id']}",
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert [(item["id"], item["name"]) for item in listed.json()["items"]] == [
        (visible["id"], shared_name)
    ]
    assert visible_detail.status_code == 200
    assert visible_detail.json()["id"] == visible["id"]
    assert hidden_domain_detail.status_code == 404
    assert hidden_environment_detail.status_code == 404


def test_rate_batches_dba_same_name_all_domains_still_follow_active_environment(client, admin_header):
    project_id, environment_id = create_project_environment_context(
        client,
        admin_header,
        domain_name="OTM1",
        can_view_all_domains=True,
    )
    other_environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project_id, "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    shared_name = "Shared DBA tariff upload"
    otm1 = create_scoped_rate_batch(
        client,
        admin_header,
        name=shared_name,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )
    otm2 = create_scoped_rate_batch(
        client,
        admin_header,
        name=shared_name,
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM2",
    )
    hidden_environment = create_scoped_rate_batch(
        client,
        admin_header,
        name=shared_name,
        project_id=project_id,
        environment_id=other_environment["id"],
        domain_name="OTM3",
    )

    listed = client.get("/api/v1/modules/rates/batches", headers=admin_header)
    hidden_detail = client.get(
        f"/api/v1/modules/rates/batches/{hidden_environment['id']}",
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert {item["id"] for item in listed.json()["items"]} == {otm1["id"], otm2["id"]}
    assert all(item["name"] == shared_name for item in listed.json()["items"])
    assert hidden_detail.status_code == 404


def test_rate_batch_table_detail_returns_rows_and_table_issues(client, admin_header):
    project_id, environment_id = create_project_environment_context(
        client,
        admin_header,
        domain_name="OTM1",
    )
    batch = create_scoped_rate_batch(
        client,
        admin_header,
        name="Table detail rates",
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )
    tables = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables",
        json={
            "tables": [
                {
                    "table_name": "X_LANE",
                    "rows": [
                        {
                            "X_LANE_GID": "OTM1.XL_DETAIL_001",
                            "X_LANE_XID": "XL_DETAIL_001",
                        }
                    ],
                }
            ]
        },
        headers=admin_header,
    )
    assert tables.status_code == 200

    detail = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables/X_LANE",
        headers=admin_header,
    )
    missing = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/tables/RATE_GEO",
        headers=admin_header,
    )

    assert detail.status_code == 200
    payload = detail.json()
    assert payload["batch_id"] == batch["id"]
    assert payload["table"]["table_name"] == "X_LANE"
    assert payload["rows"] == [
        {
            "row_index": 1,
            "status": "PENDING",
            "payload": {
                "X_LANE_GID": "OTM1.XL_DETAIL_001",
                "X_LANE_XID": "XL_DETAIL_001",
            },
        }
    ]
    assert payload["issues"] == []
    assert missing.status_code == 404


def test_rate_batches_dba_context_can_see_all_domains_in_active_environment(client, admin_header):
    project_id, environment_id = create_project_environment_context(
        client,
        admin_header,
        domain_name="OTM1",
        can_view_all_domains=True,
    )
    otm1 = create_scoped_rate_batch(
        client,
        admin_header,
        name="OTM1 rates",
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM1",
    )
    otm2 = create_scoped_rate_batch(
        client,
        admin_header,
        name="OTM2 rates",
        project_id=project_id,
        environment_id=environment_id,
        domain_name="OTM2",
    )
    create_scoped_rate_batch(
        client,
        admin_header,
        name="Other env rates",
        project_id=project_id,
        environment_id="env_dev",
        domain_name="OTM3",
    )

    listed = client.get("/api/v1/modules/rates/batches", headers=admin_header)

    assert listed.status_code == 200
    assert {item["id"] for item in listed.json()["items"]} == {otm1["id"], otm2["id"]}


def test_rate_batches_non_admin_without_active_context_cannot_access_or_create(
    client,
    admin_header,
    auth_header,
):
    created = create_scoped_rate_batch(
        client,
        admin_header,
        name="Hidden without context",
        project_id="project_rates",
        environment_id="env_uat",
        domain_name="OTM1",
    )

    listed = client.get("/api/v1/modules/rates/batches", headers=auth_header)
    detail = client.get(f"/api/v1/modules/rates/batches/{created['id']}", headers=auth_header)
    create = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": "RATE_GEO_ONLY",
            "name": "Unscoped non admin batch",
            "domain_name": "OTM1",
            "project_id": "project_rates",
            "environment_id": "env_uat",
        },
        headers=auth_header,
    )

    assert listed.status_code == 200
    assert listed.json()["items"] == []
    assert detail.status_code == 404
    assert create.status_code == 403
    assert create.json()["code"] == "ACTIVE_CONTEXT_REQUIRED"


def test_create_rate_batch_for_non_admin_must_match_active_context_scope(
    client,
    admin_header,
    auth_header,
    db_session,
):
    project_id, environment_id = create_project_environment_context(
        client,
        admin_header,
        domain_name="OTM1",
    )
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Rates Scoped Author")
    capability = Capability(name="rates.batch.manage")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    db_session.add(
        UserProjectRole(
            user_id=user_id,
            project_id=project_id,
            environment_id=environment_id,
            domain_name="OTM1",
            role_id=role.id,
        )
    )
    db_session.commit()
    active_context = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project_id,
            "environment_id": environment_id,
            "domain_name": "otm1",
        },
        headers=auth_header,
    )
    assert active_context.status_code == 200

    visible = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": "RATE_GEO_ONLY",
            "name": "Visible scoped author batch",
            "domain_name": "OTM1",
            "project_id": project_id,
            "environment_id": environment_id,
        },
        headers=auth_header,
    )
    hidden_domain = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": "RATE_GEO_ONLY",
            "name": "Hidden cross-domain author batch",
            "domain_name": "OTM2",
            "project_id": project_id,
            "environment_id": environment_id,
        },
        headers=auth_header,
    )
    hidden_environment = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": "RATE_GEO_ONLY",
            "name": "Hidden cross-environment author batch",
            "domain_name": "OTM1",
            "project_id": project_id,
            "environment_id": "env_dev",
        },
        headers=auth_header,
    )
    other_project_id, other_environment_id = create_project_environment_context(
        client,
        admin_header,
        domain_name="OTM1",
        name_suffix=" Other",
        set_context=False,
    )
    hidden_project = client.post(
        "/api/v1/modules/rates/batches",
        json={
            "scenario_code": "RATE_GEO_ONLY",
            "name": "Hidden cross-project author batch",
            "domain_name": "OTM1",
            "project_id": other_project_id,
            "environment_id": other_environment_id,
        },
        headers=auth_header,
    )

    assert visible.status_code == 200
    assert visible.json()["project_id"] == project_id
    assert visible.json()["environment_id"] == environment_id
    assert visible.json()["domain_name"] == "OTM1"
    assert hidden_domain.status_code == 403
    assert hidden_domain.json()["code"] == "RATES_SCOPE_FORBIDDEN"
    assert hidden_environment.status_code == 403
    assert hidden_environment.json()["code"] == "RATES_SCOPE_FORBIDDEN"
    assert hidden_project.status_code == 403
    assert hidden_project.json()["code"] == "RATES_SCOPE_FORBIDDEN"
