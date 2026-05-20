# GUI Contract Audit - OTM Workbench

**Status:** planning foundation
**Date:** 2026-05-20
**Scope:** backend contract audit for the first web GUI, keeping desktop migration in mind.

## 1. Classification

This audit covers:

- Codebase UI Audit
- Frontend Architecture
- Backend Contract Audit
- Information Architecture
- Documentation Update

The goal is to decide what the GUI can safely consume now, and what should be added to the backend before frontend code starts inventing product rules.

## 2. Verdict

The backend is ready for a thin Workbench shell prototype, but not yet ready for a governed GUI scaffold that preserves the product rules we want.

The strongest contracts today are:

- Authentication/session basics.
- Backend-owned modules and navigation.
- Active context basics.
- Jobs and job events.
- Error envelope.
- Rates, Assets, Load Plan, Catalog, and Integration Mapping list/detail/action surfaces.

The main gaps before GUI implementation are:

- Backend-owned user preferences for theme, density, layout, and system-following behavior.
- Navigation metadata for groups, icon keys, sort order, and module surface type.
- List endpoints for project/profile/environment selectors.
- A normalized action contract so buttons are not hardcoded in each screen.
- A normalized list/query contract for search, filters, sorting, and pagination.
- Module overview/read-model endpoints for cockpit-style landing pages.

## 3. Ready For Shell

These contracts are usable for the first web shell:

| Concern | Current contract | Status | GUI use |
| --- | --- | --- | --- |
| Health | `GET /health` | Ready | API/degraded banner and boot check. |
| Login | `POST /api/v1/platform/session/login` | Ready | Login form. |
| Current user | `GET /api/v1/platform/session/me` | Ready | User menu and session hydration. |
| Modules | `GET /api/v1/platform/modules` | Ready, thin | Module registry and status. |
| Navigation | `GET /api/v1/platform/navigation` | Ready, thin | Sidebar items. |
| Active context | `GET/POST /api/v1/platform/active-context` | Ready, thin | Context banner/switcher. |
| Capabilities | `GET /api/v1/platform/active-context/capabilities` | Ready | Permission-aware UI states. |
| Jobs | `POST/GET /api/v1/platform/jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/run`, `POST /jobs/{id}/cancel`, `GET /jobs/{id}/events` | Ready | Activity rail, job drawer, progress state. |
| Errors | `ErrorResponse` and FastAPI handlers | Ready | Shared error panel/toast contract. |

## 4. Must Add Before Scaffold

These should be added before the React/Vite app begins, because they affect global architecture and should not become frontend-only state.

### 4.1 User Preferences

Add backend-owned preferences from the start:

```text
GET /api/v1/platform/user-preferences
PUT /api/v1/platform/user-preferences
```

Minimum response:

```json
{
  "user_id": "synthetic-user-id",
  "theme_mode": "light",
  "follow_system_theme": false,
  "density": "comfortable",
  "sidebar_mode": "expanded",
  "updated_at": "2026-05-20T00:00:00"
}
```

Rules:

- Default theme is `light`.
- `theme_mode` supports `light` and `dark`.
- `follow_system_theme` lets the GUI follow Windows/browser preference without making the preference local-only.
- The frontend may read OS/browser preference, but must persist the user's selected mode/backend preference.
- Token and icon variants must derive from the preference contract.

### 4.2 Navigation Metadata

Extend `Module` or the navigation projection with:

```text
group_key
group_label
icon_key
sort_order
surface_type
description
is_primary
```

This supports consistent sidebar grouping without frontend hardcoding:

```text
Cockpit
Build
Govern
Admin
```

The current flat navigation is acceptable only for an interim shell.

### 4.3 Active Context Selectors

The shell needs selectable data for workspace, project, profile, and environment.

Current coverage:

- `GET /api/v1/platform/workspaces` exists.
- `POST /api/v1/platform/projects` exists.
- `POST /api/v1/platform/profiles` exists.
- `POST /api/v1/platform/environments` exists.

Add:

```text
GET /api/v1/platform/projects?workspace_id=...
GET /api/v1/platform/profiles?project_id=...
GET /api/v1/platform/environments?project_id=...
```

This keeps active context selection backend-owned and avoids frontend fixture state.

### 4.4 Session Lifecycle

Add a logout/revoke endpoint:

```text
POST /api/v1/platform/session/logout
```

There is already a `session_tokens.revoked_at` column, so this is a natural contract completion.

## 5. Must Add Before Module Screens

These are needed before building substantial module pages.

### 5.1 Standard List Contract

`PageResponse` exists, but list endpoints do not consistently expose query shape. Define a shared guideline for:

```text
page
page_size
search
sort
filters
status
project_id
profile_id
environment_id
domain_name
```

The GUI should be able to render `ObjectList` the same way across Rates, Assets, Integration Mapping, Evidence, Jobs, and Load Plan.

### 5.2 Available Actions Contract

Avoid hardcoding buttons per lifecycle status in the frontend. Add an optional field to detail/readiness responses:

```json
{
  "available_actions": [
    {
      "key": "approve",
      "label": "Approve",
      "method": "POST",
      "href": "/api/v1/modules/rates/batches/{batch_id}/approve",
      "variant": "primary",
      "requires_confirmation": true,
      "disabled": false,
      "disabled_reason": null
    }
  ]
}
```

This is especially important for Rates, Load Plan, Cutover, Order Release Generator, and Integration Mapping.

### 5.3 Module Overview Read Models

Every module needs a small overview endpoint before polished landing pages:

```text
GET /api/v1/modules/{module}/summary
```

Minimum summary:

```text
health/status
primary_object_counts
recent_objects
recent_jobs
recent_artifacts
open_blockers
recommended_next_actions
```

The current `GET /api/v1/modules/load-plan/summary` is a good starting pattern.

### 5.4 Object Relationship Blocks

Object detail screens should not require the frontend to join many endpoints. Detail responses should expose or link related:

```text
jobs
artifacts
evidence
audit
validation/readiness
```

Links can be IDs or HAL-like `href`s. The important part is that the relationship shape is backend-owned.

## 6. Module Readiness

| Module | GUI readiness | Notes |
| --- | --- | --- |
| Platform Shell | Partial | Auth, navigation, active context, jobs exist. Needs preferences, context list selectors, logout, richer nav metadata. |
| Project Cockpit | Partial | Shell data exists, but cockpit summary/read-model is not explicit yet. |
| OTM Catalog Core | Good | Tables, columns, macro-objects, load plan and validators are usable. Needs overview and standard list/query guidance. |
| Rates Studio | Good | Strong batch lifecycle, readiness, validation, CSV preview/export, artifacts/evidence. Needs action metadata and query normalization. |
| Master Data / Data Factory | Partial | Template and workflow actions exist. Missing batch list/detail endpoints for natural GUI navigation. |
| Coordinate Quality | Partial | Validate, batch detail, results, export exist. Missing batch list and summary. |
| Load Plan / Cutover | Good | Broad backend surface exists, including packages, sequence, checklist, readiness, handoff, CSVUTIL, ZIP analysis, review queue. Needs information architecture and action metadata. |
| Assets Library | Good | Classification, assets, links, versions, archive and download are GUI-friendly. Needs query normalization. |
| Order Release Generator | Partial | Templates, create/detail, preview/generate/submit guard exist. Missing batch list and action metadata. |
| Integration Mapping Studio | Good | Definitions, systems, endpoints, payload artifacts, schema trees, mappings, loops, joins, lookups, validation, preview and spec generation exist. Needs edit/archive decisions and action metadata. |
| Evidence Hub | Partial | Evidence list/detail and artifact download exist. Needs broader artifact list/search and relationship filters for module/object detail panels. |

## 7. Design System Contract Implications

The frontend should implement Workbench UI Kit components around these backend contracts:

- `AppShell` consumes `navigation`, `modules`, `active-context`, `capabilities`, and `user-preferences`.
- `ThemeProvider` consumes backend preferences and only uses browser/Windows preference as an input signal.
- `SidebarNav` renders backend `group_key`, `icon_key`, `sort_order`, `status`, and permission-filtered items.
- `ObjectList` consumes `PageResponse` plus a standard query contract.
- `ObjectDetailHeader` consumes lifecycle status and `available_actions`.
- `ActivityRail` consumes jobs and job events.
- `EvidencePanel` consumes object-linked evidence/artifact relationships.

No module screen should create its own button style, status colors, or lifecycle logic unless the exception is documented in the GUI exception register.

## 8. Recommended Next Slices

1. Add backend-owned user preferences and tests.
2. Extend module/navigation metadata for GUI grouping and icons.
3. Add project/profile/environment list endpoints for active context selection.
4. Document the standard list/action/read-model contracts.
5. Add missing batch list/detail endpoints for Master Data, Coordinate Quality, and Order Release Generator.
6. Add module summary/read-model endpoints, starting with Platform Cockpit and Rates.
7. Start the React/Vite shell scaffold only after items 1-3 are complete, or accept a deliberately temporary shell with those gaps documented.

## 9. Acceptance Criteria For GUI Scaffold Start

The GUI scaffold can start when:

- `GET/PUT /api/v1/platform/user-preferences` exists.
- Navigation includes group and icon metadata, or the shell explicitly treats flat navigation as temporary.
- Active context selectors can fetch workspaces, projects, profiles, and environments from the backend.
- The frontend architecture document states that backend contracts own preferences, navigation, permissions, lifecycle gates, and available actions.
- Tests cover the new global contracts.

## 10. Linear Note

Linear sync was attempted during this audit, but the connector could not find the current project by the available project name. Once the correct Linear project or team identifier is available, this audit should be linked as the next GUI planning item after `OTM-56`.
