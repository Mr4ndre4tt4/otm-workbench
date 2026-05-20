# GUI Context Switcher

**Status:** initial context selector delivered  
**Branch:** `codex/gui-context-switcher`

## Objective

Let authenticated users select the active project/profile/environment/domain
from backend-owned platform contracts.

## Backend Contracts

```text
GET /api/v1/platform/projects
GET /api/v1/platform/projects?workspace_id={workspace_id}
GET /api/v1/platform/profiles?project_id={project_id}
GET /api/v1/platform/environments?project_id={project_id}
POST /api/v1/platform/active-context
```

The list endpoints return `PageResponse<IdNameResponse>` and require
authentication.

## Frontend Behavior

- The selector appears only after login.
- Project list is loaded from `/platform/projects`.
- Profile and environment lists are loaded only after a project is selected.
- Applying the selector posts the active context to the backend.
- The shell invalidates platform queries after context update so navigation,
  cockpit summary, and related platform contracts can refresh from backend
  truth.

## Boundary

The GUI does not infer context readiness or permissions. It only submits the
selected context and renders backend responses.

## Verification

```text
python -m pytest tests\test_operational_context.py::test_active_context_selector_lists_projects_profiles_and_environments -q
npm run test
```

The frontend test verifies that selector GETs and the active-context POST carry
the bearer token.
