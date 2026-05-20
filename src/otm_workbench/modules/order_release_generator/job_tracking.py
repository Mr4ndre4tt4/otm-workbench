from sqlalchemy.orm import Session

from otm_workbench.models import Job, utcnow
from otm_workbench.platform.jobs import audit_job, dumps_limited_json_object, emit_job_event


SOURCE_MODULE = "order_release_generator"


def record_completed_order_release_job(
    db: Session,
    *,
    job_type: str,
    batch_id: str,
    result_payload: dict[str, object],
    created_by: str,
    message: str,
) -> Job:
    job = Job(
        job_type=job_type,
        source_module=SOURCE_MODULE,
        status="PENDING",
        progress=0,
        message="Job created.",
        input_json=dumps_limited_json_object({"batch_id": batch_id}, label="input"),
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
    job.message = message
    job.result_json = dumps_limited_json_object(result_payload, label="result")
    job.finished_at = utcnow()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_SUCCEEDED",
        status_before="RUNNING",
        status_after="SUCCEEDED",
        message=message,
        created_by=created_by,
    )
    audit_job(db, actor=created_by, action="job.succeed", job=job)
    db.commit()
    db.refresh(job)
    return job
