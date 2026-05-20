import json

from otm_workbench.models import Job, JobEvent
from tests.test_order_release_generator_xml_preview import create_batch


def job_event_types(db_session, job_id):
    return [
        event.event_type
        for event in (
            db_session.query(JobEvent)
            .filter(JobEvent.job_id == job_id)
            .order_by(JobEvent.created_at, JobEvent.id)
            .all()
        )
    ]


def test_preview_order_release_xml_records_succeeded_job(client, admin_header, db_session):
    batch = create_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/order-release-generator/batches/{batch['id']}/preview-xml",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    job = db_session.get(Job, payload["job_id"])
    assert job is not None
    assert job.job_type == "ORDER_RELEASE_XML_PREVIEW"
    assert job.source_module == "order_release_generator"
    assert job.status == "SUCCEEDED"
    assert job.progress == 100
    input_payload = json.loads(job.input_json)
    result_payload = json.loads(job.result_json)
    assert input_payload == {"batch_id": batch["id"]}
    assert result_payload["batch_id"] == batch["id"]
    assert result_payload["release_count"] == 2
    assert result_payload["line_count"] == 3
    assert "xml" not in result_payload
    assert "<Transmission>" not in job.result_json
    assert "OR_SYN_001" not in job.result_json
    assert job_event_types(db_session, job.id) == ["JOB_CREATED", "JOB_STARTED", "JOB_SUCCEEDED"]


def test_generate_order_release_xml_artifact_records_succeeded_job(client, admin_header, db_session):
    batch = create_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/order-release-generator/batches/{batch['id']}/generate-xml-artifact",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    job = db_session.get(Job, payload["job_id"])
    assert job is not None
    assert job.job_type == "ORDER_RELEASE_XML_GENERATE"
    assert job.source_module == "order_release_generator"
    assert job.status == "SUCCEEDED"
    assert job.progress == 100
    input_payload = json.loads(job.input_json)
    result_payload = json.loads(job.result_json)
    assert input_payload == {"batch_id": batch["id"]}
    assert result_payload["batch_id"] == batch["id"]
    assert result_payload["artifact_id"] == payload["artifact_id"]
    assert result_payload["evidence_id"] == payload["evidence_id"]
    assert result_payload["sha256"] == payload["sha256"]
    assert result_payload["size_bytes"] == payload["size_bytes"]
    assert result_payload["release_count"] == 2
    assert result_payload["line_count"] == 3
    assert "file_path" not in result_payload
    assert "<Transmission>" not in job.result_json
    assert "OR_SYN_001" not in job.result_json
    assert job_event_types(db_session, job.id) == ["JOB_CREATED", "JOB_STARTED", "JOB_SUCCEEDED"]
