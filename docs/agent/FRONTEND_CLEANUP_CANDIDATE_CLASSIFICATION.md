# Frontend Cleanup Candidate Classification

**Status:** active cleanup planning
**Date:** 2026-05-28
**GitHub issue:** #233

## Purpose

Classify frontend cleanup candidates before deleting, archiving, or moving any
source. This document turns the route inventory into reviewable cleanup slices.

## Source Inputs

- `docs/agent/FRONTEND_ROUTE_INVENTORY.md`
- `docs/agent/CURRENT_SCOPE.md`
- `docs/agent/TO_BE_SOLUTION_ALIGNMENT_PLAN.md`
- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
- `docs/agent/CONTEXT_ISOLATION_VALIDATION_MATRIX.md`

## Classification Terms

| Term | Meaning |
|---|---|
| Keep | Preserve as an active current-phase route or required shared component. |
| Hide | Keep source/runtime capability, but prevent normal top-level exposure. |
| Absorb | Move user-facing purpose into another active route family. |
| Alter | Keep the surface, but change labels, guards, tests, or route behavior. |
| Archive | Move docs or generated evidence out of active guidance after approval. |
| Remove | Delete source only after an explicit implementation issue and tests. |
| Create | Add a missing guard, test, manifest, or doc before cleanup can proceed. |

## Active Route Surfaces

| Surface | Treatment | Rationale | Required validation before change |
|---|---|---|---|
| `/home` Cockpit | Keep | Current context selector, accelerator launcher, Public View entry, and project-info hub. | Cockpit tests and browser freshness gate for visual claims. |
| `/settings` Settings | Keep / Alter | Current setup and access-control home; reuses `AdminConsoleView`. | Settings access tests; ensure separate Admin Console does not reappear. |
| `/rates` Rates Studio | Keep | Accepted active module with route-level lifecycle. | Rates backend/frontend focused tests before Rates changes. |
| `/assets` Assets Library | Keep | Accepted active module and controlled asset/version/link library. | Assets tests plus Data Dictionary env when needed. |
| `/master-data` Master Data | Keep | Active Data Factory and Quality Tools route family. | Master Data and Coordinate Quality focused tests. |
| `/load-plan` Load Plan | Keep | Active package, CSVUTIL, readiness, and handoff dependency. | Load Plan tests and browser freshness gate for screenshots. |
| `/order-release-generator` Order Release | Keep | Active template/batch/XML workflow. | Order Release focused tests. |
| `/integration-mapping` Integration Mapping | Keep / Reserved | Active module, but reserved for its dedicated workstream. | Do not modify unless the user explicitly requests it or a minimal cross-module fix is required. |

## Excluded Or Internal Surfaces

| Surface | Treatment | Rationale | Safe next slice |
|---|---|---|---|
| `/catalog` Catalog Core | Hide | Remains a backend/internal Data Dictionary and dependency source, not normal UI. | Add or preserve direct-route unavailable tests; do not remove backend catalog APIs. |
| `/evidence` Evidence Hub | Hide | Evidence stays module-local/backend-traceable for this phase. | Classify browser scripts and frontend tests that still expect top-level evidence. |
| `/admin` Admin Console / Jobs | Absorb / Hide | Setup is absorbed into Settings; Jobs dashboard is out of main UI. | Keep Settings tests authoritative; add a stale `/admin` recovery test if missing. |
| `/dev-tools` Developer Tools | Hide | Developer diagnostics must stay restricted/internal. | Ensure normal navigation cannot expose it; avoid deleting diagnostics used by tests. |
| Coordinate Quality top-level exposure | Absorb | Quality Tools belong inside Master Data, not top-level navigation. | Keep Master Data route coverage for Quality Tools. |
| Generic dashboards/readiness/workstreams | Remove only by later approval | Not part of current accelerator model. | Inventory any remaining labels/components before deleting. |

## Special And Test Surfaces

| Surface | Treatment | Rationale | Required validation |
|---|---|---|---|
| `/__gui/component-gallery` | Hide | Internal design utility only. | Must never appear in backend navigation. |
| `UnknownRoute` | Keep | Required stale-route recovery behavior. | Frontend route tests. |
| `frontend/scripts/functional-*-browser.mjs` | Alter | Scripts are evidence tools; update stale expectations instead of deleting. | `node --check` and fresh runtime gate before screenshots. |
| `AppFunctional*.test.tsx` | Alter | Tests should follow current active scope and distinguish hidden UI from retained backend capability. | Focused Vitest for touched modules. |
| Excluded module frontend components | Hide now, remove later | Source may support internal dependencies or future reintroduction. | Separate removal issue with impact review and tests. |

## Recommended Next Implementation Slices

1. Evidence/Admin/DevTools stale-route recovery tests:
   Add or tighten tests that direct excluded routes return `Module unavailable`
   when backend navigation omits them.

2. Browser script classification:
   Mark scripts as active, deferred, stale, or internal so future QA does not
   capture evidence for excluded top-level routes.

3. Component dependency map:
   Identify excluded components that are still imported by active modules before
   any removal proposal.

4. Docs archive candidate list:
   List superseded GUI docs and generated wireframe reports for later user
   approval. Do not archive in the same slice.

## Guardrails

- No cleanup slice may delete source until an issue names the candidate files,
  expected dependency impact, tests, and rollback path.
- No screenshot is acceptance evidence unless the live
  `/api/v1/platform/navigation` response matches the current UI phase.
- Integration Mapping remains reserved for its dedicated workstream.
- `OTM_RESOURCES/` and generated outputs stay protected.
