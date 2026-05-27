# Context Segregation Foundation Task Contract

**Date:** 2026-05-27
**Status:** active implementation slice

## Objective

Plan and start the client/domain, environment, and visibility/access-policy
segregation foundation before continuing Settings and module completion work.

## Original User Request

The user asked to continue the To-Be adaptation sequence after Figma
consolidation and frontend cleanup. The requested sequence prioritizes
frontend cleanup, then domain/environment segregation, then finishing Settings,
Cockpit, Rates, Assets, Master Data, Integration, and Order Release.

## Interpreted Scope

This slice inventories the current backend scope posture, creates an
implementation plan for enforcing operational data segregation across modules,
and adds the first reusable backend scope utility with behavior-lock tests. It
does not change database schema or retrofit module routes yet.

## Out Of Scope

- Applying migrations.
- Refactoring module operational queries.
- Creating Settings UI flows.
- Creating large fixture files.
- Updating Linear or opening a GitHub PR.
- Consulting Oracle documentation for specific table dependencies; that is
  required during module fixture and validation slices.

## Allowed Files Or Areas

- `docs/agent/`
- `docs/superpowers/plans/`
- `src/otm_workbench/platform/scoping.py`
- small platform helper reuse in `src/otm_workbench/platform/routes.py`
- `tests/test_operational_scope.py`
- documentation control records such as decision log, handoff, and inventory

## Protected Files Or Areas

- `OTM_RESOURCES/`
- application schema and module route code
- generated artifacts and local databases

## Acceptance Criteria

- Current context capabilities are summarized from code.
- Scope gaps are classified by module/entity family.
- A staged implementation plan exists with tests, data migration approach, and
  module order.
- Backend scope resolution has behavior-lock tests for Public View, normal
  private context, `DBA` wildcard domains, required private scope, and initial
  SQLAlchemy filtering.
- Existing active-context behavior remains compatible.
- Public View and `DBA` visibility behavior are explicitly preserved.
- Next implementation slice is small enough to execute with TDD.

## Validation Plan

- Run targeted backend tests for operational scope and active context.
- Run `git diff --check`.
- Review `git status --short`.

## Risks

- Some existing records are intentionally global reference/catalog data. A
  blanket scope migration would corrupt shared technical metadata.
- Order Release, Integration, and Master Data have several child tables where
  scope should be inherited from a parent record instead of duplicated.
- Public View must remain explicit; it cannot be treated as null project,
  null environment, or unrestricted access.

## Decision

Proceed with a small TDD implementation of scope resolution and reusable query
filtering first. Production schema changes and module route retrofits should
start only after the model ledger is explicit.
