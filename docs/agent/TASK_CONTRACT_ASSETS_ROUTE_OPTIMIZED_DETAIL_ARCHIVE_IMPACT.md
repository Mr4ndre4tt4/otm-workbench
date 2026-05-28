# Task Contract - Assets Detail And Archive Impact Contracts

**Date:** 2026-05-28
**GitHub issue:** #198
**Status:** in progress

## Objective

Add backend-owned Assets detail and archive impact contracts so route-level
screens can rely on server facts instead of frontend inference.

## Original User Request

Continue with the next roadmap step after Load Plan closeout.

## Interpreted Scope

- Add a route-optimized asset detail endpoint that consolidates asset metadata,
  current version, versions, links, available actions, and archive impact.
- Add an archive impact endpoint used before archive commit.
- Update the archive route UI to consume backend-owned archive impact facts.
- Preserve existing list/detail/archive endpoints.
- Add backend and focused frontend tests.

## Out Of Scope

- Full Assets visual redesign.
- Target lookup implementation for batches/checklists (#199).
- Target OTM version taxonomy validation (#200).
- Integration Mapping work.

## Allowed Files Or Areas

- `src/otm_workbench/modules/assets/`
- `tests/test_assets_library_assets.py`
- `frontend/src/platform/hooks/assets.ts`
- `frontend/src/platform/types/assets.ts`
- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- Assets docs under `docs/agent/`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- Integration Mapping files.
- Unrelated dirty workspace changes.

## Acceptance Criteria

- Detail endpoint returns asset, current version, versions, links, available
  actions, and archive impact.
- Archive impact endpoint returns eligibility, disabled reason, impacted
  version/link counts, linked target types, and actions that will be disabled.
- Archived assets report archive as disabled with backend-owned reason.
- Archive UI displays backend impact facts when available.
- Existing endpoints remain compatible.

## Validation Plan

- `python -m pytest tests/test_assets_library_assets.py -k "route_optimized_detail or archive_impact or archive_asset_preserves" -q`
- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "archives an asset on a direct route"`
- Broader focused Assets backend/frontend tests if implementation changes shared behavior.

## Risks

- Frontend could still infer impact if endpoint is unavailable; keep fallback
  only for compatibility and prefer backend facts on the archive route.
- Impact contract must not expose local file paths.

## Challenge Notes

This is not a mandate to redesign Assets now. The slice gives the route-level
archive/detail screens the backend-owned facts needed for that redesign.

## Decision

Proceed with additive endpoints and focused UI consumption in the archive route.
