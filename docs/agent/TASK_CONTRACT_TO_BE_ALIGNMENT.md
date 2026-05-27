# To-Be Alignment Task Contract

**Date:** 2026-05-27
**Status:** active planning slice

## Objective

Consolidate the generated mockups, wireframes, diagrams, module specs, Figma
deep-flow boards, and user-approved delivery direction into the repository
documentation, then start the implementation planning path from the current
solution toward the To-Be product.

## Original User Request

The user asked to consolidate the mockups, wireframes, diagrams, specs, flows,
and Figma work into documentation, then begin planning the solution adaptation
to the To-Be state. The requested sequence is:

1. clean the current frontend and remove or hide modules that will not be
   attacked now;
2. implement client/domain and environment segregation so data can be isolated;
3. continue the Settings module until it is complete;
4. continue Cockpit until it is complete;
5. then continue Rates, Assets, Master Data, Integration, and Order Release;
6. define thoughtful test scenarios and create valid synthetic test files
   (`csv`, `xslt`, `pdf`, `docx`, `md`, `xml`, `json`, and others when needed);
7. use the local Data Dictionary and official Oracle documentation whenever
   OTM behavior, dependencies, CSV shape, XML shape, or table semantics are
   uncertain.

## Interpreted Scope

This slice is documentation and planning only. It updates the active source of
truth so future implementation can proceed safely. It does not remove frontend
routes, alter backend persistence, generate fixture files, or create commits.

## Out Of Scope

- Source-code cleanup.
- Route removal or module deletion.
- Database migrations.
- Fixture file generation.
- GitHub branch/PR creation.
- Linear issue creation without a confirmed project/team target.
- Archiving or deleting existing documentation.

## Allowed Files Or Areas

- `docs/agent/`
- `docs/agent/figma-wireframes/`
- `docs/otm-workbench/README.md`

## Protected Files Or Areas

- `frontend/`
- `src/`
- `tests/`
- `OTM_RESOURCES/`
- generated outputs and local databases

## Acceptance Criteria

- The active Figma source is corrected to the `OTM Workbench - Complete
  Solution Mockup`.
- The seven new deep-flow boards are documented as the active To-Be UX input.
- The module delivery order is recorded.
- The first implementation move is documented as frontend cleanup/hiding of
  out-of-current-phase modules, not deletion.
- Settings is documented as the first module to finish after context
  segregation.
- Cockpit remains a context selector, accelerator launcher, Public View entry,
  and project-info hub.
- Every module delivery requires revalidation against its desired outcome.
- The test and fixture strategy explicitly requires valid synthetic files,
  large files where useful, and Oracle/Data Dictionary validation for OTM
  uncertainty.

## Validation Plan

- Review updated docs for consistency.
- Confirm no source-code files were changed.
- Run `git diff --check`.
- Run targeted `rg` checks for stale active-Figma references.
- Review `git status --short`.

## Risks

- The current frontend still contains top-level routes for modules that are now
  out of current UI phase.
- Existing tests and browser scripts reference out-of-current-phase modules and
  must be classified before cleanup.
- Data segregation touches backend models, APIs, frontend context, tests, and
  fixtures; implementing it without a staged plan risks partial isolation.
- Test fixtures can become unrealistic if they are not validated against the
  Data Dictionary and official Oracle documentation.

## Challenge Notes

Frontend cleanup should start by hiding or disabling navigation exposure and
classifying code paths. Deleting source code should come only after inventory,
replacement coverage, and explicit approval.

## Decision

Proceed with documentation consolidation and To-Be planning. Defer code changes,
fixture generation, Linear/GitHub delivery records, and cleanup execution to
subsequent approved implementation slices.
