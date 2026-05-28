# Assets Acceptance Create Route Plan

## Goal

Make `/assets/new` a dedicated create route and stop mixing classification authoring with asset creation.

## Steps

- [x] Add failing functional tests for `/assets/new` and classification separation.
- [x] Implement the route-level create screen.
- [x] Remove classification authoring from asset creation workflow.
- [x] Update browser QA to create classifications only through classification routes.
- [x] Run focused tests, full Assets functional tests, build, browser QA, and diff checks.
- [x] Update handoff and validation docs.
- [x] Commit and push the slice.

## Scope Guard

Do not add backend search/operator work in this slice, and do not stage `OTM_RESOURCES/` or `outputs/`.
