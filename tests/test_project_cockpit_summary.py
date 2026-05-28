from otm_workbench.models import Artifact, Capability, Evidence, Role, RoleCapability, SessionToken, UserProjectRole


def create_context(client, admin_header):
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
    active_context = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
        },
        headers=admin_header,
    )
    assert active_context.status_code == 200
    return project, profile, environment


def action_by_key(payload, key):
    return next(action for action in payload["available_actions"] if action["key"] == key)


def accelerator_by_key(payload, key):
    return next(accelerator for accelerator in payload["accelerators"] if accelerator["key"] == key)


def test_project_cockpit_summary_requires_authentication(client):
    response = client.get("/api/v1/platform/project-cockpit/summary")

    assert response.status_code == 401


def test_project_cockpit_summary_returns_empty_shell_contract(client, admin_header):
    response = client.get("/api/v1/platform/project-cockpit/summary", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["module_id"] == "home"
    assert payload["title"] == "Project Cockpit"
    assert payload["status"] == "needs_context"
    assert payload["active_context"]["project_id"] is None
    assert payload["setup_status"] is None
    assert payload["counts"]["recent_jobs"] == 0
    assert payload["counts"]["recent_artifacts"] == 0
    assert payload["counts"]["recent_evidence"] == 0
    assert payload["recent_jobs"] == []
    assert payload["recent_artifacts"] == []
    assert payload["recent_evidence"] == []
    assert payload["module_summary"]["total"] >= 1
    assert any(item["id"] == "home" for item in payload["module_summary"]["items"])
    assert payload["context_selector"] == {
        "mode": "PUBLIC",
        "active_context": payload["active_context"],
        "public_view_available": True,
        "requires_private_context": False,
        "set_context_action_key": "set_active_context",
    }
    assert payload["project_info"] == {
        "title": "Project information",
        "status": "NEEDS_CONTEXT",
        "links": [],
        "documents": [],
        "contacts": [],
        "secure_vault": {
            "status": "NOT_CONFIGURED",
            "metadata_only": True,
            "secret_values_available": False,
        },
    }
    assert payload["user_scope"]["role_mode"] == "DBA"
    assert payload["user_scope"]["can_view_all_domains"] is False
    assert payload["user_scope"]["allowed_domains"] == ["PUBLIC"]
    assert payload["route_recovery"] == {
        "default_path": "/home",
        "return_action_key": "return_to_cockpit",
        "blocked_route_message": "Return to Project Cockpit and select an available context or accelerator.",
    }
    assert accelerator_by_key(payload, "rates")["disabled"] is True
    assert accelerator_by_key(payload, "rates")["disabled_reason"] == "ACTIVE_CONTEXT_REQUIRED"
    assert accelerator_by_key(payload, "settings")["href"] == "/settings"
    assert action_by_key(payload, "set_active_context")["disabled"] is False
    assert action_by_key(payload, "view_jobs")["disabled"] is True
    assert action_by_key(payload, "view_jobs")["disabled_reason"] == "ACTIVE_CONTEXT_REQUIRED"
    assert action_by_key(payload, "view_evidence")["disabled"] is True
    assert action_by_key(payload, "view_evidence")["disabled_reason"] == "ACTIVE_CONTEXT_REQUIRED"


def test_project_cockpit_summary_reports_active_project_without_raw_payloads(
    client,
    admin_header,
    db_session,
):
    project, profile, environment = create_context(client, admin_header)
    job = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
            "input": {"raw_reference": "SYNTHETIC_RATE_ROW_001"},
        },
        headers=admin_header,
    ).json()
    artifact = Artifact(
        project_id=project["id"],
        profile_id=profile["id"],
        environment_id=environment["id"],
        domain_name="OTM1",
        visibility="PROJECT",
        source_module="rates",
        artifact_type="rates_csv_zip",
        file_path="var/test-artifacts/synthetic-rates.zip",
        file_name="synthetic-rates.zip",
        content_type="application/zip",
        sha256="1" * 64,
        size_bytes=128,
        sensitivity_level="internal",
    )
    db_session.add(artifact)
    db_session.flush()
    evidence = Evidence(
        project_id=project["id"],
        profile_id=profile["id"],
        environment_id=environment["id"],
        domain_name="OTM1",
        visibility="PROJECT",
        source_module="rates",
        evidence_type="rates_csv_export",
        summary_json='{"status":"ok","raw_reference":"SYNTHETIC_RATE_ROW_001"}',
        artifact_id=artifact.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db_session.add(evidence)
    db_session.commit()

    response = client.get("/api/v1/platform/project-cockpit/summary", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["active_context"]["project_id"] == project["id"]
    assert payload["active_context"]["profile_id"] == profile["id"]
    assert payload["active_context"]["environment_id"] == environment["id"]
    assert payload["active_context"]["domain_name"] == "OTM1"
    assert payload["setup_status"]["status"] == "READY"
    assert payload["counts"]["recent_jobs"] == 1
    assert payload["counts"]["recent_artifacts"] == 1
    assert payload["counts"]["recent_evidence"] == 1
    assert payload["recent_jobs"][0]["id"] == job["id"]
    assert payload["recent_jobs"][0]["input_present"] is True
    assert "input" not in payload["recent_jobs"][0]
    assert payload["recent_artifacts"][0]["id"] == artifact.id
    assert "file_path" not in payload["recent_artifacts"][0]
    assert payload["recent_evidence"][0]["id"] == evidence.id
    assert payload["recent_evidence"][0]["summary"] == {"status": "ok"}
    assert payload["context_selector"]["mode"] == "PRIVATE"
    assert payload["context_selector"]["active_context"]["domain_name"] == "OTM1"
    assert payload["context_selector"]["public_view_available"] is True
    assert payload["project_info"]["status"] == "AVAILABLE"
    assert payload["project_info"]["secure_vault"]["metadata_only"] is True
    assert payload["project_info"]["secure_vault"]["secret_values_available"] is False
    assert payload["user_scope"]["role_mode"] == "DBA"
    assert payload["user_scope"]["can_view_all_domains"] is False
    assert "PUBLIC" in payload["user_scope"]["allowed_domains"]
    assert accelerator_by_key(payload, "rates")["disabled"] is False
    assert accelerator_by_key(payload, "rates")["href"] == "/rates"
    assert accelerator_by_key(payload, "home")["disabled"] is False
    assert action_by_key(payload, "view_jobs")["disabled"] is False
    assert action_by_key(payload, "view_evidence")["disabled"] is False
    assert "SYNTHETIC_RATE_ROW_001" not in str(payload)


def test_project_cockpit_summary_represents_public_view_as_selector_state(
    client,
    admin_header,
    db_session,
):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Public Cockpit Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Public Cockpit Project"},
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
    private_artifact = Artifact(
        project_id=project["id"],
        profile_id=profile["id"],
        environment_id=environment["id"],
        domain_name="OTM1",
        visibility="PROJECT",
        source_module="rates",
        artifact_type="rates_csv_zip",
        file_path="var/test-artifacts/private-cockpit.zip",
        file_name="private-cockpit.zip",
        content_type="application/zip",
        sha256="5" * 64,
        size_bytes=128,
        sensitivity_level="internal",
    )
    public_artifact = Artifact(
        project_id=project["id"],
        profile_id=profile["id"],
        environment_id=environment["id"],
        domain_name="PUBLIC",
        visibility="PUBLIC",
        source_module="rates",
        artifact_type="rates_csv_zip",
        file_path="var/test-artifacts/public-cockpit.zip",
        file_name="public-cockpit.zip",
        content_type="application/zip",
        sha256="6" * 64,
        size_bytes=128,
        sensitivity_level="internal",
    )
    db_session.add_all([private_artifact, public_artifact])
    db_session.commit()
    active_context = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
        },
        headers=admin_header,
    )

    response = client.get("/api/v1/platform/project-cockpit/summary", headers=admin_header)

    assert active_context.status_code == 200
    assert response.status_code == 200
    payload = response.json()
    assert payload["context_selector"]["mode"] == "PUBLIC"
    assert payload["context_selector"]["public_view_available"] is True
    assert payload["active_context"]["domain_name"] is None
    assert payload["active_context"]["allowed_domains"] == ["PUBLIC"]
    assert "Public View" not in [item["label"] for item in payload["module_summary"]["items"]]
    assert "private-cockpit" not in str(payload)


def test_project_cockpit_summary_limits_recent_records_to_active_context_for_non_admin(
    client,
    admin_header,
    auth_header,
    db_session,
):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Cockpit Scope Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Cockpit Scope Project"},
        headers=admin_header,
    ).json()
    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Default"},
        headers=admin_header,
    ).json()
    visible_environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    hidden_environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "UAT", "environment_type": "UAT"},
        headers=admin_header,
    ).json()
    visible_job = client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": visible_environment["id"],
            "domain_name": "otm1",
            "input": {"value": "visible"},
        },
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": hidden_environment["id"],
            "domain_name": "otm2",
            "input": {"value": "hidden"},
        },
        headers=admin_header,
    )
    visible_artifact = Artifact(
        project_id=project["id"],
        profile_id=profile["id"],
        environment_id=visible_environment["id"],
        domain_name="OTM1",
        visibility="PROJECT",
        source_module="rates",
        artifact_type="rates_csv_zip",
        file_path="var/test-artifacts/visible-cockpit.zip",
        file_name="visible-cockpit.zip",
        content_type="application/zip",
        sha256="2" * 64,
        size_bytes=128,
        sensitivity_level="internal",
    )
    hidden_artifact = Artifact(
        project_id=project["id"],
        profile_id=profile["id"],
        environment_id=hidden_environment["id"],
        domain_name="OTM2",
        visibility="PROJECT",
        source_module="rates",
        artifact_type="rates_csv_zip",
        file_path="var/test-artifacts/hidden-cockpit.zip",
        file_name="hidden-cockpit.zip",
        content_type="application/zip",
        sha256="3" * 64,
        size_bytes=128,
        sensitivity_level="internal",
    )
    db_session.add_all([visible_artifact, hidden_artifact])
    db_session.flush()
    visible_evidence = Evidence(
        project_id=project["id"],
        profile_id=profile["id"],
        environment_id=visible_environment["id"],
        domain_name="OTM1",
        visibility="PROJECT",
        source_module="rates",
        evidence_type="rates_csv_export",
        summary_json='{"status":"visible"}',
        artifact_id=visible_artifact.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    hidden_evidence = Evidence(
        project_id=project["id"],
        profile_id=profile["id"],
        environment_id=hidden_environment["id"],
        domain_name="OTM2",
        visibility="PROJECT",
        source_module="rates",
        evidence_type="rates_csv_export",
        summary_json='{"status":"hidden"}',
        artifact_id=hidden_artifact.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db_session.add_all([visible_evidence, hidden_evidence])
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Cockpit Viewer")
    capability = Capability(name="cockpit.view")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    db_session.add(
        UserProjectRole(
            user_id=user_id,
            project_id=project["id"],
            environment_id=visible_environment["id"],
            domain_name="OTM1",
            role_id=role.id,
        )
    )
    db_session.commit()
    client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": visible_environment["id"],
            "domain_name": "otm1",
        },
        headers=auth_header,
    )

    response = client.get("/api/v1/platform/project-cockpit/summary", headers=auth_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["counts"]["recent_jobs"] == 1
    assert payload["counts"]["recent_artifacts"] == 1
    assert payload["counts"]["recent_evidence"] == 1
    assert payload["recent_jobs"][0]["id"] == visible_job["id"]
    assert payload["recent_artifacts"][0]["id"] == visible_artifact.id
    assert payload["recent_evidence"][0]["id"] == visible_evidence.id
    assert payload["user_scope"]["role_mode"] == "SCOPED"
    assert payload["user_scope"]["is_dba"] is False
    assert payload["user_scope"]["allowed_domains"] == ["PUBLIC", "OTM1"]
    assert "hidden" not in str(payload).lower()


def test_project_cockpit_summary_ignores_stale_active_context_after_grant_removed(
    client,
    admin_header,
    auth_header,
    db_session,
):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Stale Cockpit Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Stale Cockpit Project"},
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
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
            "input": {"value": "stale"},
        },
        headers=admin_header,
    )
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Temporary Cockpit Viewer")
    capability = Capability(name="cockpit.view")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    grant = UserProjectRole(
        user_id=user_id,
        project_id=project["id"],
        environment_id=environment["id"],
        domain_name="OTM1",
        role_id=role.id,
    )
    db_session.add(grant)
    db_session.commit()
    active_context = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": environment["id"],
            "domain_name": "otm1",
        },
        headers=auth_header,
    )
    assert active_context.status_code == 200
    db_session.delete(grant)
    db_session.commit()

    response = client.get("/api/v1/platform/project-cockpit/summary", headers=auth_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "needs_context"
    assert payload["active_context"]["project_id"] is None
    assert payload["setup_status"] is None
    assert payload["counts"]["recent_jobs"] == 0
    assert payload["recent_jobs"] == []
    assert action_by_key(payload, "view_jobs")["disabled"] is True
    assert action_by_key(payload, "view_evidence")["disabled"] is True
    assert project["id"] not in str(payload)
    assert "Stale Cockpit Project" not in str(payload)


def test_project_cockpit_summary_ignores_active_context_after_scope_grant_changes(
    client,
    admin_header,
    auth_header,
    db_session,
):
    workspace = client.post(
        "/api/v1/platform/workspaces",
        json={"name": "Shifted Cockpit Workspace"},
        headers=admin_header,
    ).json()
    project = client.post(
        "/api/v1/platform/projects",
        json={"workspace_id": workspace["id"], "name": "Shifted Cockpit Project"},
        headers=admin_header,
    ).json()
    profile = client.post(
        "/api/v1/platform/profiles",
        json={"project_id": project["id"], "name": "Default"},
        headers=admin_header,
    ).json()
    original_environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "DEV", "environment_type": "DEV"},
        headers=admin_header,
    ).json()
    new_environment = client.post(
        "/api/v1/platform/environments",
        json={"project_id": project["id"], "name": "UAT", "environment_type": "UAT"},
        headers=admin_header,
    ).json()
    client.post(
        "/api/v1/platform/jobs",
        json={
            "job_type": "DEMO_ECHO",
            "source_module": "platform",
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": original_environment["id"],
            "domain_name": "otm1",
            "input": {"value": "original-scope"},
        },
        headers=admin_header,
    )
    artifact = Artifact(
        project_id=project["id"],
        profile_id=profile["id"],
        environment_id=original_environment["id"],
        domain_name="OTM1",
        visibility="PROJECT",
        source_module="rates",
        artifact_type="rates_csv_zip",
        file_path="var/test-artifacts/original-scope.zip",
        file_name="original-scope.zip",
        content_type="application/zip",
        sha256="4" * 64,
        size_bytes=128,
        sensitivity_level="internal",
    )
    db_session.add(artifact)
    db_session.flush()
    db_session.add(
        Evidence(
            project_id=project["id"],
            profile_id=profile["id"],
            environment_id=original_environment["id"],
            domain_name="OTM1",
            visibility="PROJECT",
            source_module="rates",
            evidence_type="rates_csv_export",
            summary_json='{"status":"original-scope"}',
            artifact_id=artifact.id,
            client_safe=True,
            sensitivity_level="client_safe",
        )
    )
    user_token = auth_header["Authorization"].split(" ", 1)[1]
    user_id = db_session.get(SessionToken, user_token).user_id
    role = Role(name="Shifted Cockpit Viewer")
    capability = Capability(name="cockpit.view")
    db_session.add_all([role, capability])
    db_session.flush()
    db_session.add(RoleCapability(role_id=role.id, capability_id=capability.id))
    grant = UserProjectRole(
        user_id=user_id,
        project_id=project["id"],
        environment_id=original_environment["id"],
        domain_name="OTM1",
        role_id=role.id,
    )
    db_session.add(grant)
    db_session.commit()
    active_context = client.post(
        "/api/v1/platform/active-context",
        json={
            "project_id": project["id"],
            "profile_id": profile["id"],
            "environment_id": original_environment["id"],
            "domain_name": "otm1",
        },
        headers=auth_header,
    )
    assert active_context.status_code == 200
    grant.environment_id = new_environment["id"]
    grant.domain_name = "OTM2"
    db_session.commit()

    response = client.get("/api/v1/platform/project-cockpit/summary", headers=auth_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "needs_context"
    assert payload["active_context"]["project_id"] is None
    assert payload["setup_status"] is None
    assert payload["counts"]["recent_jobs"] == 0
    assert payload["counts"]["recent_artifacts"] == 0
    assert payload["counts"]["recent_evidence"] == 0
    assert payload["recent_jobs"] == []
    assert payload["recent_artifacts"] == []
    assert payload["recent_evidence"] == []
    assert action_by_key(payload, "view_jobs")["disabled"] is True
    assert action_by_key(payload, "view_evidence")["disabled"] is True
    assert project["id"] not in str(payload)
    assert "Shifted Cockpit Project" not in str(payload)
    assert "original-scope" not in str(payload)
