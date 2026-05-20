from otm_workbench.models import Job
from tests.test_order_release_generator_xml_preview import create_batch


def test_submit_order_release_batch_to_otm_is_guarded_in_mvp0(client, admin_header, db_session):
    batch = create_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/order-release-generator/batches/{batch['id']}/submit-otm",
        headers=admin_header,
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["code"] == "ORDER_RELEASE_OTM_SUBMIT_DISABLED"
    assert payload["message"] == "Direct OTM submission is disabled in MVP0."
    assert payload["details"] == {
        "batch_id": batch["id"],
        "required_capability": "order_release_generator.submit_otm",
        "reason": "MVP0 has no governed OTM connection/capability for direct submit.",
    }
    assert db_session.query(Job).filter(Job.source_module == "order_release_generator").count() == 0


def test_submit_order_release_batch_to_otm_rejects_missing_batch(client, admin_header):
    response = client.post(
        "/api/v1/modules/order-release-generator/batches/missing-batch/submit-otm",
        headers=admin_header,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "ORDER_RELEASE_BATCH_NOT_FOUND"
