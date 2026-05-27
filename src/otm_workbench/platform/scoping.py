from dataclasses import dataclass

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from otm_workbench.models import ActiveContext


class OperationalScopeError(ValueError):
    pass


@dataclass(frozen=True)
class OperationalScope:
    project_id: str | None = None
    profile_id: str | None = None
    environment_id: str | None = None
    domain_name: str = "PUBLIC"
    can_view_all_domains: bool = False

    @property
    def allowed_domain_names(self) -> tuple[str, ...]:
        if self.can_view_all_domains:
            return ("*",)
        domains = ["PUBLIC"]
        if self.domain_name != "PUBLIC":
            domains.append(self.domain_name)
        return tuple(domains)

    @property
    def is_public_view(self) -> bool:
        return self.project_id is None and self.environment_id is None and self.domain_name == "PUBLIC"


def normalize_domain_name(domain_name: str | None) -> str:
    normalized = (domain_name or "PUBLIC").strip().upper()
    return normalized or "PUBLIC"


def normalize_visibility(visibility: str | None) -> str:
    normalized = (visibility or "PRIVATE").strip().upper()
    return normalized or "PRIVATE"


def normalize_domain_for_visibility(domain_name: str | None, visibility: str | None) -> str | None:
    if normalize_visibility(visibility) == "PUBLIC":
        return "PUBLIC"
    if not domain_name:
        return None
    return normalize_domain_name(domain_name)


def operational_scope_from_context(context: ActiveContext | None) -> OperationalScope:
    if context is None:
        return OperationalScope()
    return OperationalScope(
        project_id=context.project_id,
        profile_id=context.profile_id,
        environment_id=context.environment_id,
        domain_name=normalize_domain_name(context.domain_name),
        can_view_all_domains=bool(context.can_view_all_domains),
    )


def require_private_operational_scope(scope: OperationalScope) -> OperationalScope:
    if not scope.project_id:
        raise OperationalScopeError("Private operational records require project scope.")
    if not scope.environment_id:
        raise OperationalScopeError("Private operational records require environment scope.")
    if scope.domain_name == "PUBLIC":
        raise OperationalScopeError("Private operational records require a private domain.")
    return scope


def apply_operational_scope(query: Query, model: type, scope: OperationalScope) -> Query:
    if hasattr(model, "domain_name") and not scope.can_view_all_domains:
        private_filters = []
        if hasattr(model, "project_id") and scope.project_id:
            private_filters.append(model.project_id == scope.project_id)
        if hasattr(model, "environment_id") and scope.environment_id:
            private_filters.append(model.environment_id == scope.environment_id)
        private_filters.append(model.domain_name.in_(scope.allowed_domain_names))
        return query.filter(or_(and_(*private_filters), model.domain_name == "PUBLIC"))
    if hasattr(model, "project_id") and scope.project_id:
        query = query.filter(model.project_id == scope.project_id)
    if hasattr(model, "environment_id") and scope.environment_id:
        query = query.filter(model.environment_id == scope.environment_id)
    return query
