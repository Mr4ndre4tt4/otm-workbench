# GUI API Contract Patterns - OTM Workbench

**Status:** planning foundation
**Date:** 2026-05-20
**Scope:** backend/API contracts for reusable GUI screens before React/Vite scaffold.

## 1. Decision

The GUI must render backend contracts. It must not duplicate lifecycle gates,
permissions, validation rules, OTM dependency rules, or action availability in
frontend-only logic.

This document defines the standard shapes for:

- Object lists.
- Available actions.
- Module summaries/read-models.
- Object detail relationship blocks.
- Error and visual state mapping.

These patterns are the target for new backend endpoints and for hardening
existing endpoints over time.

## 2. List Contract

Use `PageResponse[T]` as the envelope for object lists:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 50
}
```

All new GUI-facing list endpoints should support the same query names whenever
they are meaningful:

```text
page
page_size
search
sort
status
source_module
project_id
profile_id
environment_id
domain_name
created_from
created_to
updated_from
updated_to
```

Module-specific filters are allowed, but the shared names above must keep the
same meaning across modules.

### 2.1 Sort Syntax

Use one comma-separated `sort` parameter:

```text
sort=created_at:desc,name:asc
```

Rules:

- Missing direction defaults to `asc`.
- Unsupported sort fields return `422 VALIDATION_ERROR` or `400 INVALID_SORT`.
- Backend decides the allowed sort fields per endpoint.

### 2.2 Filter Syntax

Prefer explicit query parameters for common filters:

```text
GET /api/v1/modules/rates/batches?status=VALIDATED&project_id=...
```

For advanced filters, use repeated `filter` parameters only after the simple
shape becomes insufficient:

```text
filter=severity:eq:ERROR&filter=table_name:eq:RATE_GEO
```

Do not make the frontend construct SQL-like expressions.

### 2.3 List Item Minimum Fields

Object list items should include:

```json
{
  "id": "synthetic-id",
  "display_name": "Synthetic object",
  "status": "ACTIVE",
  "created_at": "2026-05-20T00:00:00",
  "updated_at": "2026-05-20T00:00:00",
  "project_id": "synthetic-project-id",
  "profile_id": null,
  "environment_id": null,
  "domain_name": "OTM1",
  "summary": {},
  "badges": [],
  "available_actions": []
}
```

If the object has a natural business code, include both `code` and
`display_name`.

## 3. Available Actions Contract

Buttons and row actions must be backend-owned when they depend on lifecycle,
permissions, validation, readiness, or data availability.

Use `available_actions` on list items, detail headers, readiness responses, and
summary cards:

```json
{
  "available_actions": [
    {
      "key": "approve",
      "label": "Approve",
      "method": "POST",
      "href": "/api/v1/modules/rates/batches/synthetic-id/approve",
      "variant": "primary",
      "icon_key": "check",
      "requires_confirmation": true,
      "disabled": false,
      "disabled_reason": null,
      "permission": "rates.approve",
      "result_hint": "refresh_object"
    }
  ]
}
```

### 3.1 Action Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `key` | Yes | Stable semantic action key. |
| `label` | Yes | Human-readable command label. |
| `method` | Yes | HTTP method the GUI should call. |
| `href` | Yes | Backend endpoint for the command. |
| `variant` | Yes | `primary`, `secondary`, `danger`, `ghost`, or `menu`. |
| `icon_key` | No | Semantic icon key for UI mapping. |
| `requires_confirmation` | Yes | Whether the GUI must show confirmation. |
| `disabled` | Yes | Whether action is visible but not executable. |
| `disabled_reason` | No | Backend-owned explanation for disabled state. |
| `permission` | No | Capability name when relevant. |
| `result_hint` | No | `refresh_object`, `refresh_list`, `download`, `open_job`, or `none`. |

### 3.2 Action Rules

- The GUI may choose placement, but not availability.
- Destructive or irreversible actions must include `requires_confirmation`.
- Disabled actions should remain visible when the reason helps the user resolve
  blockers.
- Hidden actions are for permissions or features that should not be disclosed.
- Direct OTM execution stays unavailable until backend contracts explicitly
  support it.

## 4. Module Summary Contract

Each module should eventually expose a compact read-model:

```text
GET /api/v1/modules/{module}/summary
```

Minimum response:

```json
{
  "module_id": "rates",
  "status": "ok",
  "title": "Rates Studio",
  "description": "Prepare, validate, approve and export OTM rates packages.",
  "primary_object": "rate_batch",
  "counts": [
    {"key": "draft", "label": "Draft", "value": 2, "severity": "neutral"},
    {"key": "blocked", "label": "Blocked", "value": 1, "severity": "warning"}
  ],
  "recent_objects": [],
  "open_blockers": [],
  "recent_jobs": [],
  "recent_artifacts": [],
  "available_actions": []
}
```

### 4.1 Summary Rules

- Summaries are decision-oriented, not decorative.
- Counts must link to real filters when possible.
- Blockers must be client-safe and avoid raw row values.
- Recent jobs/artifacts should include IDs and display labels, not filesystem
  paths.

## 5. Object Detail Contract

Detail endpoints should give the GUI enough structure to render the page header
and relationship tabs without inventing backend joins.

Minimum shape:

```json
{
  "id": "synthetic-id",
  "code": "SYNTHETIC_CODE",
  "display_name": "Synthetic Object",
  "status": "VALIDATED",
  "lifecycle": {
    "current_step": "validated",
    "next_step": "approve",
    "blocked": false,
    "blocked_reason": null
  },
  "summary": {},
  "available_actions": [],
  "relationships": {
    "jobs": {"href": "/api/v1/platform/jobs?source_module=rates&aggregate_id=synthetic-id", "count": 0},
    "artifacts": {"href": "/api/v1/modules/rates/batches/synthetic-id/artifacts", "count": 0},
    "evidence": {"href": "/api/v1/modules/rates/batches/synthetic-id/evidence", "count": 0},
    "audit": {"href": "/api/v1/platform/audit-logs?target_id=synthetic-id", "count": null},
    "validation": {"href": "/api/v1/modules/rates/batches/synthetic-id/issues", "count": 0}
  }
}
```

Relationship blocks may be links instead of embedded lists. The important rule
is that the backend owns which relationships exist.

## 6. Visual State Mapping

Backend responses should let the GUI render standard states:

| Backend condition | GUI state |
| --- | --- |
| `401 UNAUTHENTICATED` | Login/session expired. |
| `403 FORBIDDEN` | No permission state. |
| Empty `items` with no filters | Empty state. |
| Empty `items` with filters/search | No results state. |
| `disabled: true` action | Disabled action with backend reason. |
| `blocked: true` lifecycle | Blocked banner. |
| Module `status=PLANNED` | Planned/disabled module state. |
| Health `degraded` | API degraded banner. |

The GUI should have reusable components for loading, empty, no results, error,
warning, success, blocked, disabled-by-permission, and read-only.

## 7. Error Contract

Use the existing `ErrorResponse` envelope:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "The request payload is invalid.",
  "details": {}
}
```

Rules:

- `code` must be stable and machine-readable.
- `message` must be safe to display.
- `details` must be client-safe and should not include real client payloads,
  filesystem paths, secrets, or raw CSV/XML row values.

## 8. Frontend Implementation Implications

Workbench UI Kit should map contracts to reusable components:

- `DataTable` consumes `PageResponse`.
- `FilterBar` writes the standard query parameters.
- `ObjectDetailHeader` renders status, lifecycle, and `available_actions`.
- `ActionButton` uses action `variant`, `icon_key`, confirmation, and disabled
  reason.
- `ModuleOverview` consumes module summary read-models.
- `RelationshipPanel` consumes relationship blocks.
- `ErrorState` consumes `ErrorResponse`.

## 9. Adoption Order

Recommended backend-first order:

1. Add action metadata to high-lifecycle flows: Rates, Load Plan/Cutover, Order
   Release Generator, Integration Mapping.
2. Add module summaries, starting with Project Cockpit and Rates.
3. Normalize list query parameters for the first GUI-facing object lists.
4. Add relationship blocks to object detail endpoints as screens are built.
5. Begin React/Vite shell once global shell contracts are merged.

## 10. Acceptance Criteria

New GUI-facing backend endpoints should be considered ready when:

- They use shared envelopes and query names where applicable.
- They expose backend-owned actions for lifecycle-dependent commands.
- They return client-safe errors and summaries.
- They avoid raw client data in docs, tests, examples, evidence, and audit.
- Tests cover list filters, disabled/blocked action states, and error responses.
