from pathlib import Path

import pytest

from otm_workbench.assistant.services import (
    AssistantSourceInput,
    AssistantSourceIndexError,
    create_assistant_source,
    index_markdown_directory,
    rebuild_assistant_fts_index,
    search_assistant_sources,
)
from otm_workbench.models import AssistantChunk, AssistantIndexRun, AssistantSource, Role, SessionToken, UserProjectRole
from tests.test_assets_library_assets import draft_asset_payload


def dictionary_root() -> Path:
    from otm_workbench.config import get_settings

    return Path(get_settings().otm_data_dictionary_root)


def test_assistant_models_are_created(db_session):
    source = AssistantSource(
        title="Rates quick help",
        source_type="WORKBENCH_HELP",
        source_uri="workbench://rates/help",
        module_id="rates",
        domain_name="OTM1",
        visibility="PRIVATE",
        created_by="synthetic-user",
    )
    db_session.add(source)
    db_session.flush()
    chunk = AssistantChunk(
        source_id=source.id,
        chunk_index=0,
        heading="Rates",
        body_text="Use rate offering and rate record together.",
        token_estimate=8,
    )
    run = AssistantIndexRun(status="PENDING")
    db_session.add_all([chunk, run])
    db_session.commit()

    assert db_session.query(AssistantSource).count() == 1
    assert db_session.query(AssistantChunk).count() == 1
    assert db_session.query(AssistantIndexRun).count() == 1


def test_assistant_service_chunks_and_searches_text(db_session):
    source = create_assistant_source(
        db_session,
        AssistantSourceInput(
            title="Rate record help",
            source_type="WORKBENCH_HELP",
            source_uri="workbench://rates/rate-record",
            body_text="Rate records need rate geo and rate offering context.",
            module_id="rates",
            domain_name="OTM1",
            visibility="PRIVATE",
            created_by="synthetic-user",
        ),
    )
    run = rebuild_assistant_fts_index(db_session)
    results = search_assistant_sources(
        db_session,
        query_text="rate geo",
        allowed_domains=["PUBLIC", "OTM1"],
        limit=5,
    )

    assert source.title == "Rate record help"
    assert run.status == "COMPLETED"
    assert run.chunk_count == 1
    assert [item["source_title"] for item in results] == ["Rate record help"]
    snippet = results[0]["snippet"].lower()
    assert "rate" in snippet
    assert "geo" in snippet


def test_assistant_search_filters_private_domain_chunks(db_session):
    create_assistant_source(
        db_session,
        AssistantSourceInput(
            title="OTM1 private help",
            source_type="WORKBENCH_HELP",
            source_uri="workbench://one",
            body_text="Shipment reference guide for domain one.",
            domain_name="OTM1",
            visibility="PRIVATE",
        ),
    )
    create_assistant_source(
        db_session,
        AssistantSourceInput(
            title="OTM2 private help",
            source_type="WORKBENCH_HELP",
            source_uri="workbench://two",
            body_text="Shipment reference guide for domain two.",
            domain_name="OTM2",
            visibility="PRIVATE",
        ),
    )
    rebuild_assistant_fts_index(db_session)

    results = search_assistant_sources(
        db_session,
        query_text="shipment reference",
        allowed_domains=["PUBLIC", "OTM1"],
        limit=10,
    )

    assert [item["source_title"] for item in results] == ["OTM1 private help"]
    assert "OTM2" not in str(results)


def test_assistant_health_requires_auth(client):
    response = client.get("/api/v1/assistant/health")

    assert response.status_code == 401


def test_assistant_source_create_rebuild_and_search_api(client, admin_header):
    source = client.post(
        "/api/v1/assistant/sources",
        headers=admin_header,
        json={
            "title": "Workbench rates guide",
            "source_type": "WORKBENCH_HELP",
            "source_uri": "workbench://rates/guide",
            "body_text": "Rate geo cost needs a rate record context.",
            "module_id": "rates",
            "domain_name": "OTM1",
            "visibility": "PRIVATE",
        },
    )
    rebuild = client.post("/api/v1/assistant/index/rebuild", headers=admin_header)
    search = client.get("/api/v1/assistant/search?query=rate+geo&limit=5", headers=admin_header)

    assert source.status_code == 201
    assert source.json()["title"] == "Workbench rates guide"
    assert rebuild.status_code == 200
    assert rebuild.json()["status"] == "COMPLETED"
    assert search.status_code == 200
    assert search.json()["total"] == 1
    assert search.json()["items"][0]["source_title"] == "Workbench rates guide"


def test_assistant_search_uses_active_context_domains(client, admin_header, auth_header):
    context = client.post(
        "/api/v1/platform/active-context",
        headers=auth_header,
        json={"domain_name": "otm1"},
    )
    source = client.post(
        "/api/v1/assistant/sources",
        headers=admin_header,
        json={
            "title": "OTM2 private note",
            "source_type": "WORKBENCH_HELP",
            "body_text": "Private shipment lookup instructions.",
            "domain_name": "OTM2",
            "visibility": "PRIVATE",
        },
    )
    rebuild = client.post("/api/v1/assistant/index/rebuild", headers=admin_header)
    search = client.get("/api/v1/assistant/search?query=shipment", headers=auth_header)

    assert context.status_code == 200
    assert source.status_code == 201
    assert rebuild.status_code == 200
    assert search.status_code == 200
    assert search.json()["items"] == []


def test_assistant_indexes_allowlisted_markdown_directory(db_session, tmp_path):
    docs_root = tmp_path / "approved-docs"
    docs_root.mkdir()
    (docs_root / "rates-guide.md").write_text(
        "# Rates Guide\n\nRate offering markdown help for consultants.",
        encoding="utf-8",
    )

    result = index_markdown_directory(
        db_session,
        root=docs_root,
        allowed_roots=[docs_root],
        module_id="rates",
        visibility="PUBLIC",
        created_by="synthetic-user",
    )
    rebuild_assistant_fts_index(db_session)
    results = search_assistant_sources(
        db_session,
        query_text="markdown consultants",
        allowed_domains=["PUBLIC"],
        limit=5,
    )

    source = db_session.query(AssistantSource).filter(AssistantSource.title == "Rates Guide").one()
    assert result.source_count == 1
    assert result.chunk_count == 1
    assert source.source_type == "WORKBENCH_DOC"
    assert source.source_uri == "workbench-doc://rates-guide.md"
    assert str(tmp_path) not in source.source_uri
    assert [item["source_title"] for item in results] == ["Rates Guide"]


def test_assistant_markdown_index_blocks_non_allowlisted_root(db_session, tmp_path):
    docs_root = tmp_path / "approved-docs"
    private_root = tmp_path / "private-docs"
    docs_root.mkdir()
    private_root.mkdir()
    (private_root / "private.md").write_text("# Private\n\nHidden source.", encoding="utf-8")

    with pytest.raises(AssistantSourceIndexError, match="not in the approved source allowlist"):
        index_markdown_directory(db_session, root=private_root, allowed_roots=[docs_root])


def test_assistant_markdown_index_blocks_otm_resources(db_session, tmp_path):
    blocked_root = tmp_path / "OTM_RESOURCES"
    blocked_root.mkdir()
    (blocked_root / "client-note.md").write_text("# Client\n\nDo not index.", encoding="utf-8")

    with pytest.raises(AssistantSourceIndexError, match="OTM_RESOURCES"):
        index_markdown_directory(db_session, root=blocked_root, allowed_roots=[blocked_root])


def test_assistant_workbench_docs_index_api_indexes_approved_docs(client, admin_header):
    response = client.post(
        "/api/v1/assistant/index/workbench-docs",
        headers=admin_header,
        json={"root_key": "assistant_planning"},
    )
    search = client.get("/api/v1/assistant/search?query=source+index&limit=5", headers=admin_header)

    assert response.status_code == 200
    assert response.json()["root_key"] == "assistant_planning"
    assert response.json()["source_count"] >= 1
    assert search.status_code == 200
    assert search.json()["total"] >= 1


def test_assistant_asset_index_api_indexes_current_text_version(client, admin_header):
    asset = client.post(
        "/api/v1/modules/assets/assets",
        headers=admin_header,
        json=draft_asset_payload(
            name="Synthetic Carrier Template",
            description="Reusable carrier template for assistant search.",
            module_id="assets",
            domain_name="otm1",
        ),
    ).json()
    version = client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/versions",
        headers=admin_header,
        files={"file": ("carrier-template.md", b"# Carrier Template\n\nLane calibration checklist.", "text/markdown")},
    ).json()

    response = client.post(f"/api/v1/assistant/index/assets/{asset['id']}", headers=admin_header)
    search = client.get("/api/v1/assistant/search?query=calibration+checklist&limit=5", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["asset_id"] == asset["id"]
    assert payload["asset_version_id"] == version["id"]
    assert payload["source_type"] == "ASSET"
    assert payload["source_uri"] == f"asset://{asset['id']}/versions/{version['id']}"
    assert version["storage_path"] not in str(payload)
    assert search.status_code == 200
    assert [item["source_title"] for item in search.json()["items"]] == ["Synthetic Carrier Template"]


def test_assistant_asset_index_api_uses_asset_scope(client, admin_header, auth_header):
    asset = client.post(
        "/api/v1/modules/assets/assets",
        headers=admin_header,
        json=draft_asset_payload(name="Scoped Private Asset", domain_name="otm2"),
    ).json()
    client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/versions",
        headers=admin_header,
        files={"file": ("private-note.txt", b"private scoped assistant note", "text/plain")},
    )

    response = client.post(f"/api/v1/assistant/index/assets/{asset['id']}", headers=auth_header)

    assert response.status_code == 404
    assert response.json()["code"] == "ASSET_NOT_FOUND"


def test_assistant_search_filters_private_asset_by_project_and_environment(client, admin_header, auth_header, db_session):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        headers=admin_header,
        json={"name": "Assistant Asset Scope Workspace"},
    ).json()
    project_one = client.post(
        "/api/v1/platform/projects",
        headers=admin_header,
        json={"workspace_id": workspace["id"], "name": "Assistant Project One"},
    ).json()
    project_two = client.post(
        "/api/v1/platform/projects",
        headers=admin_header,
        json={"workspace_id": workspace["id"], "name": "Assistant Project Two"},
    ).json()
    environment_one = client.post(
        "/api/v1/platform/environments",
        headers=admin_header,
        json={"project_id": project_one["id"], "name": "UAT", "environment_type": "UAT"},
    ).json()
    environment_two = client.post(
        "/api/v1/platform/environments",
        headers=admin_header,
        json={"project_id": project_two["id"], "name": "UAT", "environment_type": "UAT"},
    ).json()
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Assistant Project One Viewer")
    db_session.add(role)
    db_session.flush()
    db_session.add(UserProjectRole(user_id=user_id, project_id=project_one["id"], role_id=role.id))
    db_session.commit()
    asset = client.post(
        "/api/v1/modules/assets/assets",
        headers=admin_header,
        json=draft_asset_payload(
            name="Project Two Private Template",
            project_id=project_two["id"],
            environment_id=environment_two["id"],
            domain_name="otm1",
        ),
    ).json()
    client.post(
        f"/api/v1/modules/assets/assets/{asset['id']}/versions",
        headers=admin_header,
        files={"file": ("project-two.txt", b"exclusive project token", "text/plain")},
    )
    indexed = client.post(f"/api/v1/assistant/index/assets/{asset['id']}", headers=admin_header)
    context = client.post(
        "/api/v1/platform/active-context",
        headers=auth_header,
        json={"project_id": project_one["id"], "environment_id": environment_one["id"], "domain_name": "otm1"},
    )
    search = client.get("/api/v1/assistant/search?query=exclusive+project+token", headers=auth_header)

    assert indexed.status_code == 200
    assert context.status_code == 200
    assert search.status_code == 200
    assert search.json()["items"] == []


def test_sql_helper_rejects_mutation_sql():
    from otm_workbench.assistant.sql_helper import reject_unsafe_sql

    payload = reject_unsafe_sql("delete from shipment where shipment_gid = :gid")

    assert payload is not None
    assert payload["answer_type"] == "blocked"
    assert payload["confidence"] == "high"
    assert "Only SELECT" in payload["summary"]


def test_sql_helper_drafts_single_table_select_from_dictionary():
    from otm_workbench.assistant.sql_helper import draft_single_table_select

    payload = draft_single_table_select(
        dictionary_root(),
        table_name="RATE_GEO_COST",
        columns=["RATE_GEO_COST_GROUP_GID"],
        filter_column="RATE_GEO_COST_GROUP_GID",
        purpose="Find rate geo cost by group.",
    )

    assert payload["answer_type"] == "sql_draft"
    assert payload["confidence"] == "high"
    assert "from RATE_GEO_COST rgc" in payload["block"]["sql"]
    assert ":rate_geo_cost_group_gid" in payload["block"]["sql"]
    assert payload["block"]["tables"] == ["RATE_GEO_COST"]
    assert payload["block"]["columns"] == ["RATE_GEO_COST.RATE_GEO_COST_GROUP_GID"]
    assert payload["sources"][0]["source_type"] == "data_dictionary"


def test_sql_helper_blocks_unknown_column():
    from otm_workbench.assistant.sql_helper import draft_single_table_select

    payload = draft_single_table_select(
        dictionary_root(),
        table_name="RATE_GEO_COST",
        columns=["MISSING_COLUMN"],
        filter_column="RATE_GEO_COST_GROUP_GID",
        purpose="Find rate geo cost.",
    )

    assert payload["answer_type"] == "blocked"
    assert payload["summary"] == "One or more requested columns are not in the local Data Dictionary."
    assert payload["warnings"] == ["RATE_GEO_COST.MISSING_COLUMN was not found."]


def test_sql_helper_explains_select_and_flags_unknown_references():
    from otm_workbench.assistant.sql_helper import explain_select_sql

    payload = explain_select_sql(
        dictionary_root(),
        "select rgc.rate_geo_cost_group_gid, rgc.missing_column from rate_geo_cost rgc where rgc.rate_geo_cost_group_gid = :gid",
    )

    assert payload["answer_type"] == "sql_draft"
    assert payload["block"]["tables"] == ["RATE_GEO_COST"]
    assert "RATE_GEO_COST.RATE_GEO_COST_GROUP_GID" in payload["block"]["columns"]
    assert "RATE_GEO_COST.MISSING_COLUMN was not found." in payload["block"]["warnings"]
    assert payload["confidence"] == "medium"


def test_assistant_sql_draft_api_requires_auth(client):
    response = client.post(
        "/api/v1/assistant/sql/draft",
        json={
            "table_name": "RATE_GEO_COST",
            "columns": ["RATE_GEO_COST_GROUP_GID"],
            "filter_column": "RATE_GEO_COST_GROUP_GID",
            "purpose": "Find rate geo cost by group.",
        },
    )

    assert response.status_code == 401


def test_assistant_sql_draft_api_returns_select_only_draft(client, admin_header):
    response = client.post(
        "/api/v1/assistant/sql/draft",
        headers=admin_header,
        json={
            "table_name": "RATE_GEO_COST",
            "columns": ["RATE_GEO_COST_GROUP_GID"],
            "filter_column": "RATE_GEO_COST_GROUP_GID",
            "purpose": "Find rate geo cost by group.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer_type"] == "sql_draft"
    assert payload["block"]["tables"] == ["RATE_GEO_COST"]
    assert "delete" not in payload["block"]["sql"].lower()


def test_assistant_sql_explain_api_rejects_mutation(client, admin_header):
    response = client.post(
        "/api/v1/assistant/sql/explain",
        headers=admin_header,
        json={"sql_text": "update shipment set domain_name = 'PUBLIC'"},
    )

    assert response.status_code == 200
    assert response.json()["answer_type"] == "blocked"


def test_saved_query_models_and_draft_creation(db_session):
    from otm_workbench.assistant.saved_queries import create_saved_query
    from otm_workbench.models import AssistantSavedQuery, AssistantSavedQueryColumn, AssistantSavedQueryTable

    query = create_saved_query(
        db_session,
        name="Rate geo cost lookup",
        purpose="Find rate geo cost by group.",
        sql_text="select rgc.rate_geo_cost_group_gid from rate_geo_cost rgc where rgc.rate_geo_cost_group_gid = :rate_geo_cost_group_gid",
        module_id="rates",
        visibility="PUBLIC",
        created_by="synthetic-user",
    )

    assert query.status == "DRAFT"
    assert db_session.query(AssistantSavedQuery).count() == 1
    assert db_session.query(AssistantSavedQueryTable).count() == 1
    assert db_session.query(AssistantSavedQueryColumn).count() == 1


def test_saved_query_approval_validates_dictionary_references(db_session):
    from otm_workbench.assistant.saved_queries import approve_saved_query, create_saved_query

    query = create_saved_query(
        db_session,
        name="Rate geo cost lookup",
        purpose="Find rate geo cost by group.",
        sql_text="select rgc.rate_geo_cost_group_gid from rate_geo_cost rgc where rgc.rate_geo_cost_group_gid = :rate_geo_cost_group_gid",
        visibility="PUBLIC",
    )

    approved = approve_saved_query(db_session, query.id, dictionary_root=dictionary_root(), reviewed_by="reviewer")

    assert approved.status == "APPROVED"
    assert approved.reviewed_by == "reviewer"


def test_saved_query_approval_blocks_unknown_column(db_session):
    from otm_workbench.assistant.saved_queries import approve_saved_query, create_saved_query

    query = create_saved_query(
        db_session,
        name="Broken query",
        purpose="Broken query.",
        sql_text="select rgc.missing_column from rate_geo_cost rgc",
        visibility="PUBLIC",
    )

    approved = approve_saved_query(db_session, query.id, dictionary_root=dictionary_root(), reviewed_by="reviewer")

    assert approved.status == "DRAFT"
    assert "RATE_GEO_COST.MISSING_COLUMN was not found." in approved.warnings_json


def test_saved_query_approval_blocks_literal_values(db_session):
    from otm_workbench.assistant.saved_queries import approve_saved_query, create_saved_query

    query = create_saved_query(
        db_session,
        name="Unsafe literal",
        purpose="Unsafe literal.",
        sql_text="select s.shipment_gid from shipment s where s.shipment_gid = 'SYNTHETIC.REAL_LOOKING_VALUE'",
        visibility="PUBLIC",
    )

    approved = approve_saved_query(db_session, query.id, dictionary_root=dictionary_root(), reviewed_by="reviewer")

    assert approved.status == "DRAFT"
    assert "Use bind parameters instead of quoted literals." in approved.warnings_json


def test_saved_query_search_hides_retired_by_default(db_session):
    from otm_workbench.assistant.saved_queries import create_saved_query, search_saved_queries

    approved = create_saved_query(
        db_session,
        name="Approved rate lookup",
        purpose="Approved.",
        sql_text="select rgc.rate_geo_cost_group_gid from rate_geo_cost rgc",
        visibility="PUBLIC",
    )
    retired = create_saved_query(
        db_session,
        name="Retired rate lookup",
        purpose="Retired.",
        sql_text="select rgc.rate_geo_cost_group_gid from rate_geo_cost rgc",
        visibility="PUBLIC",
    )
    approved.status = "APPROVED"
    retired.status = "RETIRED"
    db_session.commit()

    results = search_saved_queries(db_session, query_text="rate lookup", allowed_domains=["PUBLIC"])

    assert [item["name"] for item in results] == ["Approved rate lookup"]


def test_assistant_saved_query_create_and_search_api(client, admin_header):
    created = client.post(
        "/api/v1/assistant/sql/saved-queries",
        headers=admin_header,
        json={
            "name": "Rate geo cost lookup",
            "purpose": "Find rate geo cost by group.",
            "sql_text": "select rgc.rate_geo_cost_group_gid from rate_geo_cost rgc where rgc.rate_geo_cost_group_gid = :rate_geo_cost_group_gid",
            "module_id": "rates",
            "visibility": "PUBLIC",
        },
    )
    approved = client.post(f"/api/v1/assistant/sql/saved-queries/{created.json().get('id', 'missing')}/approve", headers=admin_header)
    search = client.get("/api/v1/assistant/sql/saved-queries?query=rate+geo", headers=admin_header)

    assert created.status_code == 201
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    assert search.status_code == 200
    assert search.json()["total"] == 1


def test_join_pattern_model_and_draft_creation(db_session):
    from otm_workbench.assistant.join_patterns import create_join_pattern
    from otm_workbench.models import AssistantJoinPattern

    pattern = create_join_pattern(
        db_session,
        name="Shipment to shipment stop",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
        join_type="INNER",
        business_meaning="Shipment header to stops.",
        module_id="order_release_generator",
        created_by="synthetic-user",
    )

    assert pattern.status == "DRAFT"
    assert pattern.confidence == "LOW"
    assert db_session.query(AssistantJoinPattern).count() == 1


def test_join_pattern_approval_validates_dictionary_references(db_session):
    from otm_workbench.assistant.join_patterns import approve_join_pattern, create_join_pattern

    pattern = create_join_pattern(
        db_session,
        name="Shipment to shipment stop",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
        business_meaning="Shipment header to stops.",
    )

    approved = approve_join_pattern(db_session, pattern.id, dictionary_root=dictionary_root(), reviewed_by="reviewer")

    assert approved.status == "APPROVED"
    assert approved.confidence == "HIGH"
    assert approved.reviewed_by == "reviewer"


def test_join_pattern_approval_blocks_unknown_column(db_session):
    from otm_workbench.assistant.join_patterns import approve_join_pattern, create_join_pattern

    pattern = create_join_pattern(
        db_session,
        name="Broken join",
        left_table="SHIPMENT",
        left_column="MISSING_COLUMN",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
    )

    approved = approve_join_pattern(db_session, pattern.id, dictionary_root=dictionary_root(), reviewed_by="reviewer")

    assert approved.status == "DRAFT"
    assert "SHIPMENT.MISSING_COLUMN was not found." in approved.warnings_json


def test_join_pattern_saved_query_source_requires_approved_query(db_session):
    from otm_workbench.assistant.join_patterns import approve_join_pattern, create_join_pattern
    from otm_workbench.assistant.saved_queries import create_saved_query

    saved_query = create_saved_query(
        db_session,
        name="Draft shipment stop query",
        purpose="Draft source.",
        sql_text="select s.shipment_gid from shipment s",
        visibility="PUBLIC",
    )
    pattern = create_join_pattern(
        db_session,
        name="Shipment to stop from draft",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
        source_type="SAVED_QUERY",
        source_id=saved_query.id,
    )

    approved = approve_join_pattern(db_session, pattern.id, dictionary_root=dictionary_root(), reviewed_by="reviewer")

    assert approved.status == "DRAFT"
    assert "Saved query source must be approved before it can validate a join pattern." in approved.warnings_json


def test_join_pattern_search_returns_only_approved_by_default(db_session):
    from otm_workbench.assistant.join_patterns import create_join_pattern, search_join_patterns

    approved = create_join_pattern(
        db_session,
        name="Approved shipment stop join",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
    )
    create_join_pattern(
        db_session,
        name="Draft shipment stop join",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
    )
    approved.status = "APPROVED"
    approved.confidence = "HIGH"
    db_session.commit()

    results = search_join_patterns(db_session, query_text="shipment stop")

    assert [item["name"] for item in results] == ["Approved shipment stop join"]


def test_assistant_join_pattern_create_approve_and_search_api(client, admin_header):
    created = client.post(
        "/api/v1/assistant/sql/join-patterns",
        headers=admin_header,
        json={
            "name": "Shipment to shipment stop",
            "left_table": "SHIPMENT",
            "left_column": "SHIPMENT_GID",
            "right_table": "SHIPMENT_STOP",
            "right_column": "SHIPMENT_GID",
            "join_type": "INNER",
            "business_meaning": "Shipment header to stops.",
            "module_id": "order_release_generator",
        },
    )
    approved = client.post(f"/api/v1/assistant/sql/join-patterns/{created.json().get('id', 'missing')}/approve", headers=admin_header)
    search = client.get("/api/v1/assistant/sql/join-patterns?query=shipment+stop", headers=admin_header)

    assert created.status_code == 201
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    assert search.status_code == 200
    assert search.json()["total"] == 1


def test_joined_sql_draft_uses_approved_join_pattern(db_session):
    from otm_workbench.assistant.join_patterns import approve_join_pattern, create_join_pattern
    from otm_workbench.assistant.sql_helper import draft_joined_select

    pattern = create_join_pattern(
        db_session,
        name="Shipment to shipment stop",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
        join_type="INNER",
        business_meaning="Shipment header to stops.",
    )
    approve_join_pattern(db_session, pattern.id, dictionary_root=dictionary_root(), reviewed_by="reviewer")

    payload = draft_joined_select(
        db_session,
        dictionary_root(),
        join_pattern_id=pattern.id,
        left_columns=["SHIPMENT_GID"],
        right_columns=["SHIPMENT_GID"],
        filter_table="SHIPMENT",
        filter_column="SHIPMENT_GID",
        purpose="Find shipment stops by shipment.",
    )

    assert payload["answer_type"] == "sql_draft"
    assert payload["confidence"] == "high"
    assert "from SHIPMENT s" in payload["block"]["sql"]
    assert "join SHIPMENT_STOP ss on s.SHIPMENT_GID = ss.SHIPMENT_GID" in payload["block"]["sql"]
    assert "where s.SHIPMENT_GID = :shipment_gid" in payload["block"]["sql"]
    assert payload["block"]["tables"] == ["SHIPMENT", "SHIPMENT_STOP"]
    assert payload["block"]["join_patterns"] == [pattern.id]
    assert payload["block"]["parameters"] == [
        {"name": "shipment_gid", "description": "Filter for SHIPMENT.SHIPMENT_GID"}
    ]


def test_joined_sql_draft_blocks_unapproved_join_pattern(db_session):
    from otm_workbench.assistant.join_patterns import create_join_pattern
    from otm_workbench.assistant.sql_helper import draft_joined_select

    pattern = create_join_pattern(
        db_session,
        name="Draft shipment stop join",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
    )

    payload = draft_joined_select(
        db_session,
        dictionary_root(),
        join_pattern_id=pattern.id,
        left_columns=["SHIPMENT_GID"],
        right_columns=["SHIPMENT_GID"],
        filter_table="SHIPMENT",
        filter_column="SHIPMENT_GID",
        purpose="Find shipment stops by shipment.",
    )

    assert payload["answer_type"] == "blocked"
    assert payload["warnings"] == ["Join pattern must be approved before joined SQL can be drafted."]


def test_joined_sql_draft_blocks_unknown_requested_column(db_session):
    from otm_workbench.assistant.join_patterns import approve_join_pattern, create_join_pattern
    from otm_workbench.assistant.sql_helper import draft_joined_select

    pattern = create_join_pattern(
        db_session,
        name="Shipment to shipment stop",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
    )
    approve_join_pattern(db_session, pattern.id, dictionary_root=dictionary_root(), reviewed_by="reviewer")

    payload = draft_joined_select(
        db_session,
        dictionary_root(),
        join_pattern_id=pattern.id,
        left_columns=["MISSING_COLUMN"],
        right_columns=["SHIPMENT_GID"],
        filter_table="SHIPMENT",
        filter_column="SHIPMENT_GID",
        purpose="Find shipment stops by shipment.",
    )

    assert payload["answer_type"] == "blocked"
    assert payload["summary"] == "One or more requested columns are not in the local Data Dictionary."
    assert "SHIPMENT.MISSING_COLUMN was not found." in payload["warnings"]


def test_joined_sql_api_creates_select_from_approved_pattern(client, admin_header):
    created = client.post(
        "/api/v1/assistant/sql/join-patterns",
        headers=admin_header,
        json={
            "name": "Shipment to shipment stop",
            "left_table": "SHIPMENT",
            "left_column": "SHIPMENT_GID",
            "right_table": "SHIPMENT_STOP",
            "right_column": "SHIPMENT_GID",
            "join_type": "INNER",
            "business_meaning": "Shipment header to stops.",
        },
    )
    pattern_id = created.json().get("id", "missing")
    approved = client.post(f"/api/v1/assistant/sql/join-patterns/{pattern_id}/approve", headers=admin_header)

    response = client.post(
        "/api/v1/assistant/sql/draft-join",
        headers=admin_header,
        json={
            "join_pattern_id": pattern_id,
            "left_columns": ["SHIPMENT_GID"],
            "right_columns": ["SHIPMENT_GID"],
            "filter_table": "SHIPMENT",
            "filter_column": "SHIPMENT_GID",
            "purpose": "Find shipment stops by shipment.",
        },
    )

    assert created.status_code == 201
    assert approved.status_code == 200
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer_type"] == "sql_draft"
    assert payload["block"]["join_patterns"] == [pattern_id]
    assert "delete" not in payload["block"]["sql"].lower()


def test_oracle_docs_cache_model_and_draft_creation(db_session):
    from otm_workbench.assistant.oracle_docs import create_oracle_doc_cache
    from otm_workbench.models import AssistantOracleDocCache

    record = create_oracle_doc_cache(
        db_session,
        title="Oracle OTM REST API Guide",
        url="https://docs.oracle.com/en/cloud/saas/transportation/25a/otmra/",
        product_area="REST API",
        topic="shipment",
        version_label="25A",
        summary="Synthetic cache entry for shipment REST API documentation.",
        created_by="synthetic-user",
    )

    assert record.status == "DRAFT"
    assert record.source_domain == "docs.oracle.com"
    assert db_session.query(AssistantOracleDocCache).count() == 1


def test_oracle_docs_cache_rejects_non_official_url(db_session):
    from otm_workbench.assistant.oracle_docs import create_oracle_doc_cache

    with pytest.raises(ValueError, match="official Oracle documentation"):
        create_oracle_doc_cache(
            db_session,
            title="Unofficial copy",
            url="https://example.com/oracle/otm",
            product_area="REST API",
            topic="shipment",
            version_label="25A",
            summary="Rejected synthetic entry.",
        )


def test_oracle_docs_cache_approval_and_search(db_session):
    from otm_workbench.assistant.oracle_docs import (
        approve_oracle_doc_cache,
        create_oracle_doc_cache,
        search_oracle_doc_cache,
    )

    approved = create_oracle_doc_cache(
        db_session,
        title="Oracle OTM REST API Guide",
        url="https://docs.oracle.com/en/cloud/saas/transportation/25a/otmra/",
        product_area="REST API",
        topic="shipment",
        version_label="25A",
        summary="Shipment endpoint reference.",
    )
    create_oracle_doc_cache(
        db_session,
        title="Draft Oracle OTM SOAP Guide",
        url="https://docs.oracle.com/en/cloud/saas/transportation/25a/otmsoap/",
        product_area="SOAP",
        topic="shipment",
        version_label="25A",
        summary="Draft SOAP reference.",
    )

    reviewed = approve_oracle_doc_cache(db_session, approved.id, reviewed_by="reviewer")
    results = search_oracle_doc_cache(db_session, query_text="shipment", product_area="REST API")

    assert reviewed.status == "APPROVED"
    assert reviewed.reviewed_by == "reviewer"
    assert [item["title"] for item in results] == ["Oracle OTM REST API Guide"]
    assert results[0]["url"].startswith("https://docs.oracle.com/")


def test_oracle_docs_live_lookup_is_blocked_until_explicit_connector_exists():
    from otm_workbench.assistant.oracle_docs import blocked_live_lookup

    payload = blocked_live_lookup("post shipment endpoint")

    assert payload["answer_type"] == "blocked"
    assert payload["cost_level"] == "web"
    assert payload["source_mode"] == "none"
    assert "not enabled" in payload["summary"].lower()


def test_oracle_lookup_request_sanitizes_private_terms_and_generates_official_links():
    from otm_workbench.assistant.oracle_docs import prepare_live_lookup_request

    payload = prepare_live_lookup_request(
        "For client ACME in UAT at https://private.example.test with token ABCDEF1234567890, find OTM REST API post shipment endpoint.",
        private_terms=["ACME", "UAT"],
    )

    assert payload["answer_type"] == "lookup_request"
    assert payload["cost_level"] == "web"
    assert payload["network_performed"] is False
    assert "ACME" not in payload["sanitized_query"]
    assert "UAT" not in payload["sanitized_query"]
    assert "private.example" not in payload["sanitized_query"]
    assert "ABCDEF1234567890" not in payload["sanitized_query"]
    assert "REST API" in payload["sanitized_query"]
    assert "shipment endpoint" in payload["sanitized_query"]
    assert payload["actions"][0]["url"].startswith("https://docs.oracle.com/search/")
    assert "ACME" not in payload["actions"][0]["url"]


def test_oracle_lookup_request_api_prepares_search_without_network(client, admin_header):
    response = client.post(
        "/api/v1/assistant/oracle-docs/live-lookup",
        headers=admin_header,
        json={
            "query": "For client ACME in PROD, find OTM REST API post shipment endpoint.",
            "private_terms": ["ACME", "PROD"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer_type"] == "lookup_request"
    assert payload["network_performed"] is False
    assert "ACME" not in payload["sanitized_query"]
    assert "PROD" not in payload["sanitized_query"]
    assert payload["actions"][0]["url"].startswith("https://docs.oracle.com/search/")


def test_oracle_docs_cache_create_approve_search_api(client, admin_header):
    created = client.post(
        "/api/v1/assistant/oracle-docs/cache",
        headers=admin_header,
        json={
            "title": "Oracle OTM REST API Guide",
            "url": "https://docs.oracle.com/en/cloud/saas/transportation/25a/otmra/",
            "product_area": "REST API",
            "topic": "shipment",
            "version_label": "25A",
            "summary": "Shipment endpoint reference.",
        },
    )
    record_id = created.json().get("id", "missing")
    approved = client.post(f"/api/v1/assistant/oracle-docs/cache/{record_id}/approve", headers=admin_header)
    search = client.get("/api/v1/assistant/oracle-docs/search?query=shipment&product_area=REST+API", headers=admin_header)

    assert created.status_code == 201
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    assert search.status_code == 200
    assert search.json()["total"] == 1
    assert search.json()["items"][0]["url"].startswith("https://docs.oracle.com/")


def test_oracle_docs_live_lookup_api_is_blocked(client, admin_header):
    response = client.post(
        "/api/v1/assistant/oracle-docs/live-lookup",
        headers=admin_header,
        json={"query": "post shipment endpoint"},
    )

    assert response.status_code == 200
    assert response.json()["answer_type"] == "lookup_request"
    assert response.json()["cost_level"] == "web"
    assert response.json()["network_performed"] is False
