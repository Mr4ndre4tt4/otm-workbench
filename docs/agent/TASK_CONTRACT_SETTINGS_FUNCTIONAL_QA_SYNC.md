# Task Contract: Settings Functional QA Sync

**Date:** 2026-05-28
**Status:** implementation complete

## Objective

Align the functional Settings/Admin frontend QA test with the current UI phase
decision that Settings owns setup/access policy work and separate Admin Console
/ Jobs is not a top-level acceptance target.

## Original User Request

The user asked to continue with the next roadmap step after closing context
segregation foundation.

## Interpreted Scope

- Revalidate GitHub issue #185.
- Update the stale functional Admin test so it exercises the current Settings
  route, Settings navigation label, scope authority, role/user/grant setup, and
  access-policy binding behavior.
- Preserve jobs/audit as loaded empty supporting panels only; do not treat them
  as current-phase acceptance criteria.
- Close #185 if validation passes.

## Out Of Scope

- Reintroducing Admin Console or Jobs as top-level modules.
- Implementing new Settings product behavior.
- Browser QA rerun; existing browser evidence remains the accepted visual
  evidence for this closure, and this slice updates automated functional QA.
- Integration Mapping work.

## Allowed Files Or Areas

- `frontend/src/app/AppFunctionalAdmin.test.tsx`
- `docs/agent/TASK_CONTRACT_SETTINGS_FUNCTIONAL_QA_SYNC.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

## Protected Files Or Areas

- Integration Mapping files.
- `OTM_RESOURCES/`
- `outputs/`
- backend models and routes.

## Acceptance Criteria

- Functional Admin/Settings QA targets `/settings` and backend-owned Settings
  navigation.
- The test validates scope authority, role/user authoring, grant binding,
  access-policy authoring, and return-to-Cockpit recovery link.
- The test does not require `Admin Console` heading or top-level Admin Console
  navigation.
- Targeted backend/frontend Settings validation passes.
- GitHub #185 is updated with the validation evidence.

## Validation Plan

```powershell
npm run qa:functional:admin
npm test -- src/app/App.test.tsx -t "Settings"
python -m pytest tests/test_operational_context.py -q
npm run build
git diff --check -- frontend/src/app/AppFunctionalAdmin.test.tsx
```

## Risks

- The component file is still named `AdminConsoleView`; this remains an
  accepted non-blocking cleanup item, not a reason to keep #185 open.
- The legacy browser script still references Admin Console and should be
  updated in a later browser-QA cleanup slice before it is used as fresh
  acceptance evidence.

## Decision

Proceed with the automated QA sync and close #185 after validation.
