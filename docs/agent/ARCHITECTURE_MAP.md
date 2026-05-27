# OTM Workbench Architecture Map

**Status:** active governance baseline
**Date:** 2026-05-27

## Repository Shape

```text
.
|-- AGENTS.md
|-- README.md
|-- pyproject.toml
|-- alembic.ini
|-- docs/
|   |-- agent/
|   |-- otm-workbench/
|   `-- superpowers/
|-- frontend/
|-- migrations/
|-- src/
|-- tests/
|-- output/
`-- OTM_RESOURCES/
```

## Backend

Primary package:

```text
src/otm_workbench/
```

Observed areas:

- platform app entry, config, database, dependencies, security;
- module routers and services under `src/otm_workbench/modules/`;
- Catalog Core under `src/otm_workbench/catalog/`;
- Evidence Hub under `src/otm_workbench/evidence_hub/`;
- Alembic migrations under `migrations/`.

The backend should remain the owner of:

- navigation and module visibility;
- client/domain, environment, Public View, and visibility/access-policy scope;
- capabilities and permissions;
- lifecycle and readiness;
- available actions and disabled reasons;
- validation rules;
- jobs, artifacts, manifests, audit, and evidence;
- OTM Data Dictionary validation.

## Frontend

Primary app:

```text
frontend/src/
```

Observed areas:

- app shell and routes under `frontend/src/app/`;
- module views under `frontend/src/modules/`;
- API hooks and types under `frontend/src/platform/`;
- browser QA scripts under `frontend/scripts/`;
- React/Vitest functional tests under `frontend/src/app/`.

The frontend should render backend-owned state and route users to focused
screens. It should not become the source of truth for permissions, lifecycle,
or OTM dependency decisions.

## Documentation

Governance entry layer:

```text
docs/agent/
```

Deep product and engineering docs:

```text
docs/otm-workbench/
```

Historical design and implementation plans:

```text
docs/superpowers/
```

## Current Visual Diagnostics

FigJam as-is solution diagnostic:

```text
OTM Workbench - Stack As-Is Map
https://www.figma.com/board/4oR1pKe0Ia3g5IeJlkLnh2
```

The diagnostic board visualizes:

- current stack and user modes;
- active UI phase versus internal/excluded module surfaces;
- implemented/evidenced module capabilities versus current target shape;
- frontend module views, backend routers, database model groups, artifacts,
  manifests, and evidence;
- operational flow from login/context selection through validation and handoff;
- cleanup decision rules;
- high-level data model group dependencies.

Key architecture reading:

- The backend is richer than the current target UI surface.
- Several routes exist in code or docs but are not current top-level UI targets.
- Catalog Core should remain a backend/internal validation dependency even when
  hidden from top-level navigation.
- Evidence Hub should stay module-local or backend-traceable until explicitly
  reintroduced.
- Settings is the intended home for setup surfaces in the current UI phase.

## Validation Commands

Backend:

```powershell
python -m pytest
python -m alembic upgrade head
```

Frontend:

```powershell
cd frontend
npm run test
npm run build
```

Functional/browser QA is module-specific through scripts in
`frontend/package.json`.

## Architecture Cautions

- Do not add new top-level module routes without updating governance, roadmap,
  backend navigation contracts, docs, tests, and QA evidence.
- Do not use frontend-only module identity maps as durable product truth.
- Do not mix dev/DBA tools into consultant operational flows.
- Do not let any module read, write, display, or export operational data without
  explicit client/domain, environment, and visibility/access-policy scope.
- Do not make Project Cockpit responsible for project lifecycle control,
  readiness, workstreams, blockers, activity, or jobs. Keep those concerns out
  of the current Cockpit UI.
- For the current UI phase, keep project/profile/user/access setup in
  Settings and keep separate Admin Console / Jobs, Developer Tools,
  Evidence Hub, Catalog Core, and standalone Coordinate Quality out of
  top-level navigation.
- Do not use current UI shape as the source for Figma wireframes; use validated
  module specs, current UI phase scope, and the supplied PDF.
