# Assets Acceptance Checklist

**Status:** accepted for current delivery cycle
**Date:** 2026-05-28
**Version issue:** `https://github.com/Mr4ndre4tt4/otm-workbench/issues/195`
**Acceptance issue:** `https://github.com/Mr4ndre4tt4/otm-workbench/issues/197`

## Scope Reviewed

Source:

- `docs/otm-workbench/gui/GUI_ASSETS_LIBRARY_CONSOLIDATED_SPEC.md`
- Assets task contracts under `docs/agent/TASK_CONTRACT_ASSETS_*.md`
- Assets backend tests
- Assets functional frontend tests
- Assets browser QA evidence

Current-cycle accepted scope:

- `/assets` hub
- `/assets/library` searchable library
- `/assets/new` create route
- `/assets/:assetId` detail route
- `/assets/:assetId/edit` metadata route
- `/assets/:assetId/versions`
- `/assets/:assetId/versions/new`
- `/assets/:assetId/links`
- `/assets/:assetId/archive`
- `/assets/classifications`
- `/assets/classifications/new`
- `/assets/classifications/:classificationId/edit`

## Acceptance Criteria

| Criterion | Status | Evidence |
|---|---|---|
| `/assets` explains library health without hosting full lifecycle. | Accepted | Hub route test and browser QA. |
| Asset rows open route-level detail pages with `Back`. | Accepted | Row actions and detail route tests. |
| Create, edit, upload, links, classifications, and archive have route-level task boundaries. | Accepted | Functional tests and browser QA route journey. |
| Asset search supports backend-owned metadata fields and operators. | Accepted | Search API/UI tests, linked target type, and target OTM version slices. |
| Classification authoring is separated from asset creation. | Accepted | Classification route tests and create route test. |
| Archived asset blockers and disabled reasons come from backend contracts. | Accepted | Available-action and archived-state functional/browser coverage. |
| Artifact/evidence link target safety remains backend-owned. | Accepted | Browser QA covers client-safe artifact/evidence target flow. |
| Guarded downloads do not expose local file paths. | Accepted | Download endpoint and browser download coverage. |
| Functional QA covers happy, negative, out-of-order, and route recovery paths. | Accepted for current cycle | Browser QA covers create/edit/version/link/download/archive/switch/reset/guards. |
| No real client data appears in docs, UI fixtures, screenshots, or tests. | Accepted | Synthetic-only fixture review in task contracts and QA evidence. |

## Validation Evidence

Latest Assets validation from #196:

```text
Focused backend target OTM version test: failed before implementation, then 2 passed.
Assets backend suite: 50 passed.
Focused frontend Assets journey: failed before UI control, then 1 passed / 12 skipped.
Assets functional suite: 13 passed.
Frontend build: passed with existing Vite large chunk warning.
Alembic head: c1f4a8e7d9b2.
Browser QA: passed.
```

Browser QA freshness evidence:

```text
Backend:  http://127.0.0.1:8025
Frontend: http://127.0.0.1:5204
Database: var/qa-assets-target-otm-version.db
Navigation IDs: master_data, home, rates, load_plan, assets,
  order_release_generator, integration_mapping, settings
```

## Accepted Deferrals

The following are not blockers for the current Assets cycle:

- route-optimized aggregate detail endpoint;
- archive impact preview endpoint before commit;
- BATCH and CHECKLIST link target lookup;
- official taxonomy validation for `target_otm_version`;
- restore/deprecate lifecycle variants beyond archive;
- create-with-file shortcut.

## Backlog Issues

- #198 `[Backlog]: Assets route-optimized detail and archive impact contracts`
- #199 `[Backlog]: Assets backend-owned batch and checklist link targets`
- #200 `[Backlog]: Assets target OTM version taxonomy validation`

## Completion Decision

Assets Library is accepted for the current delivery cycle. The module now solves
the core governed reusable-asset workflow: find, create, inspect, edit,
version, link, download, classify, and archive assets with backend-owned
validation and route-level recovery.

## Recommended Next Step

Move to the next approved module slice after closing `v0.3-assets-stabilization`.
Given the current roadmap, start Master Data / Data Factory foundation unless
the user prioritizes another non-Integration-Mapping module.
