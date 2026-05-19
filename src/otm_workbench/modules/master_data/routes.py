from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from otm_workbench.config import get_settings
from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import api_error, get_db, require_user
from otm_workbench.models import MasterDataTemplate, User
from otm_workbench.modules.master_data.templates import (
    build_master_data_template_workbook,
    seed_master_data_templates,
    serialize_master_data_template,
    validate_master_data_template,
)

router = APIRouter(prefix="/api/v1/modules/master-data", tags=["master-data"])


def dictionary_root() -> Path:
    return Path(get_settings().otm_data_dictionary_root)


@router.get("/health")
def master_data_health(user: User = Depends(require_user)):
    return {"status": "ok", "module": "master_data", "catalog_macro_object_code": "REGION"}


@router.get("/templates")
def list_master_data_templates(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    templates = db.query(MasterDataTemplate).order_by(MasterDataTemplate.code).all()
    items = [serialize_master_data_template(template) for template in templates]
    return PageResponse(items=items, total=len(items))


@router.get("/templates/{template_code}")
def get_master_data_template(
    template_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    return serialize_master_data_template(template)


@router.post("/templates/{template_code}/validate")
def validate_master_data_template_endpoint(
    template_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    return validate_master_data_template(template, dictionary_root())


@router.post("/templates/{template_code}/build-workbook")
def build_master_data_template_workbook_endpoint(
    template_code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    seed_master_data_templates(db)
    template = db.query(MasterDataTemplate).filter(MasterDataTemplate.code == template_code.upper()).first()
    if template is None:
        raise api_error(404, "MASTER_DATA_TEMPLATE_NOT_FOUND", "Master Data template not found.")
    validation = validate_master_data_template(template, dictionary_root())
    if not validation["valid"]:
        raise api_error(
            409,
            "MASTER_DATA_TEMPLATE_INVALID",
            "Master Data template must be valid before workbook generation.",
            details=validation,
        )
    return build_master_data_template_workbook(db, template, Path(get_settings().artifact_root))
