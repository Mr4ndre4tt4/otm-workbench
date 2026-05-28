import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import (
    Artifact,
    AuditLog,
    CsvutilBuild,
    CutoverChecklist,
    CutoverChecklistItem,
    DomainEvent,
    Evidence,
    LoadPlanPackage,
    Manifest,
    utcnow,
)
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object
from otm_workbench.modules.rates.exports import file_sha256, iso_now, utc_timestamp


DEFAULT_PARAMETER_SET = {
    "mode": "INSERT",
    "delimiter": "COMMA",
    "encoding": "UTF-8",
    "date_format": "YYYY-MM-DD HH24:MI:SS",
}
ALLOWED_CSVUTIL_MODES = {"INSERT", "UPDATE", "INSERT_UPDATE"}
ALLOWED_DELIMITERS = {"COMMA", "PIPE", "SEMICOLON", "TAB"}
ALLOWED_ENCODINGS = {"UTF-8"}


def normalize_parameter_set(parameter_set: dict[str, object] | None = None) -> dict[str, str]:
    normalized = dict(DEFAULT_PARAMETER_SET)
    if parameter_set:
        for key, value in parameter_set.items():
            if key not in DEFAULT_PARAMETER_SET:
                raise ValueError(f"Unsupported CSVUTIL parameter: {key}.")
            normalized[key] = str(value).strip().upper() if key != "date_format" else str(value).strip()
    if normalized["mode"] not in ALLOWED_CSVUTIL_MODES:
        raise ValueError("Invalid CSVUTIL mode.")
    if normalized["delimiter"] not in ALLOWED_DELIMITERS:
        raise ValueError("Invalid CSVUTIL delimiter.")
    if normalized["encoding"] not in ALLOWED_ENCODINGS:
        raise ValueError("Invalid CSVUTIL encoding.")
    if not normalized["date_format"]:
        raise ValueError("Invalid CSVUTIL date_format.")
    return normalized


def normalize_table_overrides(
    table_overrides: dict[str, object] | None,
    load_sequence: list[dict[str, object]],
) -> dict[str, dict[str, str]]:
    if not table_overrides:
        return {}
    selected_tables = {str(item["table_name"]).upper() for item in load_sequence}
    normalized: dict[str, dict[str, str]] = {}
    for table_name, raw_override in table_overrides.items():
        normalized_table = str(table_name).strip().upper()
        if normalized_table not in selected_tables:
            raise ValueError(f"CSVUTIL table override references a table that is not selected: {normalized_table}.")
        if not isinstance(raw_override, dict):
            raise ValueError("CSVUTIL table override must be an object.")
        item_override: dict[str, str] = {}
        for key, value in raw_override.items():
            if key not in {"mode", "delimiter"}:
                raise ValueError(f"Unsupported CSVUTIL table override parameter: {key}.")
            normalized_value = str(value).strip().upper()
            if key == "mode" and normalized_value not in ALLOWED_CSVUTIL_MODES:
                raise ValueError("Invalid CSVUTIL table override mode.")
            if key == "delimiter" and normalized_value not in ALLOWED_DELIMITERS:
                raise ValueError("Invalid CSVUTIL table override delimiter.")
            item_override[key] = normalized_value
        normalized[normalized_table] = item_override
    return dict(sorted(normalized.items()))


def csv_relative_name(index: int, table_name: str) -> str:
    return f"csv/{index:03d}_{table_name}.csv"


def build_ctl_text(
    package: LoadPlanPackage,
    load_sequence: list[dict[str, object]],
    parameter_set: dict[str, str],
    table_overrides: dict[str, dict[str, str]] | None = None,
) -> str:
    lines = [
        "# OTM Workbench CSVUTIL CTL",
        f"# package_id={package.id}",
        f"# source_module={package.source_module}",
        f"# csvutil_mode={parameter_set['mode']}",
        f"# delimiter={parameter_set['delimiter']}",
        f"# encoding={parameter_set['encoding']}",
        f"# date_format={parameter_set['date_format']}",
    ]
    for table_name, override in (table_overrides or {}).items():
        mode = override.get("mode", parameter_set["mode"])
        delimiter = override.get("delimiter", parameter_set["delimiter"])
        lines.append(f"# table_override {table_name} mode={mode} delimiter={delimiter}")
    for index, item in enumerate(load_sequence, start=1):
        table_name = str(item["table_name"])
        lines.append(f"{index:03d},{table_name},{csv_relative_name(index, table_name)}")
    return "\n".join(lines) + "\n"


def build_cl_text(
    package: LoadPlanPackage,
    load_sequence: list[dict[str, object]],
    parameter_set: dict[str, str],
    table_overrides: dict[str, dict[str, str]] | None = None,
) -> str:
    lines = [
        "# OTM Workbench CSVUTIL CL",
        f"# package_id={package.id}",
        f"SET MODE {parameter_set['mode']}",
        f"SET DELIMITER {parameter_set['delimiter']}",
        f"SET ENCODING {parameter_set['encoding']}",
        f"SET DATE_FORMAT {parameter_set['date_format']}",
    ]
    for index, item in enumerate(load_sequence, start=1):
        table_name = str(item["table_name"])
        override = (table_overrides or {}).get(table_name.upper(), {})
        mode = override.get("mode", parameter_set["mode"])
        delimiter = override.get("delimiter", parameter_set["delimiter"])
        lines.append(f"LOAD {table_name} FROM {csv_relative_name(index, table_name)} MODE {mode} DELIMITER {delimiter}")
    return "\n".join(lines) + "\n"


def serialize_csvutil_build(build: CsvutilBuild) -> dict[str, object]:
    return {
        "id": build.id,
        "project_id": build.project_id,
        "environment_id": build.environment_id,
        "profile_id": build.profile_id,
        "package_id": build.package_id,
        "status": build.status,
        "ctl_artifact_id": build.ctl_artifact_id,
        "cl_artifact_id": build.cl_artifact_id,
        "manifest_id": build.manifest_id,
        "evidence_id": build.evidence_id,
        "summary": parse_json_object(build.summary_json),
        "created_by": build.created_by,
        "built_at": build.built_at.isoformat() if build.built_at else None,
    }


def ensure_buildable_package(package: LoadPlanPackage) -> list[dict[str, object]]:
    if package.status != "REGISTERED":
        raise ValueError("Load Plan package must be REGISTERED before CSVUTIL build.")
    if not package.artifact_id or not package.manifest_id:
        raise ValueError("Load Plan package must reference source artifact and manifest before CSVUTIL build.")
    load_sequence = parse_json_list(package.load_sequence_json)
    if not load_sequence:
        raise ValueError("Load Plan package must have a load sequence before CSVUTIL build.")
    row_count = sum(int(item.get("row_count", 0)) for item in load_sequence)
    if row_count == 0:
        raise ValueError("Load Plan package must have rows before CSVUTIL build.")
    return load_sequence


def catalog_context_for_package(package: LoadPlanPackage) -> dict[str, object]:
    summary = parse_json_object(package.summary_json)
    return {
        key: summary[key]
        for key in ("catalog_macro_object_code", "catalog_load_plan_path")
        if summary.get(key)
    }


def domain_name_for_package(package: LoadPlanPackage) -> str | None:
    summary = parse_json_object(package.summary_json)
    domain_name = summary.get("domain_name")
    return str(domain_name).strip().upper() if domain_name else None


def create_artifact(
    db: Session,
    *,
    package: LoadPlanPackage,
    artifact_type: str,
    path: Path,
) -> Artifact:
    digest, size = file_sha256(path)
    artifact = Artifact(
        project_id=package.project_id,
        profile_id=package.profile_id,
        environment_id=package.environment_id,
        domain_name=domain_name_for_package(package),
        visibility="PROJECT",
        source_module="load_plan",
        artifact_type=artifact_type,
        file_path=str(path),
        file_name=path.name,
        content_type="text/plain",
        sha256=digest,
        size_bytes=size,
        sensitivity_level="internal",
    )
    db.add(artifact)
    db.flush()
    return artifact


def generate_csvutil_build_with_sequence(
    db: Session,
    *,
    package: LoadPlanPackage,
    artifact_root: Path,
    built_by: str,
    load_sequence: list[dict[str, object]],
    source_entity_type: str = "load_plan_package",
    source_entity_id: str | None = None,
    checklist_id: str | None = None,
    parameter_set: dict[str, object] | None = None,
    table_overrides: dict[str, object] | None = None,
) -> CsvutilBuild:
    normalized_parameter_set = normalize_parameter_set(parameter_set)
    normalized_table_overrides = normalize_table_overrides(table_overrides, load_sequence)
    timestamp = utc_timestamp()
    build_dir = artifact_root / "load_plan" / package.id / "csvutil" / timestamp
    build_dir.mkdir(parents=True, exist_ok=True)
    ctl_path = build_dir / f"csvutil_{package.id}.ctl"
    cl_path = build_dir / f"csvutil_{package.id}.cl"
    ctl_path.write_text(
        build_ctl_text(package, load_sequence, normalized_parameter_set, normalized_table_overrides),
        encoding="utf-8",
    )
    cl_path.write_text(
        build_cl_text(package, load_sequence, normalized_parameter_set, normalized_table_overrides),
        encoding="utf-8",
    )

    ctl_artifact = create_artifact(db, package=package, artifact_type="csvutil_ctl", path=ctl_path)
    cl_artifact = create_artifact(db, package=package, artifact_type="csvutil_cl", path=cl_path)
    built_at = iso_now()
    catalog_context = catalog_context_for_package(package)
    files = [
        {
            "artifact_type": ctl_artifact.artifact_type,
            "file_name": ctl_artifact.file_name,
            "sha256": ctl_artifact.sha256,
            "size_bytes": ctl_artifact.size_bytes,
        },
        {
            "artifact_type": cl_artifact.artifact_type,
            "file_name": cl_artifact.file_name,
            "sha256": cl_artifact.sha256,
            "size_bytes": cl_artifact.size_bytes,
        },
    ]
    manifest_payload = {
        "schema_version": "load-plan-csvutil-build-manifest/v1",
        "manifest_type": "csvutil_build",
        "source_module": "load_plan",
        "source_entity_type": source_entity_type,
        "source_entity_id": source_entity_id or package.id,
        "package": {
            "id": package.id,
            "source_module": package.source_module,
            "source_entity_id": package.source_entity_id,
            "package_type": package.package_type,
            **catalog_context,
        },
        "files": files,
        "load_sequence": load_sequence,
        "parameter_set": normalized_parameter_set,
        "table_overrides": normalized_table_overrides,
        "built_at": built_at,
        "built_by": built_by,
    }
    if checklist_id:
        manifest_payload["checklist_id"] = checklist_id
    manifest = Manifest(
        project_id=package.project_id,
        profile_id=package.profile_id,
        environment_id=package.environment_id,
        domain_name=domain_name_for_package(package),
        visibility="PROJECT",
        source_module="load_plan",
        status="CREATED",
        manifest_json=json.dumps(manifest_payload, indent=2, sort_keys=True),
    )
    db.add(manifest)
    db.flush()

    summary = {
        "package_id": package.id,
        "source_entity_type": source_entity_type,
        "source_entity_id": source_entity_id or package.id,
        "source_module": package.source_module,
        "source_package_entity_type": package.source_entity_type,
        "source_package_entity_id": package.source_entity_id,
        "package_type": package.package_type,
        "table_count": len(load_sequence),
        "row_count": sum(int(item.get("row_count", 0)) for item in load_sequence),
        "ctl_artifact_type": "csvutil_ctl",
        "cl_artifact_type": "csvutil_cl",
        "parameter_set": normalized_parameter_set,
        "table_overrides": normalized_table_overrides,
        **catalog_context,
    }
    if checklist_id:
        summary["checklist_id"] = checklist_id
        summary["selected_item_count"] = len(load_sequence)
    build = CsvutilBuild(
        project_id=package.project_id,
        environment_id=package.environment_id,
        profile_id=package.profile_id,
        package_id=package.id,
        status="BUILT",
        ctl_artifact_id=ctl_artifact.id,
        cl_artifact_id=cl_artifact.id,
        manifest_id=manifest.id,
        summary_json=json.dumps(summary, sort_keys=True),
        created_by=built_by,
        built_at=utcnow(),
    )
    db.add(build)
    db.flush()

    evidence_summary = {
        "source_entity_type": "csvutil_build",
        "source_entity_id": build.id,
        "package_id": package.id,
        "csvutil_source_entity_type": source_entity_type,
        "csvutil_source_entity_id": source_entity_id or package.id,
        "source_package_type": package.package_type,
        "table_count": summary["table_count"],
        "row_count": summary["row_count"],
        "ctl_artifact_id": ctl_artifact.id,
        "cl_artifact_id": cl_artifact.id,
        "manifest_id": manifest.id,
        "status": "BUILT",
        "parameter_set": normalized_parameter_set,
        "table_overrides": normalized_table_overrides,
        **catalog_context,
    }
    if checklist_id:
        evidence_summary["checklist_id"] = checklist_id
    evidence = Evidence(
        project_id=package.project_id,
        profile_id=package.profile_id,
        environment_id=package.environment_id,
        domain_name=domain_name_for_package(package),
        visibility="PROJECT",
        source_module="load_plan",
        evidence_type="csvutil_build",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        artifact_id=ctl_artifact.id,
        manifest_id=manifest.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    build.evidence_id = evidence.id
    db.add(
        AuditLog(
            actor_user_id=built_by,
            action="load_plan.csvutil.build",
            target_type="csvutil_build",
            target_id=build.id,
            metadata_json=json.dumps(
                {
                    "package_id": package.id,
                    "source_entity_type": source_entity_type,
                    "source_entity_id": source_entity_id or package.id,
                    "ctl_artifact_id": ctl_artifact.id,
                    "cl_artifact_id": cl_artifact.id,
                    "manifest_id": manifest.id,
                    "evidence_id": evidence.id,
                    "parameter_set": normalized_parameter_set,
                    "table_overrides": normalized_table_overrides,
                    **({"checklist_id": checklist_id} if checklist_id else {}),
                    **catalog_context,
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.csvutil.built",
            source_module="load_plan",
            project_id=package.project_id,
            aggregate_type="csvutil_build",
            aggregate_id=build.id,
            payload_json=json.dumps(
                {
                    "package_id": package.id,
                    "status": "BUILT",
                    "source_entity_type": source_entity_type,
                    "source_entity_id": source_entity_id or package.id,
                    "parameter_set": normalized_parameter_set,
                    "table_overrides": normalized_table_overrides,
                    **({"checklist_id": checklist_id} if checklist_id else {}),
                    **catalog_context,
                },
                sort_keys=True,
            ),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(build)
    return build


def generate_csvutil_build(
    db: Session,
    *,
    package: LoadPlanPackage,
    artifact_root: Path,
    built_by: str,
    parameter_set: dict[str, object] | None = None,
    table_overrides: dict[str, object] | None = None,
) -> CsvutilBuild:
    load_sequence = ensure_buildable_package(package)
    return generate_csvutil_build_with_sequence(
        db,
        package=package,
        artifact_root=artifact_root,
        built_by=built_by,
        load_sequence=load_sequence,
        parameter_set=parameter_set,
        table_overrides=table_overrides,
    )


def checklist_csvutil_sequence(db: Session, checklist: CutoverChecklist) -> list[dict[str, object]]:
    items = (
        db.query(CutoverChecklistItem)
        .filter(CutoverChecklistItem.checklist_id == checklist.id)
        .filter(CutoverChecklistItem.item_code == "TABLE_READY")
        .filter(CutoverChecklistItem.status == "DONE")
        .filter(CutoverChecklistItem.method == "CSVUTIL")
        .order_by(CutoverChecklistItem.sort_order, CutoverChecklistItem.created_at)
        .all()
    )
    sequence: list[dict[str, object]] = []
    for index, item in enumerate(items, start=1):
        details = parse_json_object(item.details_json)
        if not item.table_name:
            continue
        sequence.append(
            {
                "position": index,
                "table_name": item.table_name,
                "row_count": int(details.get("row_count") or 0),
                "requirement_level": details.get("requirement_level") or "REQUIRED",
                "checklist_item_id": item.id,
            }
        )
    return sequence


def generate_csvutil_build_from_checklist(
    db: Session,
    *,
    checklist: CutoverChecklist,
    package: LoadPlanPackage,
    artifact_root: Path,
    built_by: str,
    parameter_set: dict[str, object] | None = None,
    table_overrides: dict[str, object] | None = None,
) -> CsvutilBuild:
    ensure_buildable_package(package)
    load_sequence = checklist_csvutil_sequence(db, checklist)
    if not load_sequence:
        raise ValueError("Cutover checklist has no eligible DONE CSVUTIL items.")
    return generate_csvutil_build_with_sequence(
        db,
        package=package,
        artifact_root=artifact_root,
        built_by=built_by,
        load_sequence=load_sequence,
        source_entity_type="cutover_checklist",
        source_entity_id=checklist.id,
        checklist_id=checklist.id,
        parameter_set=parameter_set,
        table_overrides=table_overrides,
    )
