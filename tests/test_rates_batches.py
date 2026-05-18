from otm_workbench.models import RateBatch, RateBatchIssue, RateBatchRow, RateBatchTable


def test_rate_batch_models_persist(db_session):
    batch = RateBatch(
        project_id="project_otm1",
        environment_id="uat",
        profile_id="profile_otm1",
        scenario_code="RATE_GEO_ONLY",
        name="Synthetic rate geo batch",
        domain_name="OTM1",
        source_type="api",
        created_by="codex",
    )
    db_session.add(batch)
    db_session.flush()

    table = RateBatchTable(
        batch_id=batch.id,
        table_name="RATE_GEO",
        sequence_index=4,
        requirement_level="REQUIRED",
        row_count=1,
        status="PENDING",
    )
    db_session.add(table)
    db_session.flush()

    row = RateBatchRow(
        batch_id=batch.id,
        batch_table_id=table.id,
        table_name="RATE_GEO",
        row_index=1,
        row_payload_json='{"RATE_GEO_GID": "OTM1.RG_DEMO_001"}',
        normalized_payload_json='{"RATE_GEO_GID": "OTM1.RG_DEMO_001"}',
        row_hash="hash",
        status="PENDING",
    )
    db_session.add(row)
    db_session.flush()

    issue = RateBatchIssue(
        batch_id=batch.id,
        batch_table_id=table.id,
        batch_row_id=row.id,
        severity="INFO",
        issue_code="ROW_ACCEPTED",
        table_name="RATE_GEO",
        column_name="RATE_GEO_GID",
        message="Row accepted.",
        details_json="{}",
    )
    db_session.add(issue)
    db_session.commit()

    assert db_session.query(RateBatch).count() == 1
    assert db_session.query(RateBatchTable).count() == 1
    assert db_session.query(RateBatchRow).count() == 1
    assert db_session.query(RateBatchIssue).count() == 1
