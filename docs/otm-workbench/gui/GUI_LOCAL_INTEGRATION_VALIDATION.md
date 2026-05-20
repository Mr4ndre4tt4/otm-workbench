# GUI Local Integration Validation

**Status:** validated locally  
**Branch:** `codex/gui-local-integration-validation`

## Objective

Validate the browser-first GUI against a real local FastAPI backend without
committing local database files, credentials, or generated artifacts.

## Local Validation Shape

The validation used an isolated SQLite database:

```text
sqlite:///./var/gui_validation.db
```

`var/` is gitignored, so the database and local state are not versioned.

## Synthetic Setup

The validation used synthetic-only data:

```text
User: synthetic.user@example.test
Workspace: GUI Validation Workspace
Project: GUI Synthetic Rollout
Profile: Default
Environment: DEV
Domain: OTM1
```

No client names or client payloads were used.

## Steps Validated

1. Created the isolated SQLite schema with SQLAlchemy metadata.
2. Bootstrapped a synthetic admin user through `otm_workbench.cli`.
3. Started FastAPI on `http://127.0.0.1:8000`.
4. Confirmed `/health` returned database `ok`.
5. Created workspace/project/profile/environment through protected API calls.
6. Set active context through `POST /api/v1/platform/active-context`.
7. Validated the GUI dev proxy through `http://127.0.0.1:5173/api`.
8. Confirmed login, projects list, and Project Cockpit summary through the
   Vite same-origin proxy.

## Result

```text
POST /api/v1/platform/session/login via Vite proxy -> 200
GET /api/v1/platform/projects via Vite proxy -> total 1
GET /api/v1/platform/project-cockpit/summary via Vite proxy -> Project Cockpit
```

## Bug Fixed

During validation, `python -m otm_workbench.cli bootstrap-admin` created the
admin user but failed while printing the user email after the SQLAlchemy session
closed.

The CLI now captures the email before leaving the session scope.

## Next Step

Add a browser-level visual/interaction validation pass for login and context
switching once the GUI branches are merged into a stable base.
