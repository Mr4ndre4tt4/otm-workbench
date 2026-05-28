# Assets Detail Actions Cleanup Plan

## Goal

Make the asset detail route action bar match the consolidated spec.

## Steps

- [x] Add failing functional assertions for detail route actions.
- [x] Implement action label/link/button cleanup.
- [x] Update browser QA to exercise the detail download action.
- [x] Run focused tests, full Assets tests, build, browser QA, and diff checks.
- [x] Update validation and handoff docs.
- [x] Commit and push the slice.

## Scope Guard

Do not add backend endpoints or the `/assets/:assetId/download` route in this slice.
