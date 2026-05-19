import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import (
    Artifact,
    AuditLog,
    CsvutilBuild,
    DomainEvent,
    Evidence,
    LoadPlanPackage,
    Manifest,
    utcnow,
)
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object
from otm_workbench.modules.rates.exports import file_sha256, iso_now, utc_timestamp


def csv_relative_name(index: int, table_name: str) -> str:
    return f"csv/{index:03d}_{table_name}.csv"


def build_ctl_text(package: LoadPlanPackage, load_sequence: list[dict[str, object]]) -> str:
    lines = [
        "# OTM Workbench CSVUTIL CTL",
        f"# package_id={package.id}",
        f"# source_module={package.source_module}",
    ]
    for index, item in enumerate(load_sequence, start=1):
        table_name = str(item["table_name"])
        lines.append(f"{index:03d},{table_name},{csv_relative_name(index, table_name)}")
    return "\n".join(lines) + "\n"


def build_cl_text(package: LoadPlanPackage, load_sequence: list[dict[str, object]]) -> str:
    lines = [
        "# OTM Workbench CSVUTIL CL",
        f"# package_id={package.id}",
    ]
    for index, item in enumerate(load_sequence, start=1):
        table_name = str(item["table_name"])
        lines.append(f"LOAD {table_name} FROM {csv_relative_name(index, table_name)}")
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


def generate_csvutil_build(
    db: Session,
    *,
    package: LoadPlanPackage,
    artifact_root: Path,
    built_by: str,
) -> CsvutilBuild:
    load_sequence = ensure_buildable_package(package)
    timestamp = utc_timestamp()
    build_dir = artifact_root / "load_plan" / package.id / "csvutil" / timestamp
    build_dir.mkdir(parents=True, exist_ok=True)
    ctl_path = build_dir / f"csvutil_{package.id}.ctl"
    cl_path = build_dir / f"csvutil_{package.id}.cl"
    ctl_path.write_text(build_ctl_text(package, load_sequence), encoding="utf-8")
    cl_path.write_text(build_cl_text(package, load_sequence), encoding="utf-8")

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
        "source_entity_type": "load_plan_package",
        "source_entity_id": package.id,
        "package": {
            "id": package.id,
            "source_module": package.source_module,
            "source_entity_id": package.source_entity_id,
            "package_type": package.package_type,
            **catalog_context,
        },
        "files": files,
        "load_sequence": load_sequence,
        "built_at": built_at,
        "built_by": built_by,
    }
    manifest = Manifest(
        project_id=package.project_id,
        source_module="load_plan",
        status="CREATED",
        manifest_json=json.dumps(manifest_payload, indent=2, sort_keys=True),
    )
    db.add(manifest)
    db.flush()

    summary = {
        "package_id": package.id,
        "source_module": package.source_module,
        "source_entity_type": package.source_entity_type,
        "source_entity_id": package.source_entity_id,
        "package_type": package.package_type,
        "table_count": len(load_sequence),
        "row_count": sum(int(item.get("row_count", 0)) for item in load_sequence),
        "ctl_artifact_type": "csvutil_ctl",
        "cl_artifact_type": "csvutil_cl",
        **catalog_context,
    }
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
        "source_package_type": package.package_type,
        "table_count": summary["table_count"],
        "row_count": summary["row_count"],
        "ctl_artifact_id": ctl_artifact.id,
        "cl_artifact_id": cl_artifact.id,
        "manifest_id": manifest.id,
        "status": "BUILT",
        **catalog_context,
    }
    evidence = Evidence(
        project_id=package.project_id,
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
                    "ctl_artifact_id": ctl_artifact.id,
                    "cl_artifact_id": cl_artifact.id,
                    "manifest_id": manifest.id,
                    "evidence_id": evidence.id,
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
            payload_json=json.dumps({"package_id": package.id, "status": "BUILT", **catalog_context}, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(build)
    return build
