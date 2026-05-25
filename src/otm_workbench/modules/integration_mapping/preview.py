import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from sqlalchemy.orm import Session

from otm_workbench.models import (
    Artifact,
    IntegrationDefinition,
    IntegrationJoinBinding,
    IntegrationJoinBindingHop,
    IntegrationJoinRule,
    IntegrationLookupDefinition,
    IntegrationLoopDefinition,
    IntegrationMapping,
    IntegrationPayloadArtifact,
    IntegrationSchemaDocument,
    Job,
    utcnow,
)
from otm_workbench.modules.integration_mapping.mappings import parse_transform_config
from otm_workbench.modules.rates.exports import file_sha256, utc_timestamp
from otm_workbench.platform.jobs import audit_job, dumps_limited_json_object, emit_job_event


SOURCE_MODULE = "integration_mapping"
PREVIEW_JOB_TYPE = "INTEGRATION_MAPPING_PREVIEW"


def preview_counts(db: Session, definition_id: str) -> dict[str, int]:
    return {
        "mappings": db.query(IntegrationMapping).filter(IntegrationMapping.definition_id == definition_id).count(),
        "loops": db.query(IntegrationLoopDefinition).filter(IntegrationLoopDefinition.definition_id == definition_id).count(),
        "joins": db.query(IntegrationJoinRule).filter(IntegrationJoinRule.definition_id == definition_id).count(),
        "lookups": db.query(IntegrationLookupDefinition)
        .filter(IntegrationLookupDefinition.definition_id == definition_id)
        .count(),
    }


def build_preview_payload(
    *,
    definition: IntegrationDefinition,
    validation: dict[str, object],
    counts: dict[str, int],
    executable_preview: dict[str, object] | None = None,
) -> dict[str, object]:
    preview = {
        "mode": "synthetic_metadata_only",
        "external_calls_executed": False,
        "scenario": {
            "code": "planned_shipment_to_external_delivery",
            "source_object": "OTM PlannedShipment",
            "target_object": "External Delivery JSON",
            "payload_policy": "metadata_only_no_external_calls",
        },
        "entity_counts": counts,
        "sample_result": {
            "status": "generated_from_metadata",
            "records_previewed": 1,
        },
    }
    if executable_preview is not None:
        preview.update(executable_preview)
        preview["sample_result"] = {
            "status": "materialized_from_synthetic_source",
            "records_previewed": 1,
        }
    return {
        "definition_id": definition.id,
        "definition_code": definition.code,
        "preview": preview,
        "validation": validation,
    }


def source_value_from_xml_path(content: str, path: str) -> object:
    root = ET.fromstring(content)
    parts = [part for part in path.strip("/").split("/") if part]
    if not parts or parts[0] != root.tag:
        return None
    element = root
    for part in parts[1:]:
        element = element.find(part)
        if element is None:
            return None
    return (element.text or "").strip()


def xml_elements_from_collection_path(content: str, collection_path: str) -> list[ET.Element]:
    root = ET.fromstring(content)
    parts = [part for part in collection_path.strip("/").split("/") if part]
    if not parts or parts[0] != root.tag:
        return []
    parents = [root]
    for part in parts[1:-1]:
        next_parents: list[ET.Element] = []
        for parent in parents:
            next_parents.extend(parent.findall(part))
        parents = next_parents
    if len(parts) == 1:
        return [root]
    collection_name = parts[-1]
    elements: list[ET.Element] = []
    for parent in parents:
        elements.extend(parent.findall(collection_name))
    return elements


def xml_child_value(element: ET.Element, relative_path: str) -> object:
    parts = [part for part in relative_path.strip("/").split("/") if part]
    current = element
    for part in parts:
        current = current.find(part)
        if current is None:
            return None
    return (current.text or "").strip()


def set_json_path_value(target: dict[str, object], path: str, value: object) -> None:
    parts = [part for part in path.removeprefix("$.").split(".") if part]
    if not parts:
        return
    current = target
    for part in parts[:-1]:
        existing = current.get(part)
        if not isinstance(existing, dict):
            existing = {}
            current[part] = existing
        current = existing
    current[parts[-1]] = value


def json_last_path_segment(path: str) -> str:
    return path.replace("[]", "").split(".")[-1]


def set_loop_item_value(target: dict[str, object], collection_path: str, index: int, item_field: str, value: object) -> None:
    collection_name = collection_path.removeprefix("$.").removesuffix("[]")
    if not collection_name or "." in collection_name:
        return
    rows = target.setdefault(collection_name, [])
    if not isinstance(rows, list):
        return
    while len(rows) <= index:
        rows.append({})
    row = rows[index]
    if isinstance(row, dict):
        row[item_field] = value


def document_payload_content(db: Session, document_id: str) -> tuple[str, str] | None:
    document = db.get(IntegrationSchemaDocument, document_id)
    if document is None:
        return None
    payload_artifact = db.get(IntegrationPayloadArtifact, document.payload_artifact_id)
    if payload_artifact is None:
        return None
    artifact = db.get(Artifact, payload_artifact.artifact_id)
    if artifact is None:
        return None
    path = Path(artifact.file_path)
    if not path.exists() or not path.is_file():
        return None
    return document.payload_format, path.read_text(encoding="utf-8")


def mapping_value_from_source(mapping: IntegrationMapping, source_content: str) -> tuple[object | None, str | None]:
    if mapping.transform_type == "DIRECT":
        value = source_value_from_xml_path(source_content, mapping.source_path)
        return value, "copied_from_synthetic_source"
    if mapping.transform_type == "CONSTANT":
        config = parse_transform_config(mapping.transform_config_json)
        return config.get("value"), "constant_from_transform_config"
    if mapping.transform_type == "DATE_FORMAT":
        raw_value = source_value_from_xml_path(source_content, mapping.source_path)
        config = parse_transform_config(mapping.transform_config_json)
        return format_date_value(raw_value, config), "date_format_from_transform_config"
    if mapping.transform_type == "CONCAT":
        config = parse_transform_config(mapping.transform_config_json)
        return concat_value_from_config(source_content, config), "concat_from_transform_config"
    if mapping.transform_type == "FILTER_BY_QUALIFIER":
        config = parse_transform_config(mapping.transform_config_json)
        values = filtered_collection_values_from_config(source_content, config)
        return (values[0] if values else None), "filtered_by_qualifier_transform_config"
    if mapping.transform_type == "COUNT_DISTINCT":
        config = parse_transform_config(mapping.transform_config_json)
        values = filtered_collection_values_from_config(source_content, config)
        return len(set(values)), "count_distinct_from_transform_config"
    return None, None


def filtered_collection_values_from_config(source_content: str, config: dict[str, object]) -> list[str]:
    collection_path = str(config.get("collection_path") or "").strip()
    value_path = str(config.get("value_path") or "").strip()
    qualifier_path = str(config.get("qualifier_path") or "").strip()
    qualifier_value = str(config.get("qualifier_value") or "").strip()
    if not collection_path or not value_path:
        return []
    values: list[str] = []
    for element in xml_elements_from_collection_path(source_content, collection_path):
        if qualifier_path and qualifier_value:
            current_qualifier = xml_child_value(element, qualifier_path)
            if current_qualifier != qualifier_value:
                continue
        value = xml_child_value(element, value_path)
        if value in (None, ""):
            continue
        values.append(str(value))
    return values


def concat_value_from_config(source_content: str, config: dict[str, object]) -> str | None:
    parts = config.get("parts")
    if not isinstance(parts, list) or not parts:
        return None
    fragments: list[str] = []
    for part in parts:
        if not isinstance(part, dict):
            return None
        part_type = str(part.get("type") or "").strip().lower()
        if part_type == "literal":
            fragments.append(str(part.get("value") or ""))
            continue
        if part_type == "source_path":
            path = str(part.get("path") or "").strip()
            value = source_value_from_xml_path(source_content, path)
            if value in (None, ""):
                return None
            fragments.append(str(value))
            continue
        return None
    return "".join(fragments)


def format_date_value(value: object, config: dict[str, object]) -> str | None:
    if not isinstance(value, str):
        return None
    source_format = str(config.get("source_format") or "").strip().upper()
    target_format = str(config.get("target_format") or "").strip().upper()
    timezone_offset = str(config.get("timezone_offset") or "").strip()
    if source_format != "OTM_GLOGDATE" or target_format != "ISO8601":
        return None
    if not re.fullmatch(r"[+-]\d{2}:\d{2}", timezone_offset):
        return None
    if not re.fullmatch(r"\d{14}", value):
        return None
    return (
        f"{value[0:4]}-{value[4:6]}-{value[6:8]}T"
        f"{value[8:10]}:{value[10:12]}:{value[12:14]}{timezone_offset}"
    )


def build_executable_json_preview(db: Session, *, definition: IntegrationDefinition) -> dict[str, object] | None:
    joins = (
        db.query(IntegrationJoinRule)
        .filter(IntegrationJoinRule.definition_id == definition.id)
        .order_by(IntegrationJoinRule.sequence_index, IntegrationJoinRule.created_at)
        .all()
    )
    join_bindings = (
        db.query(IntegrationJoinBinding)
        .filter(IntegrationJoinBinding.definition_id == definition.id)
        .order_by(IntegrationJoinBinding.sequence_index, IntegrationJoinBinding.created_at)
        .all()
    )

    lookups = (
        db.query(IntegrationLookupDefinition)
        .filter(IntegrationLookupDefinition.definition_id == definition.id)
        .order_by(IntegrationLookupDefinition.sequence_index, IntegrationLookupDefinition.created_at)
        .all()
    )
    loops = (
        db.query(IntegrationLoopDefinition)
        .filter(IntegrationLoopDefinition.definition_id == definition.id)
        .order_by(IntegrationLoopDefinition.sequence_index, IntegrationLoopDefinition.created_at)
        .all()
    )
    mappings = (
        db.query(IntegrationMapping)
        .filter(IntegrationMapping.definition_id == definition.id)
        .order_by(IntegrationMapping.sequence_index, IntegrationMapping.created_at)
        .all()
    )
    if loops:
        return build_loop_executable_json_preview(db, loops=loops, mappings=mappings, joins=joins, lookups=lookups)
    if not mappings:
        if lookups:
            return build_lookup_executable_json_preview(db, lookups=lookups)
        return None

    target_json: dict[str, object] = {}
    field_provenance: list[dict[str, object]] = []
    join_provenance = materialize_scalar_join_guards(db, joins=joins)
    if join_provenance is None:
        return None
    if not materialize_scalar_mappings(db, mappings=mappings, target_json=target_json, field_provenance=field_provenance):
        return None
    if lookups and not materialize_scalar_lookups(
        db,
        lookups=lookups,
        target_json=target_json,
        field_provenance=field_provenance,
    ):
        return None

    preview = {
        "mode": "synthetic_executable_json",
        "target_json": target_json,
        "field_provenance": field_provenance,
    }
    if join_provenance:
        preview["join_provenance"] = join_provenance
    multi_hop_join_provenance = materialize_multi_hop_join_bindings(db, bindings=join_bindings)
    if multi_hop_join_provenance is None:
        return None
    if multi_hop_join_provenance:
        preview["multi_hop_join_provenance"] = multi_hop_join_provenance
    return preview


def materialize_scalar_join_guards(
    db: Session,
    *,
    joins: list[IntegrationJoinRule],
) -> list[dict[str, object]] | None:
    provenance: list[dict[str, object]] = []
    for join in joins:
        source_payload = document_payload_content(db, join.source_schema_document_id)
        if source_payload is None:
            return None
        source_format, source_content = source_payload
        if source_format != "XML":
            return None
        left_value = source_value_from_xml_path(source_content, join.left_path)
        right_value = source_value_from_xml_path(source_content, join.right_path)
        if left_value in (None, "") or right_value in (None, ""):
            return None
        result = evaluate_join_operator(join.operator, left_value, right_value)
        if result is None:
            return None
        if not result:
            return None
        provenance.append(
            {
                "join_id": join.id,
                "left_path": join.left_path,
                "right_path": join.right_path,
                "operator": join.operator,
                "result": result,
            }
        )
    return provenance


def evaluate_join_operator(operator: str, left_value: object, right_value: object) -> bool | None:
    if operator == "EQ":
        return left_value == right_value
    if operator == "NE":
        return left_value != right_value
    return None


def binding_hops(db: Session, binding_id: str) -> list[IntegrationJoinBindingHop]:
    return (
        db.query(IntegrationJoinBindingHop)
        .filter(IntegrationJoinBindingHop.binding_id == binding_id)
        .order_by(IntegrationJoinBindingHop.hop_sequence, IntegrationJoinBindingHop.created_at)
        .all()
    )


def materialize_multi_hop_join_bindings(
    db: Session,
    *,
    bindings: list[IntegrationJoinBinding],
) -> list[dict[str, object]] | None:
    provenance: list[dict[str, object]] = []
    for binding in bindings:
        source_payload = document_payload_content(db, binding.source_schema_document_id)
        if source_payload is None:
            return None
        source_format, source_content = source_payload
        if source_format != "XML":
            return None
        for hop in binding_hops(db, binding.id):
            left_items = xml_elements_from_collection_path(source_content, hop.left_collection_path)
            right_items = xml_elements_from_collection_path(source_content, hop.right_collection_path)
            if not left_items or not right_items:
                return None
            matched = False
            for left_index, left_item in enumerate(left_items):
                left_value = xml_child_value(left_item, hop.left_value_path)
                if left_value in (None, ""):
                    continue
                for right_index, right_item in enumerate(right_items):
                    right_value = xml_child_value(right_item, hop.right_value_path)
                    if right_value in (None, ""):
                        continue
                    result = evaluate_join_operator(hop.operator, left_value, right_value)
                    if result is None:
                        return None
                    if not result:
                        continue
                    matched = True
                    provenance.append(
                        {
                            "binding_id": binding.id,
                            "hop_sequence": hop.hop_sequence,
                            "result_alias": hop.result_alias,
                            "left_collection_path": hop.left_collection_path,
                            "right_collection_path": hop.right_collection_path,
                            "left_item_path": (
                                f"{hop.left_collection_path}[{left_index + 1}]/{hop.left_value_path}"
                            ),
                            "right_item_path": (
                                f"{hop.right_collection_path}[{right_index + 1}]/{hop.right_value_path}"
                            ),
                            "operator": hop.operator,
                            "result": result,
                        }
                    )
            if not matched:
                return None
    return provenance


def materialize_scalar_mappings(
    db: Session,
    *,
    mappings: list[IntegrationMapping],
    target_json: dict[str, object],
    field_provenance: list[dict[str, object]],
) -> bool:
    for mapping in mappings:
        if (
            mapping.transform_type
            not in {"DIRECT", "CONSTANT", "DATE_FORMAT", "CONCAT", "FILTER_BY_QUALIFIER", "COUNT_DISTINCT"}
            or "[]" in mapping.target_path
        ):
            return False
        source_payload = document_payload_content(db, mapping.source_schema_document_id)
        target_payload = document_payload_content(db, mapping.target_schema_document_id)
        if source_payload is None or target_payload is None:
            return False
        source_format, source_content = source_payload
        target_format, _target_content = target_payload
        if source_format != "XML" or target_format != "JSON":
            return False
        value, value_policy = mapping_value_from_source(mapping, source_content)
        if value in (None, ""):
            return False
        set_json_path_value(target_json, mapping.target_path, value)
        field_provenance.append(
            {
                "mapping_id": mapping.id,
                "source_path": mapping.source_path,
                "target_path": mapping.target_path,
                "transform_type": mapping.transform_type,
                "value_policy": value_policy,
            }
        )
    return bool(field_provenance)


def materialize_scalar_lookups(
    db: Session,
    *,
    lookups: list[IntegrationLookupDefinition],
    target_json: dict[str, object],
    field_provenance: list[dict[str, object]],
) -> bool:
    for lookup in lookups:
        provenance = materialize_scalar_lookup(db, lookup=lookup, target_json=target_json)
        if provenance is None:
            return False
        field_provenance.append(provenance)
    return True


def build_lookup_executable_json_preview(
    db: Session,
    *,
    lookups: list[IntegrationLookupDefinition],
) -> dict[str, object] | None:
    target_json: dict[str, object] = {}
    field_provenance: list[dict[str, object]] = []
    if not materialize_scalar_lookups(
        db,
        lookups=lookups,
        target_json=target_json,
        field_provenance=field_provenance,
    ):
        return None
    return {
        "mode": "synthetic_executable_json",
        "target_json": target_json,
        "field_provenance": field_provenance,
    }


def materialize_scalar_lookup(
    db: Session,
    *,
    lookup: IntegrationLookupDefinition,
    target_json: dict[str, object],
) -> dict[str, object] | None:
    if lookup.lookup_type != "MOCK" or "[]" in lookup.output_path:
        return None
    source_payload = document_payload_content(db, lookup.source_schema_document_id)
    target_payload = document_payload_content(db, lookup.target_schema_document_id)
    if source_payload is None or target_payload is None:
        return None
    source_format, source_content = source_payload
    target_format, _target_content = target_payload
    if source_format != "XML" or target_format != "JSON":
        return None
    input_value = source_value_from_xml_path(source_content, lookup.input_path)
    if input_value in (None, ""):
        return None
    try:
        response = json.loads(lookup.mock_response_json or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(response, dict):
        return None
    value = response.get(json_last_path_segment(lookup.output_path))
    if value in (None, ""):
        return None
    set_json_path_value(target_json, lookup.output_path, value)
    return {
        "lookup_id": lookup.id,
        "input_path": lookup.input_path,
        "output_path": lookup.output_path,
        "lookup_type": lookup.lookup_type,
        "value_policy": "mock_lookup_response",
    }


def build_loop_executable_json_preview(
    db: Session,
    *,
    loops: list[IntegrationLoopDefinition],
    mappings: list[IntegrationMapping],
    joins: list[IntegrationJoinRule],
    lookups: list[IntegrationLookupDefinition],
) -> dict[str, object] | None:
    if len(loops) != 1:
        return None
    loop = loops[0]
    source_payload = document_payload_content(db, loop.source_schema_document_id)
    target_payload = document_payload_content(db, loop.target_schema_document_id)
    if source_payload is None or target_payload is None:
        return None
    source_format, source_content = source_payload
    target_format, _target_content = target_payload
    if source_format != "XML" or target_format != "JSON":
        return None

    loop_items = xml_elements_from_collection_path(source_content, loop.source_collection_path)
    if not loop_items:
        return None
    eligible_loop_items, join_provenance = materialize_loop_join_guards(loop=loop, joins=joins, loop_items=loop_items)
    if eligible_loop_items is None:
        return None

    target_json: dict[str, object] = {}
    field_provenance: list[dict[str, object]] = []
    for mapping in mappings:
        if mapping.transform_type not in {"DIRECT", "CONSTANT"}:
            return None
        if not mapping.source_path.startswith(f"{loop.source_collection_path}/"):
            return None
        if not mapping.target_path.startswith(f"{loop.target_collection_path}."):
            return None
        relative_source_path = mapping.source_path.removeprefix(f"{loop.source_collection_path}/")
        target_field = mapping.target_path.removeprefix(f"{loop.target_collection_path}.")
        if not target_field or "." in target_field or "[]" in target_field:
            return None
        for target_index, (source_index, item) in enumerate(eligible_loop_items):
            if mapping.transform_type == "CONSTANT":
                config = parse_transform_config(mapping.transform_config_json)
                value = config.get("value")
                value_policy = "constant_from_transform_config"
            else:
                value = xml_child_value(item, relative_source_path)
                value_policy = "copied_from_synthetic_loop_item"
            if value in (None, ""):
                continue
            set_loop_item_value(target_json, loop.target_collection_path, target_index, target_field, value)
            field_provenance.append(
                {
                    "loop_id": loop.id,
                    "mapping_id": mapping.id,
                    "source_path": mapping.source_path,
                    "source_item_path": (
                        f"{loop.source_collection_path}[{source_index + 1}]/{relative_source_path}"
                    ),
                    "target_path": mapping.target_path,
                    "target_item_path": loop.target_collection_path.replace("[]", f"[{target_index}]")
                    + f".{target_field}",
                    "transform_type": mapping.transform_type,
                    "value_policy": value_policy,
                }
            )

    for lookup in lookups:
        if lookup.lookup_type != "MOCK":
            return None
        if not lookup.input_path.startswith(f"{loop.source_collection_path}/"):
            return None
        if not lookup.output_path.startswith(f"{loop.target_collection_path}."):
            return None
        relative_input_path = lookup.input_path.removeprefix(f"{loop.source_collection_path}/")
        target_field = lookup.output_path.removeprefix(f"{loop.target_collection_path}.")
        if not target_field or "." in target_field or "[]" in target_field:
            return None
        try:
            response = json.loads(lookup.mock_response_json or "{}")
        except json.JSONDecodeError:
            return None
        if not isinstance(response, dict):
            return None
        value = response.get(target_field)
        if value in (None, ""):
            return None
        for target_index, (source_index, item) in enumerate(eligible_loop_items):
            input_value = xml_child_value(item, relative_input_path)
            if input_value in (None, ""):
                continue
            set_loop_item_value(target_json, loop.target_collection_path, target_index, target_field, value)
            field_provenance.append(
                {
                    "loop_id": loop.id,
                    "lookup_id": lookup.id,
                    "input_path": lookup.input_path,
                    "source_item_path": f"{loop.source_collection_path}[{source_index + 1}]/{relative_input_path}",
                    "output_path": lookup.output_path,
                    "target_item_path": loop.target_collection_path.replace("[]", f"[{target_index}]")
                    + f".{target_field}",
                    "lookup_type": lookup.lookup_type,
                    "value_policy": "mock_lookup_response",
                }
            )

    if not field_provenance:
        return None
    preview = {
        "mode": "synthetic_executable_json",
        "target_json": target_json,
        "field_provenance": field_provenance,
    }
    if join_provenance:
        preview["join_provenance"] = join_provenance
    return preview


def materialize_loop_join_guards(
    *,
    loop: IntegrationLoopDefinition,
    joins: list[IntegrationJoinRule],
    loop_items: list[ET.Element],
) -> tuple[list[tuple[int, ET.Element]], list[dict[str, object]]] | tuple[None, None]:
    if not joins:
        return list(enumerate(loop_items)), []

    relative_joins: list[tuple[IntegrationJoinRule, str, str]] = []
    for join in joins:
        if join.source_schema_document_id != loop.source_schema_document_id:
            return None, None
        if not join.left_path.startswith(f"{loop.source_collection_path}/"):
            return None, None
        if not join.right_path.startswith(f"{loop.source_collection_path}/"):
            return None, None
        relative_joins.append(
            (
                join,
                join.left_path.removeprefix(f"{loop.source_collection_path}/"),
                join.right_path.removeprefix(f"{loop.source_collection_path}/"),
            )
        )

    eligible_items: list[tuple[int, ET.Element]] = []
    provenance: list[dict[str, object]] = []
    for index, item in enumerate(loop_items):
        item_allowed = True
        for join, left_relative_path, right_relative_path in relative_joins:
            left_value = xml_child_value(item, left_relative_path)
            right_value = xml_child_value(item, right_relative_path)
            if left_value in (None, "") or right_value in (None, ""):
                return None, None
            result = evaluate_join_operator(join.operator, left_value, right_value)
            if result is None:
                return None, None
            provenance.append(
                {
                    "loop_id": loop.id,
                    "join_id": join.id,
                    "left_path": join.left_path,
                    "right_path": join.right_path,
                    "left_item_path": f"{loop.source_collection_path}[{index + 1}]/{left_relative_path}",
                    "right_item_path": f"{loop.source_collection_path}[{index + 1}]/{right_relative_path}",
                    "operator": join.operator,
                    "result": result,
                }
            )
            if not result:
                item_allowed = False
        if item_allowed:
            eligible_items.append((index, item))

    if not eligible_items:
        return None, None
    return eligible_items, provenance


def create_preview_artifact(
    db: Session,
    *,
    definition: IntegrationDefinition,
    artifact_root: Path,
    payload: dict[str, object],
) -> Artifact:
    export_dir = artifact_root / "integration_mapping" / definition.id / "previews" / utc_timestamp()
    export_dir.mkdir(parents=True, exist_ok=True)
    file_name = "integration_preview.json"
    file_path = export_dir / file_name
    file_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    digest, size = file_sha256(file_path)
    artifact = Artifact(
        source_module=SOURCE_MODULE,
        artifact_type="integration_preview",
        file_path=str(file_path),
        file_name=file_name,
        content_type="application/json",
        sha256=digest,
        size_bytes=size,
        sensitivity_level="internal",
    )
    db.add(artifact)
    db.flush()
    return artifact


def record_completed_preview_job(
    db: Session,
    *,
    definition: IntegrationDefinition,
    artifact: Artifact,
    result_payload: dict[str, object],
    created_by: str,
) -> Job:
    job = Job(
        job_type=PREVIEW_JOB_TYPE,
        source_module=SOURCE_MODULE,
        status="PENDING",
        progress=0,
        message="Job created.",
        input_json=dumps_limited_json_object({"definition_id": definition.id}, label="input"),
        result_json="{}",
        error_details_json="{}",
        created_by=created_by,
    )
    db.add(job)
    db.flush()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_CREATED",
        status_before=None,
        status_after="PENDING",
        message="Job created.",
        created_by=created_by,
    )
    audit_job(db, actor=created_by, action="job.create", job=job)
    db.flush()

    job.status = "RUNNING"
    job.progress = 1
    job.message = "Job started."
    job.started_at = utcnow()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_STARTED",
        status_before="PENDING",
        status_after="RUNNING",
        message="Job started.",
        created_by=created_by,
    )
    db.flush()

    job.status = "SUCCEEDED"
    job.progress = 100
    job.message = "Integration Mapping preview generated."
    job.result_json = dumps_limited_json_object(
        {
            "definition_id": definition.id,
            "artifact_id": artifact.id,
            "preview": result_payload["preview"],
            "validation": result_payload["validation"],
        },
        label="result",
    )
    job.finished_at = utcnow()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_SUCCEEDED",
        status_before="RUNNING",
        status_after="SUCCEEDED",
        message="Integration Mapping preview generated.",
        created_by=created_by,
        payload={"artifact_id": artifact.id},
    )
    audit_job(db, actor=created_by, action="job.succeed", job=job, metadata={"artifact_id": artifact.id})
    db.flush()
    return job


def build_integration_preview(
    db: Session,
    *,
    definition: IntegrationDefinition,
    validation: dict[str, object],
    artifact_root: Path,
    created_by: str,
) -> dict[str, object]:
    counts = preview_counts(db, definition.id)
    executable_preview = build_executable_json_preview(db, definition=definition)
    preview_payload = build_preview_payload(
        definition=definition,
        validation=validation,
        counts=counts,
        executable_preview=executable_preview,
    )
    artifact = create_preview_artifact(db, definition=definition, artifact_root=artifact_root, payload=preview_payload)
    job = record_completed_preview_job(
        db,
        definition=definition,
        artifact=artifact,
        result_payload=preview_payload,
        created_by=created_by,
    )
    db.commit()
    db.refresh(job)
    db.refresh(artifact)
    return {
        "definition_id": definition.id,
        "status": job.status,
        "job_id": job.id,
        "artifact_id": artifact.id,
        "preview": preview_payload["preview"],
        "validation": validation,
    }
