# Assets Library Search UI Plan

## Goal

Connect the `/assets/library` frontend search surface to the backend-owned
search/operator/pagination contract.

## Steps

1. Add a failing functional test that expects text search fields, operators,
   page size, and backend query params.
2. Extend frontend asset filter types and query serialization.
3. Add compact operator/search controls to the existing Library panel.
4. Add basic pagination display and previous/next page actions.
5. Update browser QA to exercise the new search controls and capture evidence.
6. Run frontend functional tests, build, browser QA, and diff checks.
7. Update handoff and validation docs.
