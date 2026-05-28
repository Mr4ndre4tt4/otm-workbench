# Task Contract: Assets Acceptance Pass

## Objective

Complete GitHub issue #197 by revalidating Assets Library against the
consolidated spec and recording accepted scope, deferred scope, and backlog.

## Original User Request

Continue with the next step after implementing #196 in the Assets version train.

## Interpreted Scope

- Review `GUI_ASSETS_LIBRARY_CONSOLIDATED_SPEC.md` against the current Assets
  implementation and validation evidence.
- Produce an acceptance checklist/report.
- Create GitHub backlog issues for real follow-ups.
- Update GitHub/PR/handoff/validation records.

## Out Of Scope

- Implementing Integration Mapping.
- Adding new Assets product behavior unless a blocking P1 gap is discovered.
- Running full repository validation.
- Reopening already-accepted module scope.

## Allowed Files Or Areas

- `docs/agent/ASSETS_ACCEPTANCE_CHECKLIST_2026-05-28.md`
- `docs/agent/TASK_CONTRACT_ASSETS_ACCEPTANCE_PASS.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- GitHub issues #195 and #197-#200.

## Protected Files Or Areas

- `OTM_RESOURCES/`
- `outputs/`
- Integration Mapping code/docs unless explicitly requested.
- Workbench Assistant parallel work.

## Acceptance Criteria

- Assets acceptance checklist exists.
- Remaining backlog is listed with GitHub issue links.
- Validation evidence is named and scoped.
- PR #182 and issue #197 are updated.
- Handoff names the next recommended slice/module.

## Validation Plan

- Review consolidated Assets spec and current route/test evidence.
- Use latest Assets backend/frontend/build/browser QA evidence from #196.
- Run documentation diff/staged diff checks before commit.

## Risks

- Acceptance could be mistaken for completion of all future Assets ideas.
  Mitigation: checklist separates accepted current-cycle scope from backlog.
- Parallel dirty worktree could leak into this commit.
  Mitigation: stage only acceptance docs and staged-index handoff/validation.

## Decision

Proceed with a documentation-only acceptance pass and GitHub backlog closeout.
