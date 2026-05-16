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
