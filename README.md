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

```powershell
python -m pytest tests/test_reference_catalog.py tests/test_rates_dictionary.py tests/test_rates_csv_preview.py
python -m alembic upgrade head
```
