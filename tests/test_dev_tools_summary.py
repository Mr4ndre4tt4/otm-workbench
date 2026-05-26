from otm_workbench.models import Job, SchemaFile, SchemaPack, SchemaRoot


def test_dev_tools_summary_requires_authentication(client):
    response = client.get("/api/v1/platform/dev-tools/summary")

    assert response.status_code == 401


def test_dev_tools_summary_requires_enabled_feature_flag(client, admin_header):
    response = client.get("/api/v1/platform/dev-tools/summary", headers=admin_header)

    assert response.status_code == 403
    assert response.json()["code"] == "DEV_TOOLS_DISABLED"


def test_dev_tools_summary_returns_backend_owned_guarded_contract(client, admin_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Local"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Synthetic Rollout"},
        headers=admin_header,
    ).json()
    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Default"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
        },
        headers=admin_header,
    )
    client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=admin_header,
    )
    client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "dev_tools",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "OTM1",
            "input": {"secret": "do-not-leak", "safe": "synthetic"},
            "execute_now": True,
        },
        headers=admin_header,
    )

    response = client.get("/api/v1/platform/dev-tools/summary", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["module_id"] == "dev_tools"
    assert payload["title"] == "Technical Diagnostics Hub"
    assert payload["status"] == "guarded"
    assert payload["active_context"]["project_id"] == project["id"]
    assert payload["guards"] == [
        {
            "key": "feature_flag",
            "label": "Feature flag",
            "status": "READY",
            "message": "dev_tools is enabled.",
        },
        {
            "key": "capability",
            "label": "Capability",
            "status": "READY",
            "message": "Admin access authorizes technical diagnostics.",
        },
        {
            "key": "safe_output",
            "label": "Safe output",
            "status": "READY",
            "message": "Summary returns metadata only; raw inputs and results stay hidden.",
        },
    ]
    assert [tool["key"] for tool in payload["tools"]] == [
        "data_dictionary",
        "fk_catalog",
        "schema_packs",
        "environment_readiness",
        "otm_explorer",
        "oracle_lab",
    ]
    assert payload["tools"][0]["status"] == "AVAILABLE"
    assert payload["tools"][0]["href"] == "/dev-tools/data-dictionary"
    assert payload["tools"][-1]["status"] == "DISABLED"
    assert "governance" in payload["tools"][-1]["disabled_reason"].lower()
    assert payload["counts"] == {"available_tools": 4, "disabled_tools": 2, "recent_runs": 1}
    assert payload["recent_runs"][0]["source_module"] == "dev_tools"
    assert payload["recent_runs"][0]["input_present"] is True
    assert payload["recent_runs"][0]["result_present"] is True
    assert "input" not in payload["recent_runs"][0]
    assert "result" not in payload["recent_runs"][0]
    assert "do-not-leak" not in str(payload)

    job = db_session.query(Job).filter(Job.source_module == "dev_tools").one()
    assert job.input_json


def test_dev_tools_data_dictionary_requires_enabled_feature_flag(client, admin_header):
    response = client.get("/api/v1/platform/dev-tools/data-dictionary?query=rate_geo", headers=admin_header)

    assert response.status_code == 403
    assert response.json()["code"] == "DEV_TOOLS_DISABLED"


def test_dev_tools_data_dictionary_lists_client_safe_table_metadata(client, admin_header):
    client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=admin_header,
    )

    response = client.get("/api/v1/platform/dev-tools/data-dictionary?query=rate_geo&limit=5", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["module_id"] == "dev_tools"
    assert payload["tool_key"] == "data_dictionary"
    assert payload["title"] == "Data Dictionary Explorer"
    assert payload["query"] == "rate_geo"
    assert payload["source_contract"] == "/api/v1/catalog/tables"
    assert payload["total"] >= len(payload["items"])
    assert "RATE_GEO" in [item["table_name"] for item in payload["items"]]
    assert "RATE_GEO_COST" in [item["table_name"] for item in payload["items"]]
    assert all("file_path" not in item for item in payload["items"])
    assert "file_path" not in str(payload)


def test_dev_tools_data_dictionary_table_detail_returns_columns_without_file_paths(client, admin_header):
    client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=admin_header,
    )

    response = client.get("/api/v1/platform/dev-tools/data-dictionary/tables/RATE_GEO_COST", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["module_id"] == "dev_tools"
    assert payload["tool_key"] == "data_dictionary"
    assert payload["table"]["table_name"] == "RATE_GEO_COST"
    assert payload["table"]["exists"] is True
    assert "RATE_GEO_COST_GROUP_GID" in [item["column_name"] for item in payload["columns"]]
    assert "file_path" not in str(payload)


def test_dev_tools_fk_catalog_requires_enabled_feature_flag(client, admin_header):
    response = client.get("/api/v1/platform/dev-tools/fk-catalog?source_table=RATE_GEO_COST", headers=admin_header)

    assert response.status_code == 403
    assert response.json()["code"] == "DEV_TOOLS_DISABLED"


def test_dev_tools_fk_catalog_lists_client_safe_relationships(client, admin_header):
    client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=admin_header,
    )

    response = client.get("/api/v1/platform/dev-tools/fk-catalog?source_table=RATE_GEO_COST", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["module_id"] == "dev_tools"
    assert payload["tool_key"] == "fk_catalog"
    assert payload["title"] == "FK Catalog Explorer"
    assert payload["source_table"] == "RATE_GEO_COST"
    assert payload["source_contract"] == "/api/v1/catalog/tables/RATE_GEO_COST"
    assert payload["total"] >= len(payload["items"])
    assert "RATE_GEO_COST_GROUP" in [item["parent_table_name"] for item in payload["items"]]
    assert "RATE_GEO_COST_GROUP_GID" in [item["column_name"] for item in payload["items"]]
    assert all("file_path" not in item for item in payload["items"])
    assert "file_path" not in str(payload)


def test_dev_tools_schema_packs_requires_enabled_feature_flag(client, admin_header):
    response = client.get("/api/v1/platform/dev-tools/schema-packs", headers=admin_header)

    assert response.status_code == 403
    assert response.json()["code"] == "DEV_TOOLS_DISABLED"


def test_dev_tools_schema_packs_lists_client_safe_pack_and_root_metadata(client, admin_header, db_session):
    pack = SchemaPack(
        code="OTM26A",
        name="Synthetic OTM 26A",
        otm_version="26A",
        source_type="LOCAL_FOLDER",
        source_path="C:/synthetic/local/schema-pack",
        status="INDEXED",
        namespace_count=2,
        root_count=1,
        operation_count=0,
        content_hash="synthetic-hash",
        created_by="synthetic.user@example.test",
    )
    db_session.add(pack)
    db_session.flush()
    schema_file = SchemaFile(
        schema_pack_id=pack.id,
        file_name="Transmission.xsd",
        relative_path="glog/Transmission.xsd",
        file_type="XSD",
        namespace="http://xmlns.oracle.com/apps/otm/transmission",
    )
    db_session.add(schema_file)
    db_session.flush()
    db_session.add(
        SchemaRoot(
            schema_pack_id=pack.id,
            schema_file_id=schema_file.id,
            root_name="Transmission",
            namespace="http://xmlns.oracle.com/apps/otm/transmission",
            domain_area="INTEGRATION",
            root_type="ENVELOPE",
            envelope_role="TRANSMISSION",
            recommended_modules_json='["integration_mapping", "order_release_generator"]',
            documentation="Synthetic transmission envelope.",
        )
    )
    db_session.add(
        SchemaPack(
            code="OTM26A_OTHER",
            name="Other Synthetic OTM 26A",
            otm_version="26A",
            source_type="LOCAL_FOLDER",
            source_path="C:/synthetic/local/other-schema-pack",
            status="INDEXED",
            content_hash="other-synthetic-hash",
        )
    )
    db_session.commit()
    client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=admin_header,
    )

    response = client.get("/api/v1/platform/dev-tools/schema-packs?otm_version=26A&code=OTM26A", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["module_id"] == "dev_tools"
    assert payload["tool_key"] == "schema_packs"
    assert payload["title"] == "Schema Pack Diagnostics"
    assert payload["otm_version"] == "26A"
    assert payload["source_contract"] == "/api/v1/catalog/schema-packs"
    assert payload["root_contract"] == "/api/v1/catalog/schema-roots"
    assert payload["total"] == 1
    assert payload["items"][0]["code"] == "OTM26A"
    assert payload["items"][0]["root_preview"][0]["root_name"] == "Transmission"
    assert payload["items"][0]["root_preview"][0]["schema_guidance_role"] == "ENVELOPE_ONLY"
    assert "source_path" not in str(payload)
    assert "C:/synthetic/local/schema-pack" not in str(payload)


def test_dev_tools_environment_readiness_requires_enabled_feature_flag(client, admin_header):
    response = client.get("/api/v1/platform/dev-tools/environment-readiness", headers=admin_header)

    assert response.status_code == 403
    assert response.json()["code"] == "DEV_TOOLS_DISABLED"


def test_dev_tools_environment_readiness_returns_active_context_and_environment_checks(client, admin_header):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Local"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Synthetic Rollout"},
        headers=admin_header,
    ).json()
    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Default"},
        headers=admin_header,
    ).json()
    environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
            "can_view_all_domains": False,
        },
        headers=admin_header,
    )
    client.post(
        "/api/v1/platform/feature-flags",
        json={"name": "dev_tools", "enabled": True, "scope": "global"},
        headers=admin_header,
    )

    response = client.get("/api/v1/platform/dev-tools/environment-readiness", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["module_id"] == "dev_tools"
    assert payload["tool_key"] == "environment_readiness"
    assert payload["title"] == "Environment Readiness"
    assert payload["active_context"]["project_id"] == project["id"]
    assert payload["active_environment_id"] == environment["id"]
    assert payload["counts"] == {"environments": 1, "ready_checks": 4, "blocked_checks": 0}
    assert payload["environments"] == [
        {
            "id": environment["id"],
            "name": "DEV",
            "environment_type": "DEV",
            "status": "ACTIVE",
            "is_active": True,
        }
    ]
    assert [item["key"] for item in payload["checks"]] == [
        "active_project",
        "active_profile",
        "active_environment",
        "domain_scope",
    ]
    assert all(item["status"] == "READY" for item in payload["checks"])
    assert "password" not in str(payload).lower()
    assert "connection" not in str(payload).lower()
