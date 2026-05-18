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

```powershell
python -m pytest tests/test_reference_catalog.py tests/test_rates_dictionary.py tests/test_rates_csv_preview.py tests/test_rates_batch_approval.py
python -m alembic upgrade head
```
