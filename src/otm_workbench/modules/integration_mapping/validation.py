from dataclasses import dataclass

from sqlalchemy.orm import Session

from otm_workbench.models import (
    IntegrationDefinition,
    IntegrationJoinRule,
    IntegrationLookupDefinition,
    IntegrationLoopDefinition,
    IntegrationMapping,
)
from otm_workbench.modules.integration_mapping.joins import ALLOWED_JOIN_OPERATORS
from otm_workbench.modules.integration_mapping.lookups import ALLOWED_LOOKUP_TYPES
from otm_workbench.modules.integration_mapping.mappings import schema_path_exists
from otm_workbench.modules.integration_mapping.transform_types import transform_type_is_active


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    entity_type: str
    entity_id: str
    field: str
    message: str


def issue(
    *,
    code: str,
    entity_type: str,
    entity_id: str,
    field: str,
    message: str,
    severity: str = "ERROR",
) -> ValidationIssue:
    return ValidationIssue(
        severity=severity,
        code=code,
        entity_type=entity_type,
        entity_id=entity_id,
        field=field,
        message=message,
    )


def path_issue(entity_type: str, entity_id: str, field: str, path: str) -> ValidationIssue:
    return issue(
        code="INTEGRATION_VALIDATION_PATH_MISSING",
        entity_type=entity_type,
        entity_id=entity_id,
        field=field,
        message=f"{field} does not exist in the referenced schema document: {path}",
    )


def catalog_issue(entity_type: str, entity_id: str, field: str, value: str) -> ValidationIssue:
    return issue(
        code="INTEGRATION_VALIDATION_CATALOG_INVALID",
        entity_type=entity_type,
        entity_id=entity_id,
        field=field,
        message=f"{field} is not active in the controlled Integration Mapping catalog: {value}",
    )


def validate_mapping(db: Session, mapping: IntegrationMapping) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not schema_path_exists(db, schema_document_id=mapping.source_schema_document_id, path=mapping.source_path):
        issues.append(path_issue("mapping", mapping.id, "source_path", mapping.source_path))
    if not schema_path_exists(db, schema_document_id=mapping.target_schema_document_id, path=mapping.target_path):
        issues.append(path_issue("mapping", mapping.id, "target_path", mapping.target_path))
    if not transform_type_is_active(db, mapping.transform_type):
        issues.append(catalog_issue("mapping", mapping.id, "transform_type", mapping.transform_type))
    return issues


def validate_loop(db: Session, loop: IntegrationLoopDefinition) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not schema_path_exists(db, schema_document_id=loop.source_schema_document_id, path=loop.source_collection_path):
        issues.append(path_issue("loop", loop.id, "source_collection_path", loop.source_collection_path))
    if not schema_path_exists(db, schema_document_id=loop.target_schema_document_id, path=loop.target_collection_path):
        issues.append(path_issue("loop", loop.id, "target_collection_path", loop.target_collection_path))
    return issues


def validate_join(db: Session, join_rule: IntegrationJoinRule) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not schema_path_exists(db, schema_document_id=join_rule.source_schema_document_id, path=join_rule.left_path):
        issues.append(path_issue("join", join_rule.id, "left_path", join_rule.left_path))
    if not schema_path_exists(db, schema_document_id=join_rule.source_schema_document_id, path=join_rule.right_path):
        issues.append(path_issue("join", join_rule.id, "right_path", join_rule.right_path))
    if join_rule.operator not in ALLOWED_JOIN_OPERATORS:
        issues.append(catalog_issue("join", join_rule.id, "operator", join_rule.operator))
    return issues


def validate_lookup(db: Session, lookup: IntegrationLookupDefinition) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not schema_path_exists(db, schema_document_id=lookup.source_schema_document_id, path=lookup.input_path):
        issues.append(path_issue("lookup", lookup.id, "input_path", lookup.input_path))
    if not schema_path_exists(db, schema_document_id=lookup.target_schema_document_id, path=lookup.output_path):
        issues.append(path_issue("lookup", lookup.id, "output_path", lookup.output_path))
    if lookup.lookup_type not in ALLOWED_LOOKUP_TYPES:
        issues.append(catalog_issue("lookup", lookup.id, "lookup_type", lookup.lookup_type))
    return issues


def serialize_issue(validation_issue: ValidationIssue) -> dict[str, str]:
    return {
        "severity": validation_issue.severity,
        "code": validation_issue.code,
        "entity_type": validation_issue.entity_type,
        "entity_id": validation_issue.entity_id,
        "field": validation_issue.field,
        "message": validation_issue.message,
    }


def validate_integration_definition(db: Session, definition: IntegrationDefinition) -> dict[str, object]:
    issues: list[ValidationIssue] = []
    mappings = db.query(IntegrationMapping).filter(IntegrationMapping.definition_id == definition.id).all()
    loops = db.query(IntegrationLoopDefinition).filter(IntegrationLoopDefinition.definition_id == definition.id).all()
    joins = db.query(IntegrationJoinRule).filter(IntegrationJoinRule.definition_id == definition.id).all()
    lookups = (
        db.query(IntegrationLookupDefinition).filter(IntegrationLookupDefinition.definition_id == definition.id).all()
    )
    for mapping in mappings:
        issues.extend(validate_mapping(db, mapping))
    for loop in loops:
        issues.extend(validate_loop(db, loop))
    for join_rule in joins:
        issues.extend(validate_join(db, join_rule))
    for lookup in lookups:
        issues.extend(validate_lookup(db, lookup))
    return {
        "definition_id": definition.id,
        "is_valid": not issues,
        "issue_count": len(issues),
        "issues": [serialize_issue(validation_issue) for validation_issue in issues],
    }
