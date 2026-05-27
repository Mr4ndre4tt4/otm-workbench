import pytest

from otm_workbench.models import ActiveContext, Job
from otm_workbench.platform.scoping import (
    OperationalScopeError,
    apply_operational_scope,
    operational_scope_from_context,
    require_private_operational_scope,
)


def test_default_scope_only_allows_explicit_public_records():
    scope = operational_scope_from_context(None)

    assert scope.project_id is None
    assert scope.profile_id is None
    assert scope.environment_id is None
    assert scope.domain_name == "PUBLIC"
    assert scope.allowed_domain_names == ("PUBLIC",)
    assert scope.is_public_view is True
    assert scope.can_view_all_domains is False


def test_private_scope_normalizes_domain_and_keeps_environment():
    context = ActiveContext(
        user_id="user_demo",
        project_id="project_demo",
        profile_id="profile_demo",
        environment_id="env_dev",
        domain_name="otm1",
    )

    scope = operational_scope_from_context(context)

    assert scope.project_id == "project_demo"
    assert scope.profile_id == "profile_demo"
    assert scope.environment_id == "env_dev"
    assert scope.domain_name == "OTM1"
    assert scope.allowed_domain_names == ("PUBLIC", "OTM1")
    assert scope.is_public_view is False
    assert scope.can_view_all_domains is False


def test_dba_scope_keeps_context_and_all_domain_visibility():
    context = ActiveContext(
        user_id="dba_demo",
        project_id="project_demo",
        environment_id="env_prod",
        domain_name="otm2",
        can_view_all_domains=True,
    )

    scope = operational_scope_from_context(context)

    assert scope.project_id == "project_demo"
    assert scope.environment_id == "env_prod"
    assert scope.domain_name == "OTM2"
    assert scope.allowed_domain_names == ("*",)
    assert scope.can_view_all_domains is True


def test_private_operational_scope_requires_project_environment_and_private_domain():
    public_scope = operational_scope_from_context(None)
    missing_environment = operational_scope_from_context(
        ActiveContext(user_id="user_demo", project_id="project_demo", domain_name="otm1")
    )

    with pytest.raises(OperationalScopeError, match="project"):
        require_private_operational_scope(public_scope)
    with pytest.raises(OperationalScopeError, match="environment"):
        require_private_operational_scope(missing_environment)

    private_scope = operational_scope_from_context(
        ActiveContext(
            user_id="user_demo",
            project_id="project_demo",
            environment_id="env_dev",
            domain_name="otm1",
        )
    )
    assert require_private_operational_scope(private_scope) is private_scope


def test_apply_operational_scope_filters_project_environment_and_domain(db_session):
    matching = Job(
        job_type="DEMO",
        source_module="rates",
        project_id="project_demo",
        environment_id="env_dev",
        domain_name="OTM1",
    )
    public = Job(job_type="DEMO", source_module="rates", domain_name="PUBLIC")
    wrong_environment = Job(
        job_type="DEMO",
        source_module="rates",
        project_id="project_demo",
        environment_id="env_test",
        domain_name="OTM1",
    )
    wrong_domain = Job(
        job_type="DEMO",
        source_module="rates",
        project_id="project_demo",
        environment_id="env_dev",
        domain_name="OTM2",
    )
    db_session.add_all([matching, public, wrong_environment, wrong_domain])
    db_session.commit()
    scope = operational_scope_from_context(
        ActiveContext(
            user_id="user_demo",
            project_id="project_demo",
            environment_id="env_dev",
            domain_name="otm1",
        )
    )

    rows = apply_operational_scope(db_session.query(Job), Job, scope).all()

    assert {row.id for row in rows} == {matching.id, public.id}


def test_apply_operational_scope_allows_dba_to_see_all_domains_in_environment(db_session):
    otm1 = Job(
        job_type="DEMO",
        source_module="rates",
        project_id="project_demo",
        environment_id="env_dev",
        domain_name="OTM1",
    )
    otm2 = Job(
        job_type="DEMO",
        source_module="rates",
        project_id="project_demo",
        environment_id="env_dev",
        domain_name="OTM2",
    )
    other_environment = Job(
        job_type="DEMO",
        source_module="rates",
        project_id="project_demo",
        environment_id="env_test",
        domain_name="OTM3",
    )
    db_session.add_all([otm1, otm2, other_environment])
    db_session.commit()
    scope = operational_scope_from_context(
        ActiveContext(
            user_id="dba_demo",
            project_id="project_demo",
            environment_id="env_dev",
            domain_name="otm1",
            can_view_all_domains=True,
        )
    )

    rows = apply_operational_scope(db_session.query(Job), Job, scope).order_by(Job.domain_name).all()

    assert [row.id for row in rows] == [otm1.id, otm2.id]
