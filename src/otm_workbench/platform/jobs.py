import json
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from otm_workbench.models import AuditLog, Job, JobEvent, utcnow


TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "CANCELLED"}


@dataclass(frozen=True)
class JobRunResult:
    result: dict[str, object]
    message: str = "Job completed."


JobHandler = Callable[[dict[str, object]], JobRunResult]


def demo_echo_handler(input_payload: dict[str, object]) -> JobRunResult:
    return JobRunResult(result={"echo": input_payload}, message="Demo job completed.")


JOB_HANDLERS: dict[str, JobHandler] = {
    "DEMO_ECHO": demo_echo_handler,
}


def parse_json_object(raw: str | None) -> dict[str, object]:
    if not raw:
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Job JSON payload must be an object.")
    return payload


def emit_job_event(
    db: Session,
    *,
    job: Job,
    event_type: str,
    status_before: str | None,
    status_after: str | None,
    message: str,
    created_by: str | None,
    payload: dict[str, object] | None = None,
) -> None:
    event_payload = {
        "job_id": job.id,
        "job_type": job.job_type,
        "source_module": job.source_module,
        "project_id": job.project_id,
        "profile_id": job.profile_id,
        "environment_id": job.environment_id,
        "domain_name": job.domain_name,
        **(payload or {}),
    }
    db.add(
        JobEvent(
            job_id=job.id,
            event_type=event_type,
            status_before=status_before,
            status_after=status_after,
            message=message,
            payload_json=json.dumps(event_payload, sort_keys=True),
            created_by=created_by,
        )
    )


def audit_job(db: Session, *, actor: str | None, action: str, job: Job, metadata: dict[str, object] | None = None) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor,
            action=action,
            target_type="job",
            target_id=job.id,
            metadata_json=json.dumps(
                {
                    "job_id": job.id,
                    "job_type": job.job_type,
                    "source_module": job.source_module,
                    "project_id": job.project_id,
                    "profile_id": job.profile_id,
                    "environment_id": job.environment_id,
                    "domain_name": job.domain_name,
                    **(metadata or {}),
                },
                sort_keys=True,
            ),
        )
    )


def serialize_job(job: Job) -> dict[str, object]:
    return {
        "id": job.id,
        "job_type": job.job_type,
        "source_module": job.source_module,
        "project_id": job.project_id,
        "profile_id": job.profile_id,
        "environment_id": job.environment_id,
        "domain_name": job.domain_name,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "input": parse_json_object(job.input_json),
        "result": parse_json_object(job.result_json),
        "error": (
            {
                "code": job.error_code,
                "message": job.error_message,
                "details": parse_json_object(job.error_details_json),
            }
            if job.error_code or job.error_message
            else None
        ),
        "created_by": job.created_by,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "cancelled_at": job.cancelled_at.isoformat() if job.cancelled_at else None,
    }


def serialize_job_event(event: JobEvent) -> dict[str, object]:
    return {
        "id": event.id,
        "job_id": event.job_id,
        "event_type": event.event_type,
        "status_before": event.status_before,
        "status_after": event.status_after,
        "message": event.message,
        "payload": parse_json_object(event.payload_json),
        "created_by": event.created_by,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


def create_job(
    db: Session,
    *,
    job_type: str,
    source_module: str,
    input_payload: dict[str, object],
    created_by: str,
    project_id: str | None = None,
    profile_id: str | None = None,
    environment_id: str | None = None,
    domain_name: str | None = None,
    execute_now: bool = False,
) -> Job:
    job = Job(
        job_type=job_type.upper(),
        source_module=source_module,
        project_id=project_id,
        profile_id=profile_id,
        environment_id=environment_id,
        domain_name=domain_name.upper() if domain_name else None,
        status="PENDING",
        progress=0,
        message="Job created.",
        input_json=json.dumps(input_payload, sort_keys=True),
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
    if execute_now:
        run_job_now(db, job=job, actor=created_by)
    db.commit()
    db.refresh(job)
    return job


def run_job_now(db: Session, *, job: Job, actor: str) -> None:
    status_before = job.status
    job.status = "RUNNING"
    job.progress = 1
    job.message = "Job started."
    job.started_at = utcnow()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_STARTED",
        status_before=status_before,
        status_after="RUNNING",
        message="Job started.",
        created_by=actor,
    )
    handler = JOB_HANDLERS.get(job.job_type)
    if handler is None:
        job.status = "FAILED"
        job.progress = 100
        job.message = "Job failed."
        job.error_code = "JOB_HANDLER_NOT_REGISTERED"
        job.error_message = "No handler is registered for this job type."
        job.error_details_json = "{}"
        job.finished_at = utcnow()
        emit_job_event(
            db,
            job=job,
            event_type="JOB_FAILED",
            status_before="RUNNING",
            status_after="FAILED",
            message="Job failed.",
            created_by=actor,
            payload={"error_code": job.error_code},
        )
        audit_job(db, actor=actor, action="job.fail", job=job, metadata={"error_code": job.error_code})
        return

    result = handler(parse_json_object(job.input_json))
    job.status = "SUCCEEDED"
    job.progress = 100
    job.message = result.message
    job.result_json = json.dumps(result.result, sort_keys=True)
    job.finished_at = utcnow()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_SUCCEEDED",
        status_before="RUNNING",
        status_after="SUCCEEDED",
        message=result.message,
        created_by=actor,
    )
    audit_job(db, actor=actor, action="job.succeed", job=job)


def run_pending_job(db: Session, *, job: Job, actor: str) -> Job:
    if job.status != "PENDING":
        raise ValueError("Only PENDING jobs can be run in MVP0.")
    run_job_now(db, job=job, actor=actor)
    db.commit()
    db.refresh(job)
    return job


def cancel_pending_job(db: Session, *, job: Job, actor: str) -> Job:
    if job.status != "PENDING":
        raise ValueError("Only PENDING jobs can be cancelled in MVP0.")
    job.status = "CANCELLED"
    job.progress = 100
    job.message = "Job cancelled."
    job.cancelled_at = utcnow()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_CANCELLED",
        status_before="PENDING",
        status_after="CANCELLED",
        message="Job cancelled.",
        created_by=actor,
    )
    audit_job(db, actor=actor, action="job.cancel", job=job)
    db.commit()
    db.refresh(job)
    return job
