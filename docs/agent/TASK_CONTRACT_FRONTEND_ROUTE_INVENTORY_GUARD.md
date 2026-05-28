# Task Contract: Frontend Route Inventory Guard

## Objective

Create a durable inventory and regression guard for the current UI phase route
surface before any source cleanup or route deletion.

## Original User Request

Continue to the next roadmap step.

## Interpreted Scope

- Follow the roadmap lane for frontend cleanup/current-phase navigation
  pruning.
- Inventory current frontend route components and classify their status.
- Add a frontend route guard test proving excluded top-level routes stay
  unavailable unless the backend navigation contract exposes them.
- Update validation and handoff documentation.

## Out Of Scope

- Removing source files.
- Deleting route components.
- Changing visible navigation.
- Integration Mapping implementation changes.
- Browser screenshots; this slice does not intentionally change UI behavior.

## Allowed Files Or Areas

- `frontend/src/app/routes/WorkbenchRoute.test.tsx`
- `docs/agent/FRONTEND_ROUTE_INVENTORY.md`
- `docs/agent/TASK_CONTRACT_FRONTEND_ROUTE_INVENTORY_GUARD.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

## Protected Files Or Areas

- Integration Mapping implementation files.
- Backend module behavior, except reading existing navigation tests.
- Raw `OTM_RESOURCES/` content.

## Acceptance Criteria

- Route inventory documents active, internal/deferred, and developer-only
  frontend surfaces.
- Tests prove excluded top-level routes such as Catalog, Evidence, Admin, and
  Developer Tools do not render from direct URL access without backend-owned
  navigation.
- Backend navigation tests still prove the sidebar module set matches the
  current UI phase.

## Validation Plan

- `python -m pytest tests/test_modules_navigation.py -q`
- `npm test -- src/app/routes/WorkbenchRoute.test.tsx src/app/shell/SidebarNav.test.tsx`
- `git diff --check`

## Risks

- Frontend files for excluded surfaces still exist. That is deliberate for this
  slice; deletion needs a separate cleanup plan with route and test impact.
- Integration Mapping is reserved for its separate workstream; it remains listed
  as active but should not be edited here.

## Challenge Notes

The previous UI-staleness incident was caused by trusting screenshots without a
fresh backend navigation gate. A route inventory guard is safer than immediate
deletion because it documents current exposure before code cleanup.

## Decision

Proceed with inventory documentation and guard tests only.
