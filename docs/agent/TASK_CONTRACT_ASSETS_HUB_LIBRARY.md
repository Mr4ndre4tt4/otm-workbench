# Task Contract: Assets Hub And Library Slice

**Status:** implemented local slice
**Date:** 2026-05-27

## Objective

Start Assets Library module completion against `11 / Assets Library Deep Flow`
by separating the `/assets` hub from the existing functional library workspace.

## Original User Request

Proceed to the next step with Solon, Michelangelo, Figma, GitHub, and Linear
context available.

## Interpreted Scope

- Treat the next approved module as Assets Library after Rates acceptance.
- Implement the first Assets slice from the consolidated spec:
  - `/assets` becomes a hub with library health and route entry points.
  - `/assets/library` preserves the existing backend-backed asset workflow as
    the temporary functional library route.
- Add focused React coverage for the route split.

## Out Of Scope

- Route-level asset detail, edit, versions, links, classifications, and archive
  extraction.
- Backend search metadata, operators, pagination, or new API contracts.
- Source deletion, route removal, or archive moves.
- Real client data or new non-synthetic fixtures.

## Allowed Files Or Areas

- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `frontend/src/app/routes/WorkbenchRoute.tsx` for compatibility fallback needed
  by browser QA when local backend summary lacks newer Cockpit groups.
- `frontend/scripts/functional-assets-browser.mjs`
- `docs/agent/`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- Backend Assets contracts unless the frontend route split proves impossible.
- Existing unrelated modified files.

## Acceptance Criteria

- `/assets` renders a hub, not the lifecycle workflow.
- The hub exposes visible route entries for library, create asset, and
  classifications.
- `/assets/library` still opens the existing functional workflow so current
  asset create/version/link/download/archive coverage remains intact.
- Tests prove the hub route and existing functional journey.

## Validation Plan

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "renders an Assets hub"`
- `npm test -- src/app/AppFunctionalAssets.test.tsx`
- `npm run build`
- `npm run qa:functional:assets:browser`
- Browser screenshot: `var/qa/assets-hub-library-route.png`

## Risks

- `/assets/new` and `/assets/classifications` are visible route entries before
  their dedicated route screens exist; they currently fall through to the
  existing Assets workspace and must be extracted in later slices.
- The existing `/assets/library` still contains more lifecycle behavior than
  the final spec allows. This is an intentional bridge to keep behavior stable.

## Challenge Notes

The slice does not claim Assets completion. It only starts the route-level
separation required by the consolidated spec and keeps the existing backend
workflow available until later slices move lifecycle tasks to dedicated routes.
The browser QA path also exposed an older local Cockpit summary contract, so a
defensive frontend fallback was added to avoid blocking route recovery before
Assets opens.

## Decision

Proceed with a narrow frontend route split and test update. Defer deeper
route extraction to the next Assets slice.
