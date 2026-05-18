# otm-workbench

Local-first workbench for Oracle Transportation Management implementation projects.

## MVP 0 Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
python -m uvicorn otm_workbench.main:app --reload
```

The MVP 0 surface is backend/API-only.

## MVP 0 Verification

```powershell
python -m pytest
python -m alembic upgrade head
python -m uvicorn otm_workbench.main:app --reload
```

## Rates Reference Catalog Verification

The Rates Reference Catalog is backend/API-only. It validates OTM table metadata
against the local Data Dictionary under `OTM_RESOURCES/DATA_DICT26B` and exposes
reference catalog contracts for future tariff workflows.

The Rates Batch Contract adds backend-only persisted batches for synthetic tariff
scenarios. It stores submitted OTM table rows, validates table and column names
against the local Data Dictionary, records batch issues, and generates technical
CSV previews using OTM table header rules.

The Rates CSV Export Artifacts slice turns validated batches into internal ZIP
artifacts with a client-safe manifest/evidence trail; it does not perform OTM
upload, CSVUTIL packaging, or XML export.

The Rates Batch Approval slice adds backend readiness and approval gates for
validated or exported batches, with client-safe approval evidence, audit, and
domain event records.

The Load Plan Package Intake slice registers approved Rates CSV exports as
backend-only Load Plan packages, preserving links to artifacts, manifests, and
client-safe evidence without generating CSVUTIL or cutover readiness outputs.

The Load Plan CSVUTIL Builder slice generates internal CTL/CL control artifacts
from registered Load Plan packages, with manifest/evidence metadata, without
executing CSVUTIL, connecting to OTM, or producing cutover readiness.

The Load Plan ZIP Analysis slice inspects registered package ZIP artifacts,
records client-safe file/table/row counts and Data Dictionary findings, and
persists manifest/evidence/audit/event metadata without running CSVUTIL,
connecting to OTM, creating setup review decisions, or producing cutover
readiness.

The Load Plan Setup Review Queue slice creates client-safe `PENDING_REVIEW`
items from ZIP Analysis findings, preserving audit/event metadata, without
making review decisions, approving packages, or producing cutover readiness.

The Load Plan Review Decisions slice records append-only decisions for review
queue items through `POST /api/v1/modules/load-plan/review-queue/{item_id}/decide`.
Allowed statuses are `CONFIRMED`, `REJECTED`, `NEEDS_MANUAL_ACTION`, and
`EXCLUDED_FROM_CUTOVER`; list/detail review queue responses expose latest
decision metadata without copying decision notes into client-safe evidence,
audit logs, or domain events.

The Load Plan Sequence Blockers slice generates backend-only sequence snapshots
with client-safe blockers from package metadata, latest ZIP Analysis, review
decisions, and local OTM Data Dictionary parent-table dependencies. It does not
execute CSVUTIL, connect to OTM, transition package status, or produce cutover
readiness.

The Load Plan Cutover Readiness slice generates backend-only readiness records
from the latest sequence snapshots, preserving client-safe blockers, evidence,
audit, and domain events. It does not export cutover packages, execute CSVUTIL,
connect to OTM, or transition package status.

The Load Plan Readiness Export slice exports persisted cutover readiness records
as internal ZIP artifacts with `manifest.json`, `readiness.json`, and
`blockers.json`, plus client-safe evidence, audit, and domain events. It does
not provide a download endpoint, execute CSVUTIL, connect to OTM, or transition
package status.

The Evidence Hub Index slice adds backend-only list/detail APIs for client-safe
evidence across modules, including linked artifact and manifest summaries. It
does not download artifacts, build archive packages, expose filesystem paths, or
return full manifest payloads.

The Evidence Hub Artifact Download slice adds an authenticated artifact download
endpoint for artifacts linked to client-safe evidence. It recomputes SHA-256
before serving files, audits successful downloads, and does not expose
filesystem paths in API responses.

The Evidence Hub Archive Package slice generates metadata-only archive ZIPs from
filtered client-safe evidence, recording artifact, manifest, evidence, audit,
and domain event rows. Source artifact bytes are not bundled; individual
artifact download remains controlled by the audited download endpoint.

The Load Plan Cutover Handoff slice adds a backend-only eligibility and commit
gate that marks packages `READY_FOR_CUTOVER` only after READY readiness,
readiness export, and Evidence Hub archive evidence exist. It records
client-safe evidence, audit, and domain events without executing CSVUTIL,
uploading to OTM, or creating a real cutover package.

```powershell
python -m pytest tests/test_reference_catalog.py tests/test_rates_dictionary.py tests/test_rates_csv_preview.py tests/test_rates_batch_approval.py tests/test_load_plan_package_intake.py tests/test_load_plan_csvutil_builder.py tests/test_load_plan_zip_analysis.py tests/test_load_plan_review_queue.py tests/test_load_plan_review_decisions.py tests/test_load_plan_sequence_blockers.py tests/test_load_plan_cutover_readiness.py tests/test_load_plan_readiness_export.py tests/test_evidence_hub_index.py tests/test_load_plan_cutover_handoff.py
python -m alembic upgrade head
```
