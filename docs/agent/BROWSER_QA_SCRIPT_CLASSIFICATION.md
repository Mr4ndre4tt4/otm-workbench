# Browser QA Script Classification

**Status:** active governance map
**Date:** 2026-05-28
**GitHub issue:** #237

## Purpose

Classify browser QA scripts before future screenshots or cleanup work. A script
can remain in source without being valid current acceptance evidence.

Current browser evidence is valid only after the live backend
`/api/v1/platform/navigation` response exposes the current UI phase module IDs
and omits excluded top-level modules.

## Classification Terms

| Term | Meaning |
|---|---|
| Active | Valid for current-phase browser QA when its live navigation freshness gate passes. |
| Reserved | Valid only in the named dedicated workstream. |
| Internal | Retained for backend/internal diagnostics, not current top-level UI acceptance evidence. |
| Deferred | Retained for planned or experimental work, not current acceptance evidence. |
| Stale | Targets an excluded or absorbed top-level route and must not be used for current screenshots. |

## Script Map

| Script | Package command | Classification | Current evidence rule |
|---|---|---|---|
| `frontend/scripts/functional-shell-browser.mjs` | `qa:functional:shell:browser`, `qa:functional:browser` | Active | Valid for shell/Cockpit evidence only after its navigation freshness gate passes. |
| `frontend/scripts/functional-rates-browser.mjs` | `qa:functional:rates:browser` | Active | Valid for Rates evidence when the same runtime exposes current UI phase navigation. |
| `frontend/scripts/functional-assets-browser.mjs` | `qa:functional:assets:browser` | Active | Valid for Assets evidence; already checks excluded navigation IDs before screenshots. |
| `frontend/scripts/functional-load-plan-browser.mjs` | `qa:functional:load-plan:browser` | Active | Valid for Load Plan evidence when paired with a fresh current-phase runtime. |
| `frontend/scripts/functional-master-data-browser.mjs` | `qa:functional:master-data:browser` | Active | Valid for Master Data and in-module Quality Tools evidence. |
| `frontend/scripts/functional-order-release-browser.mjs` | `qa:functional:order-release:browser` | Active | Valid for Order Release evidence when paired with a fresh current-phase runtime. |
| `frontend/scripts/functional-integration-mapping-browser.mjs` | `qa:functional:integration-mapping:browser` | Reserved | Use only in the dedicated Integration Mapping workstream or with explicit user direction. |
| `frontend/scripts/chaos-browser.mjs` | `qa:chaos:browser` | Active / special | Valid only for controlled route-recovery or out-of-order workflow evidence after a fresh navigation gate. |
| `frontend/scripts/functional-catalog-browser.mjs` | `qa:functional:catalog:browser` | Internal | Retained for Catalog Core diagnostics; not valid current top-level UI acceptance evidence. |
| `frontend/scripts/functional-evidence-browser.mjs` | `qa:functional:evidence:browser` | Internal | Retained for Evidence Hub diagnostics; current evidence should be module-local. |
| `frontend/scripts/functional-admin-browser.mjs` | `qa:functional:admin:browser` | Stale | Targets `/admin`; current setup/access evidence belongs under Settings. |
| `frontend/scripts/functional-developer-tools-browser.mjs` | `qa:functional:developer-tools:browser` | Internal | Retained for diagnostics; not valid current top-level UI acceptance evidence. |
| `frontend/scripts/functional-coordinate-quality-browser.mjs` | `qa:functional:coordinate-quality:browser` | Stale | Coordinate Quality top-level exposure is absorbed into Master Data. |
| `frontend/scripts/functional-assistant-browser.mjs` | `qa:functional:assistant:browser` | Deferred | Assistant is not a current navigation module; do not use for current acceptance screenshots. |

## Screenshot Rules

- Do not use screenshots from stale, internal, deferred, or reserved scripts as
  current UI phase acceptance evidence.
- Before capturing any browser QA evidence, query
  `/api/v1/platform/navigation` on the same backend/session used by the browser.
- The valid current module IDs are `home`, `master_data`, `rates`,
  `load_plan`, `assets`, `order_release_generator`, `integration_mapping`, and
  `settings`.
- The backend response must omit `catalog`, `evidence`, `admin`, `dev_tools`,
  and `coordinate_quality` for current main UI screenshots.

## Safe Follow-Ups

- Add shared navigation freshness helpers to active browser scripts that do not
  already assert the current module ID set.
- Replace stale Admin browser evidence with a Settings-focused browser script
  only after a Settings implementation issue defines the expected workflow.
- Keep Catalog, Evidence Hub, and Developer Tools scripts available for
  internal diagnostics until a later removal issue names exact files and impact.
