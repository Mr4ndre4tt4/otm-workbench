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

```powershell
python -m pytest tests/test_reference_catalog.py tests/test_rates_dictionary.py tests/test_rates_csv_preview.py tests/test_rates_batch_approval.py tests/test_load_plan_package_intake.py tests/test_load_plan_csvutil_builder.py tests/test_load_plan_zip_analysis.py
python -m alembic upgrade head
```
