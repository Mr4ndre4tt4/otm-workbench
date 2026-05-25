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
from otm_workbench.modules.integration_mapping.mappings import parse_transform_config, schema_path_exists
from otm_workbench.modules.integration_mapping.transform_types import (
    transform_type_is_active,
    transform_type_requires_expression,
)


NDD_EXTERNAL_DELIVERY_REQUIRED_TARGETS = (
    "$.NumeroViagem",
    "$.DataEmissao",
    "$.Entregas[]",
    "$.Entregas[].NumeroDocumento",
    "$.Entregas[].ChaveAcesso",
)

SPECIFICATION_BLOCKING_ISSUE_CODES = {
    "INTEGRATION_VALIDATION_PATH_MISSING",
    "INTEGRATION_VALIDATION_CATALOG_INVALID",
}


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


def has_text_value(config: dict[str, object], key: str) -> bool:
    value = config.get(key)
    return isinstance(value, str) and bool(value.strip())


def validate_transform_config(mapping: IntegrationMapping) -> ValidationIssue | None:
    transform_type = mapping.transform_type.upper()
    config = parse_transform_config(mapping.transform_config_json)
    if not config:
        return issue(
            code="INTEGRATION_VALIDATION_TRANSFORM_CONFIG_MISSING",
            entity_type="mapping",
            entity_id=mapping.id,
            field="transform_config",
            message=f"transform_type requires persisted config metadata: {mapping.transform_type}",
        )
    if transform_type == "CONSTANT" and "value" not in config:
        return issue(
            code="INTEGRATION_VALIDATION_TRANSFORM_CONFIG_INVALID",
            entity_type="mapping",
            entity_id=mapping.id,
            field="transform_config",
            message="CONSTANT transform_config must include a value key.",
        )
    if transform_type == "CONCAT":
        parts = config.get("parts")
        if not isinstance(parts, list) or not parts:
            return issue(
                code="INTEGRATION_VALIDATION_TRANSFORM_CONFIG_INVALID",
                entity_type="mapping",
                entity_id=mapping.id,
                field="transform_config",
                message="CONCAT transform_config must include a non-empty parts array.",
            )
    if transform_type == "DATE_FORMAT" and not (
        has_text_value(config, "source_format") and has_text_value(config, "target_format")
    ):
        return issue(
            code="INTEGRATION_VALIDATION_TRANSFORM_CONFIG_INVALID",
            entity_type="mapping",
            entity_id=mapping.id,
            field="transform_config",
            message="DATE_FORMAT transform_config must include source_format and target_format.",
        )
    if transform_type == "FILTER_BY_QUALIFIER" and not (
        has_text_value(config, "collection_path")
        and has_text_value(config, "qualifier_path")
        and has_text_value(config, "qualifier_value")
        and has_text_value(config, "value_path")
    ):
        return issue(
            code="INTEGRATION_VALIDATION_TRANSFORM_CONFIG_INVALID",
            entity_type="mapping",
            entity_id=mapping.id,
            field="transform_config",
            message=(
                "FILTER_BY_QUALIFIER transform_config must include collection_path, "
                "qualifier_path, qualifier_value, and value_path."
            ),
        )
    if transform_type == "COUNT_DISTINCT" and not (
        has_text_value(config, "collection_path") and has_text_value(config, "value_path")
    ):
        return issue(
            code="INTEGRATION_VALIDATION_TRANSFORM_CONFIG_INVALID",
            entity_type="mapping",
            entity_id=mapping.id,
            field="transform_config",
            message="COUNT_DISTINCT transform_config must include collection_path and value_path.",
        )
    return None


def validate_mapping(db: Session, mapping: IntegrationMapping) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not schema_path_exists(db, schema_document_id=mapping.source_schema_document_id, path=mapping.source_path):
        issues.append(path_issue("mapping", mapping.id, "source_path", mapping.source_path))
    if not schema_path_exists(db, schema_document_id=mapping.target_schema_document_id, path=mapping.target_path):
        issues.append(path_issue("mapping", mapping.id, "target_path", mapping.target_path))
    if not transform_type_is_active(db, mapping.transform_type):
        issues.append(catalog_issue("mapping", mapping.id, "transform_type", mapping.transform_type))
    elif transform_type_requires_expression(db, mapping.transform_type):
        transform_config_issue = validate_transform_config(mapping)
        if transform_config_issue is not None:
            issues.append(transform_config_issue)
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
    if join_rule.left_path == join_rule.right_path:
        issues.append(
            issue(
                code="INTEGRATION_VALIDATION_JOIN_SAME_PATH",
                entity_type="join",
                entity_id=join_rule.id,
                field="right_path",
                message="Join left_path and right_path must reference different source schema paths.",
            )
        )
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


def validation_readiness(issues: list[ValidationIssue]) -> dict[str, object]:
    issue_codes = [validation_issue.code for validation_issue in issues]
    specification_blockers = [
        validation_issue.code
        for validation_issue in issues
        if validation_issue.code in SPECIFICATION_BLOCKING_ISSUE_CODES
    ]
    return {
        "specification_ready": not specification_blockers,
        "preview_executable": not issues,
        "specification_blockers": specification_blockers,
        "preview_blockers": issue_codes,
    }


def validate_duplicate_target_paths(mappings: list[IntegrationMapping]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    first_by_target_path: dict[tuple[str, str], IntegrationMapping] = {}
    for mapping in sorted(mappings, key=lambda item: (item.sequence_index, item.created_at or "")):
        key = (mapping.target_schema_document_id, mapping.target_path)
        first = first_by_target_path.get(key)
        if first is None:
            first_by_target_path[key] = mapping
            continue
        issues.append(
            issue(
                code="INTEGRATION_VALIDATION_DUPLICATE_TARGET_PATH",
                entity_type="mapping",
                entity_id=mapping.id,
                field="target_path",
                message=(
                    "target_path is already mapped by another mapping in this Integration Definition: "
                    f"{mapping.target_path}"
                ),
            )
        )
    return issues


def required_target_paths_for_definition(definition: IntegrationDefinition) -> tuple[str, ...]:
    if definition.code.upper().startswith("PS_TO_EXTERNAL_DELIVERY_NDD"):
        return NDD_EXTERNAL_DELIVERY_REQUIRED_TARGETS
    return ()


def validate_required_target_paths(
    *,
    definition: IntegrationDefinition,
    mappings: list[IntegrationMapping],
    loops: list[IntegrationLoopDefinition],
    lookups: list[IntegrationLookupDefinition],
) -> list[ValidationIssue]:
    required_paths = required_target_paths_for_definition(definition)
    if not required_paths:
        return []

    covered_paths = {mapping.target_path for mapping in mappings}
    covered_paths.update(loop.target_collection_path for loop in loops)
    covered_paths.update(lookup.output_path for lookup in lookups)

    return [
        issue(
            code="INTEGRATION_VALIDATION_REQUIRED_TARGET_MISSING",
            entity_type="definition",
            entity_id=definition.id,
            field=target_path,
            message=f"Required target path is not covered by this scenario pack: {target_path}",
        )
        for target_path in required_paths
        if target_path not in covered_paths
    ]


def collection_scope_for_path(path: str) -> str | None:
    marker = "[]"
    marker_index = path.find(marker)
    if marker_index == -1:
        return None
    return path[: marker_index + len(marker)]


def validate_lookup_output_scopes(
    *,
    lookups: list[IntegrationLookupDefinition],
    loops: list[IntegrationLoopDefinition],
) -> list[ValidationIssue]:
    loop_scopes = {
        (loop.target_schema_document_id, loop.target_collection_path)
        for loop in loops
    }
    issues: list[ValidationIssue] = []
    for lookup in lookups:
        collection_scope = collection_scope_for_path(lookup.output_path)
        if collection_scope is None:
            continue
        if (lookup.target_schema_document_id, collection_scope) in loop_scopes:
            continue
        issues.append(
            issue(
                code="INTEGRATION_VALIDATION_LOOKUP_OUTPUT_SCOPE_MISSING",
                entity_type="lookup",
                entity_id=lookup.id,
                field="output_path",
                message=(
                    "Lookup output_path targets a collection field without a matching loop "
                    f"target_collection_path: {collection_scope}"
                ),
            )
        )
    return issues


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
    issues.extend(validate_duplicate_target_paths(mappings))
    issues.extend(
        validate_required_target_paths(
            definition=definition,
            mappings=mappings,
            loops=loops,
            lookups=lookups,
        )
    )
    for loop in loops:
        issues.extend(validate_loop(db, loop))
    for join_rule in joins:
        issues.extend(validate_join(db, join_rule))
    for lookup in lookups:
        issues.extend(validate_lookup(db, lookup))
    issues.extend(validate_lookup_output_scopes(lookups=lookups, loops=loops))
    return {
        "definition_id": definition.id,
        "is_valid": not issues,
        "issue_count": len(issues),
        "issues": [serialize_issue(validation_issue) for validation_issue in issues],
        "readiness": validation_readiness(issues),
    }
