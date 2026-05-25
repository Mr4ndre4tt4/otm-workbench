from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_admin, require_user
from otm_workbench.models import ActiveContext, User
from otm_workbench.catalog.services import (
    create_schema_pack,
    get_macro_object,
    get_schema_pack,
    get_schema_root,
    index_schema_pack,
    list_dictionary_tables,
    list_macro_object_schema_links,
    list_macro_objects,
    list_schema_packs,
    list_schema_paths,
    list_schema_roots,
    list_service_operations,
    macro_object_tables,
    reference_options_payload,
    safe_load_table,
    serialize_columns,
    serialize_macro_object_schema_link,
    serialize_macro_object,
    serialize_macro_object_load_plan,
    serialize_macro_object_table,
    serialize_schema_pack,
    serialize_schema_path,
    serialize_schema_root,
    serialize_service_operation,
    SensitiveSchemaContentError,
    serialize_table_definition,
    validate_column,
    validate_table,
)
from otm_workbench.reference.services import ReferenceContext, validate_reference_value

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


class ValidateTableRequest(BaseModel):
    table_name: str
    usage: str | None = None


class ValidateColumnRequest(BaseModel):
    table_name: str
    column_name: str


class ValidateReferenceRequest(BaseModel):
    module_id: str
    field_name: str
    value: str
    domain_name: str | None = None
    project_id: str | None = None
    environment_id: str | None = None
    profile_id: str | None = None
    can_view_all_domains: bool = False


class CreateSchemaPackRequest(BaseModel):
    code: str
    name: str
    otm_version: str
    source_type: str
    source_path: str
    content_hash: str = ""
    asset_id: str | None = None


def dictionary_root() -> Path:
    return Path(get_settings().otm_data_dictionary_root)


def active_context_for_user(db: Session, user: User) -> ActiveContext | None:
    return db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()


def effective_reference_context(
    context: ActiveContext | None,
    *,
    domain_name: str | None,
    project_id: str | None,
    environment_id: str | None,
    profile_id: str | None,
    can_view_all_domains: bool,
) -> ReferenceContext:
    return ReferenceContext(
        project_id=project_id or (context.project_id if context else None),
        environment_id=environment_id or (context.environment_id if context else None),
        profile_id=profile_id or (context.profile_id if context else None),
        domain_name=domain_name or (context.domain_name if context and context.domain_name else "OTM1"),
        can_view_all_domains=can_view_all_domains or bool(context and context.can_view_all_domains),
    )


@router.get("/health")
def catalog_health(user: User = Depends(require_user)):
    return {"status": "ok", "module": "catalog"}


@router.get("/tables")
def list_catalog_tables(
    query: str | None = None,
    limit: int = 50,
    user: User = Depends(require_user),
):
    items, total = list_dictionary_tables(dictionary_root(), query=query, limit=limit)
    return PageResponse(items=items, total=total, page=1, page_size=len(items))


@router.get("/tables/{table_name}")
def get_catalog_table(table_name: str, user: User = Depends(require_user)):
    definition = safe_load_table(dictionary_root(), table_name)
    if definition is None:
        raise api_error(404, "CATALOG_TABLE_NOT_FOUND", "Catalog table not found.")
    return serialize_table_definition(definition)


@router.get("/tables/{table_name}/columns")
def list_catalog_table_columns(table_name: str, user: User = Depends(require_user)):
    definition = safe_load_table(dictionary_root(), table_name)
    if definition is None:
        raise api_error(404, "CATALOG_TABLE_NOT_FOUND", "Catalog table not found.")
    items = serialize_columns(definition)
    return PageResponse(items=items, total=len(items))


@router.get("/reference/options")
def list_catalog_reference_options(
    object_type: str,
    domain_name: str | None = None,
    project_id: str | None = None,
    environment_id: str | None = None,
    profile_id: str | None = None,
    can_view_all_domains: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    context = active_context_for_user(db, user)
    reference_context = effective_reference_context(
        context,
        domain_name=domain_name,
        project_id=project_id,
        environment_id=environment_id,
        profile_id=profile_id,
        can_view_all_domains=can_view_all_domains,
    )
    return reference_options_payload(
        db,
        object_type=object_type,
        domain_name=reference_context.domain_name,
        project_id=reference_context.project_id,
        environment_id=reference_context.environment_id,
        profile_id=reference_context.profile_id,
        can_view_all_domains=reference_context.can_view_all_domains,
    )


@router.get("/macro-objects")
def list_catalog_macro_objects(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    items = [serialize_macro_object(db, item) for item in list_macro_objects(db, dictionary_root())]
    return PageResponse(items=items, total=len(items))


@router.get("/macro-objects/{macro_object_code}")
def get_catalog_macro_object(
    macro_object_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    macro = get_macro_object(db, dictionary_root(), macro_object_code)
    if macro is None:
        raise api_error(404, "CATALOG_MACRO_OBJECT_NOT_FOUND", "Catalog macro-object not found.")
    return serialize_macro_object(db, macro, include_children=True)


@router.get("/macro-objects/{macro_object_code}/tables")
def list_catalog_macro_object_tables(
    macro_object_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    macro = get_macro_object(db, dictionary_root(), macro_object_code)
    if macro is None:
        raise api_error(404, "CATALOG_MACRO_OBJECT_NOT_FOUND", "Catalog macro-object not found.")
    items = [serialize_macro_object_table(row) for row in macro_object_tables(db, macro)]
    return PageResponse(items=items, total=len(items))


@router.get("/macro-objects/{macro_object_code}/load-plan")
def get_catalog_macro_object_load_plan(
    macro_object_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    macro = get_macro_object(db, dictionary_root(), macro_object_code)
    if macro is None:
        raise api_error(404, "CATALOG_MACRO_OBJECT_NOT_FOUND", "Catalog macro-object not found.")
    return serialize_macro_object_load_plan(db, macro)


@router.get("/macro-objects/{macro_object_code}/schema-links")
def list_catalog_macro_object_schema_links(
    macro_object_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    rows = list_macro_object_schema_links(db, macro_object_code)
    items = [serialize_macro_object_schema_link(link, root, pack, schema_file) for link, root, pack, schema_file in rows]
    return {
        "macro_object_code": macro_object_code.upper(),
        "items": items,
        "total": len(items),
    }


@router.post("/schema-packs")
def create_catalog_schema_pack(
    payload: CreateSchemaPackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    pack = create_schema_pack(
        db,
        code=payload.code,
        name=payload.name,
        otm_version=payload.otm_version,
        source_type=payload.source_type,
        source_path=payload.source_path,
        content_hash=payload.content_hash,
        asset_id=payload.asset_id,
        created_by=user.email,
    )
    return serialize_schema_pack(pack)


@router.get("/schema-packs")
def list_catalog_schema_packs(
    otm_version: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    items = [serialize_schema_pack(pack) for pack in list_schema_packs(db, otm_version=otm_version, status=status)]
    return PageResponse(items=items, total=len(items), page_size=len(items))


@router.get("/schema-packs/{schema_pack_id}")
def get_catalog_schema_pack(
    schema_pack_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    pack = get_schema_pack(db, schema_pack_id)
    if pack is None:
        raise api_error(404, "SCHEMA_PACK_NOT_FOUND", "Schema pack not found.")
    return serialize_schema_pack(pack)


@router.post("/schema-packs/{schema_pack_id}/index")
def index_catalog_schema_pack(
    schema_pack_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    pack = get_schema_pack(db, schema_pack_id)
    if pack is None:
        raise api_error(404, "SCHEMA_PACK_NOT_FOUND", "Schema pack not found.")
    try:
        return index_schema_pack(db, pack, created_by=user.email)
    except FileNotFoundError:
        raise api_error(400, "SCHEMA_PACK_SOURCE_NOT_FOUND", "Schema pack source folder was not found.")
    except SensitiveSchemaContentError:
        raise api_error(400, "SCHEMA_PACK_SENSITIVE_CONTENT", "Schema pack contains blocked sensitive content.")


@router.get("/schema-roots")
def list_catalog_schema_roots(
    schema_pack_id: str | None = None,
    root_name: str | None = None,
    domain_area: str | None = None,
    recommended_module: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    roots = list_schema_roots(
        db,
        schema_pack_id=schema_pack_id,
        root_name=root_name,
        domain_area=domain_area,
        recommended_module=recommended_module,
    )
    items = [serialize_schema_root(root) for root in roots]
    return PageResponse(items=items, total=len(items), page_size=len(items))


@router.get("/schema-roots/{schema_root_id}")
def get_catalog_schema_root(
    schema_root_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    root = get_schema_root(db, schema_root_id)
    if root is None:
        raise api_error(404, "SCHEMA_ROOT_NOT_FOUND", "Schema root not found.")
    return serialize_schema_root(root)


@router.get("/schema-roots/{schema_root_id}/paths")
def list_catalog_schema_root_paths(
    schema_root_id: str,
    query: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    if get_schema_root(db, schema_root_id) is None:
        raise api_error(404, "SCHEMA_ROOT_NOT_FOUND", "Schema root not found.")
    paths = list_schema_paths(db, schema_root_id=schema_root_id, query_text=query)
    items = [serialize_schema_path(path) for path in paths]
    return PageResponse(items=items, total=len(items), page_size=len(items))


@router.get("/schema-operations")
def list_catalog_schema_operations(
    schema_pack_id: str | None = None,
    service_name: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    operations = list_service_operations(db, schema_pack_id=schema_pack_id, service_name=service_name)
    items = [serialize_service_operation(operation) for operation in operations]
    return PageResponse(items=items, total=len(items), page_size=len(items))


@router.post("/validate/table")
def validate_catalog_table(
    payload: ValidateTableRequest,
    user: User = Depends(require_user),
):
    return validate_table(dictionary_root(), payload.table_name, payload.usage)


@router.post("/validate/column")
def validate_catalog_column(
    payload: ValidateColumnRequest,
    user: User = Depends(require_user),
):
    return validate_column(dictionary_root(), payload.table_name, payload.column_name)


@router.post("/validate/reference")
def validate_catalog_reference(
    payload: ValidateReferenceRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    active_context = active_context_for_user(db, user)
    context = effective_reference_context(
        active_context,
        project_id=payload.project_id,
        environment_id=payload.environment_id,
        profile_id=payload.profile_id,
        domain_name=payload.domain_name,
        can_view_all_domains=payload.can_view_all_domains,
    )
    result = validate_reference_value(
        db,
        context,
        payload.module_id,
        payload.field_name,
        payload.value,
    )
    return result.__dict__
