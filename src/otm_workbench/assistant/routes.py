from pathlib import Path

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.assistant.services import (
    AssistantSourceInput,
    AssistantSourceIndexError,
    create_assistant_source,
    index_asset_source,
    index_markdown_directory,
    rebuild_assistant_fts_index,
    search_assistant_sources,
)
from otm_workbench.assistant.saved_queries import (
    approve_saved_query,
    create_saved_query,
    search_saved_queries,
    serialize_saved_query,
)
from otm_workbench.assistant.join_patterns import (
    approve_join_pattern,
    create_join_pattern,
    search_join_patterns,
    serialize_join_pattern,
)
from otm_workbench.assistant.oracle_docs import (
    approve_oracle_doc_cache,
    blocked_live_lookup,
    create_oracle_doc_cache,
    prepare_live_lookup_request,
    search_oracle_doc_cache,
    serialize_oracle_doc_cache,
)
from otm_workbench.assistant.sql_helper import draft_joined_select, draft_single_table_select, explain_select_sql
from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_admin, require_user
from otm_workbench.models import ActiveContext, Asset, AssetVersion, User
from otm_workbench.platform.scoping import OperationalScope, apply_operational_scope, operational_scope_from_context

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


class AssistantSourceCreateRequest(BaseModel):
    title: str
    source_type: str
    source_uri: str = ""
    body_text: str = ""
    module_id: str | None = None
    project_id: str | None = None
    profile_id: str | None = None
    environment_id: str | None = None
    domain_name: str | None = None
    visibility: str = "PRIVATE"
    access_policy_id: str | None = None


class WorkbenchDocsIndexRequest(BaseModel):
    root_key: str = "assistant_planning"


class SqlDraftRequest(BaseModel):
    table_name: str
    columns: list[str]
    filter_column: str
    purpose: str = "Draft a safe OTM SELECT."


class SqlJoinedDraftRequest(BaseModel):
    join_pattern_id: str
    left_columns: list[str]
    right_columns: list[str]
    filter_table: str
    filter_column: str
    purpose: str = "Draft a safe joined OTM SELECT."


class SqlExplainRequest(BaseModel):
    sql_text: str


class SavedQueryCreateRequest(BaseModel):
    name: str
    purpose: str
    sql_text: str
    module_id: str | None = None
    visibility: str = "PRIVATE"
    project_id: str | None = None
    profile_id: str | None = None
    environment_id: str | None = None
    domain_name: str | None = None
    access_policy_id: str | None = None


class JoinPatternCreateRequest(BaseModel):
    name: str
    left_table: str
    left_column: str
    right_table: str
    right_column: str
    join_type: str = "INNER"
    business_meaning: str = ""
    module_id: str | None = None
    source_type: str = "MANUAL"
    source_id: str | None = None


class OracleDocCacheCreateRequest(BaseModel):
    title: str
    url: str
    product_area: str
    topic: str
    version_label: str = ""
    summary: str = ""


class OracleDocLiveLookupRequest(BaseModel):
    query: str
    private_terms: list[str] = []


class AssistantSearchResponseItem(BaseModel):
    source_id: str
    source_title: str
    source_type: str
    source_uri: str
    module_id: str | None = None
    domain_name: str | None = None
    visibility: str
    chunk_id: str
    snippet: str
    rank: float


def active_context_for_user(db: Session, user: User) -> ActiveContext | None:
    return db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()


def allowed_domains_for_context(domain_name: str | None, can_view_all_domains: bool) -> list[str]:
    scope = OperationalScope(domain_name=(domain_name or "PUBLIC").upper(), can_view_all_domains=can_view_all_domains)
    return list(scope.allowed_domain_names)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def dictionary_root() -> Path:
    return Path(get_settings().otm_data_dictionary_root)


def approved_workbench_doc_roots() -> dict[str, Path]:
    root = repository_root()
    return {
        "assistant_planning": root / "docs" / "agent" / "assistant-planning",
        "otm_workbench_docs": root / "docs" / "otm-workbench",
    }


def scoped_asset_query(db: Session, user: User):
    query = db.query(Asset)
    context = active_context_for_user(db, user)
    if context is None:
        if not user.is_admin:
            return query.filter(Asset.id.is_(None))
        return query
    return apply_operational_scope(query, Asset, operational_scope_from_context(context))


def get_scoped_asset_or_404(db: Session, user: User, asset_id: str) -> Asset:
    asset = scoped_asset_query(db, user).filter(Asset.id == asset_id).first()
    if asset is None:
        raise api_error(404, "ASSET_NOT_FOUND", "Asset not found.")
    return asset


@router.get("/health")
def assistant_health(user: User = Depends(require_user)):
    return {"status": "ok", "module": "assistant", "capabilities": ["source_index", "fts_search"]}


@router.post("/sources", status_code=status.HTTP_201_CREATED)
def create_source(
    request: AssistantSourceCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    context = active_context_for_user(db, user)
    source = create_assistant_source(
        db,
        AssistantSourceInput(
            title=request.title,
            source_type=request.source_type,
            source_uri=request.source_uri,
            body_text=request.body_text,
            module_id=request.module_id,
            project_id=request.project_id or (context.project_id if context else None),
            profile_id=request.profile_id or (context.profile_id if context else None),
            environment_id=request.environment_id or (context.environment_id if context else None),
            domain_name=request.domain_name or (context.domain_name if context else None),
            visibility=request.visibility,
            access_policy_id=request.access_policy_id,
            created_by=user.id,
        ),
    )
    return {
        "id": source.id,
        "title": source.title,
        "source_type": source.source_type,
        "source_uri": source.source_uri,
        "module_id": source.module_id,
        "domain_name": source.domain_name,
        "visibility": source.visibility,
        "status": source.status,
    }


@router.post("/index/rebuild")
def rebuild_index(db: Session = Depends(get_db), user: User = Depends(require_user)):
    run = rebuild_assistant_fts_index(db)
    return {
        "id": run.id,
        "status": run.status,
        "source_count": run.source_count,
        "chunk_count": run.chunk_count,
        "message": run.message,
    }


@router.post("/index/workbench-docs")
def index_workbench_docs(
    request: WorkbenchDocsIndexRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    roots = approved_workbench_doc_roots()
    root = roots.get(request.root_key)
    if root is None:
        raise api_error(
            400,
            "ASSISTANT_SOURCE_ROOT_NOT_APPROVED",
            "Assistant source root is not approved.",
            details={"root_key": request.root_key, "approved_root_keys": sorted(roots)},
        )
    try:
        result = index_markdown_directory(
            db,
            root=root,
            allowed_roots=list(roots.values()),
            visibility="PUBLIC",
            created_by=user.id,
        )
    except AssistantSourceIndexError as exc:
        raise api_error(400, "ASSISTANT_SOURCE_INDEX_ERROR", str(exc)) from exc
    run = rebuild_assistant_fts_index(db)
    return {
        "root_key": request.root_key,
        "source_count": result.source_count,
        "chunk_count": result.chunk_count,
        "skipped_count": result.skipped_count,
        "index_run_id": run.id,
        "index_status": run.status,
    }


@router.post("/index/assets/{asset_id}")
def index_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    asset = get_scoped_asset_or_404(db, user, asset_id)
    if not asset.current_version_id:
        raise api_error(409, "ASSET_VERSION_MISSING", "Asset has no current version to index.")
    version = db.query(AssetVersion).filter(AssetVersion.id == asset.current_version_id).first()
    if version is None:
        raise api_error(409, "ASSET_VERSION_MISSING", "Asset current version was not found.")
    try:
        result = index_asset_source(db, asset=asset, version=version)
    except AssistantSourceIndexError as exc:
        raise api_error(400, "ASSISTANT_SOURCE_INDEX_ERROR", str(exc)) from exc
    run = rebuild_assistant_fts_index(db)
    return {
        "asset_id": asset.id,
        "asset_version_id": version.id,
        "source_id": result.source.id,
        "source_type": result.source.source_type,
        "source_uri": result.source.source_uri,
        "content_indexed": result.content_indexed,
        "chunk_count": result.chunk_count,
        "index_run_id": run.id,
        "index_status": run.status,
    }


@router.post("/sql/draft")
def draft_sql(request: SqlDraftRequest, user: User = Depends(require_user)):
    return draft_single_table_select(
        dictionary_root(),
        table_name=request.table_name,
        columns=request.columns,
        filter_column=request.filter_column,
        purpose=request.purpose,
    )


@router.post("/sql/draft-join")
def draft_joined_sql(
    request: SqlJoinedDraftRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    return draft_joined_select(
        db,
        dictionary_root(),
        join_pattern_id=request.join_pattern_id,
        left_columns=request.left_columns,
        right_columns=request.right_columns,
        filter_table=request.filter_table,
        filter_column=request.filter_column,
        purpose=request.purpose,
    )


@router.post("/sql/explain")
def explain_sql(request: SqlExplainRequest, user: User = Depends(require_user)):
    return explain_select_sql(dictionary_root(), request.sql_text)


@router.post("/sql/saved-queries", status_code=status.HTTP_201_CREATED)
def create_sql_saved_query(
    request: SavedQueryCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    context = active_context_for_user(db, user)
    query = create_saved_query(
        db,
        name=request.name,
        purpose=request.purpose,
        sql_text=request.sql_text,
        module_id=request.module_id,
        visibility=request.visibility,
        project_id=request.project_id or (context.project_id if context else None),
        profile_id=request.profile_id or (context.profile_id if context else None),
        environment_id=request.environment_id or (context.environment_id if context else None),
        domain_name=request.domain_name or (context.domain_name if context else None),
        access_policy_id=request.access_policy_id,
        created_by=user.id,
    )
    return serialize_saved_query(query)


@router.post("/sql/saved-queries/{query_id}/approve")
def approve_sql_saved_query(
    query_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    query = approve_saved_query(db, query_id, dictionary_root=dictionary_root(), reviewed_by=user.id)
    return serialize_saved_query(query)


@router.get("/sql/saved-queries")
def list_sql_saved_queries(
    query: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    context = active_context_for_user(db, user)
    allowed_domains = allowed_domains_for_context(
        context.domain_name if context else None,
        user.is_admin or bool(context and context.can_view_all_domains),
    )
    items = search_saved_queries(db, query_text=query, allowed_domains=allowed_domains)
    return PageResponse(items=items, total=len(items), page=1, page_size=len(items))


@router.post("/sql/join-patterns", status_code=status.HTTP_201_CREATED)
def create_sql_join_pattern(
    request: JoinPatternCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    pattern = create_join_pattern(
        db,
        name=request.name,
        left_table=request.left_table,
        left_column=request.left_column,
        right_table=request.right_table,
        right_column=request.right_column,
        join_type=request.join_type,
        business_meaning=request.business_meaning,
        module_id=request.module_id,
        source_type=request.source_type,
        source_id=request.source_id,
        created_by=user.id,
    )
    return serialize_join_pattern(pattern)


@router.post("/sql/join-patterns/{pattern_id}/approve")
def approve_sql_join_pattern(
    pattern_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    pattern = approve_join_pattern(db, pattern_id, dictionary_root=dictionary_root(), reviewed_by=user.id)
    return serialize_join_pattern(pattern)


@router.get("/sql/join-patterns")
def list_sql_join_patterns(
    query: str = "",
    table_name: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    items = search_join_patterns(db, query_text=query, table_name=table_name)
    return PageResponse(items=items, total=len(items), page=1, page_size=len(items))


@router.post("/oracle-docs/cache", status_code=status.HTTP_201_CREATED)
def create_oracle_docs_cache_record(
    request: OracleDocCacheCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    try:
        record = create_oracle_doc_cache(
            db,
            title=request.title,
            url=request.url,
            product_area=request.product_area,
            topic=request.topic,
            version_label=request.version_label,
            summary=request.summary,
            created_by=user.id,
        )
    except ValueError as exc:
        raise api_error(400, "ORACLE_DOC_URL_NOT_APPROVED", str(exc)) from exc
    return serialize_oracle_doc_cache(record)


@router.post("/oracle-docs/cache/{record_id}/approve")
def approve_oracle_docs_cache_record(
    record_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    try:
        record = approve_oracle_doc_cache(db, record_id, reviewed_by=user.id)
    except ValueError as exc:
        raise api_error(404, "ORACLE_DOC_CACHE_NOT_FOUND", str(exc)) from exc
    return serialize_oracle_doc_cache(record)


@router.get("/oracle-docs/search")
def search_oracle_docs_cache(
    query: str = "",
    product_area: str | None = None,
    topic: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    items = search_oracle_doc_cache(db, query_text=query, product_area=product_area, topic=topic)
    return PageResponse(items=items, total=len(items), page=1, page_size=len(items))


@router.post("/oracle-docs/live-lookup")
def request_oracle_docs_live_lookup(
    request: OracleDocLiveLookupRequest,
    user: User = Depends(require_user),
):
    return prepare_live_lookup_request(request.query, request.private_terms)


@router.get("/search", response_model=PageResponse[AssistantSearchResponseItem])
def search_sources(
    query: str = Query(min_length=1),
    limit: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    context = active_context_for_user(db, user)
    allowed_domains = allowed_domains_for_context(
        context.domain_name if context else None,
        user.is_admin or bool(context and context.can_view_all_domains),
    )
    items = search_assistant_sources(
        db,
        query_text=query,
        allowed_domains=allowed_domains,
        project_id=context.project_id if context else None,
        environment_id=context.environment_id if context else None,
        profile_id=context.profile_id if context else None,
        limit=limit,
    )
    return PageResponse(items=items, total=len(items), page=1, page_size=len(items))
