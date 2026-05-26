# OTM Workbench Agent Map

This file is the short entry point for Codex or any future agent working in
this repository.

## Project Shape

- Product: OTM Workbench, a local-first modular workbench for Oracle
  Transportation Management implementation, data preparation, validation,
  evidence, integrations, and cutover support.
- Architecture: backend-first modular monolith with React/Vite frontend.
- Source of truth: repository docs and code. Linear is the visibility board.
- Current delivery mode: module by module, starting with Master Data / Data
  Factory redesign.

## Mandatory Rules

- Do not use real client data in docs, fixtures, screenshots, tests, or seeds.
- Prefer backend-owned labels, icons, capabilities, available actions, statuses,
  preferences, templates, and validation rules.
- Keep operational workflows, authoring workflows, and quality utilities on
  separate route families unless a module spec explicitly says otherwise.
- Complex object details, edit, copy, delete/retire, and result inspection must
  use a route-level screen or a deliberate modal with a visible return path.
- Always validate OTM table dependencies through the Data Dictionary and use
  official Oracle documentation for technical/functional uncertainty.
- For OTM CSVs, first line is table name, second line is columns, then values;
  if dates are present, emit the `exec alter session ...` date format line
  before values.
- Update docs, Linear, GitHub, tests, and QA evidence together when a delivery
  slice changes product behavior.

## Where To Start

1. Read `docs/otm-workbench/README.md`.
2. Read `docs/otm-workbench/engineering/HARNESS_ENGINEERING_PLAN.md`.
3. Read `docs/otm-workbench/gui/GUI_MODULE_ROADMAP_INDEX.md`.
4. For current UI/module work, read the active module spec. The current first
   priority is
   `docs/otm-workbench/gui/GUI_MASTER_DATA_DATA_FACTORY_REDESIGN_SPEC.md`.
5. Check `git status --short` before editing. Do not revert unrelated user
   changes.

## Completion Bar

A module is not complete just because it works technically. It is complete only
when it solves the real user problem clearly:

- backend/API contract exists and is tested;
- UI is clear and not overloaded;
- each click has an obvious destination;
- actions execute the expected backend behavior;
- browser QA covers happy, negative, out-of-order, and route recovery paths;
- screenshots/evidence are captured for meaningful states;
- module docs and Linear are current;
- changes are committed and pushed.
