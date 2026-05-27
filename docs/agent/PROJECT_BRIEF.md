# OTM Workbench Project Brief

**Status:** active governance baseline
**Date:** 2026-05-26

## Product

OTM Workbench is a local-first modular workbench for Oracle Transportation
Management implementation projects. It supports data preparation, validation,
evidence, integrations, cutover readiness, and controlled technical utilities.

The product is not a replacement for OTM. It is a preparation, validation,
artifact, evidence, and governance layer around OTM implementation work.

## Source Of Truth

The repository docs and code are the source of truth. GitHub Issues, Pull
Requests, and Actions are the active delivery visibility and review layer.
Linear is historical/paused unless explicitly reactivated. Browser screenshots,
tests, and generated evidence prove behavior.

## Current Delivery Mode

The project is moving from "continue adding module screens" to a governed
reorganization:

1. stabilize governance and documentation controls;
2. recover and validate the intended scope of each module;
3. create module wireframes from validated specs, not from the current UI;
4. validate wireframes and mockups;
5. promote the Complete Solution Mockup deep-flow boards as the To-Be visual
   reference;
6. clean unnecessary frontend exposure, modules, and screens;
7. implement client/domain and environment segregation;
8. restart structured module delivery from Settings and Cockpit.

## Stack

Backend:

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- SQLite
- Pytest

Frontend:

- React
- TypeScript
- Vite
- React Router
- React Query
- Vitest
- Playwright browser QA scripts

## Important Entry Points

- `AGENTS.md`
- `docs/agent/PROJECT_NORTH_STAR.md`
- `docs/agent/CURRENT_SCOPE.md`
- `docs/agent/ROADMAP.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/TO_BE_SOLUTION_ALIGNMENT_PLAN.md`
- `docs/agent/TEST_SCENARIO_FIXTURE_STRATEGY.md`
- `docs/otm-workbench/README.md`
- `docs/otm-workbench/engineering/HARNESS_ENGINEERING_PLAN.md`
- `docs/otm-workbench/gui/GUI_MODULE_ROADMAP_INDEX.md`

## Hard Rules

- Do not use real client data in docs, fixtures, screenshots, tests, or seeds.
- Keep backend-owned labels, icons, capabilities, actions, statuses,
  preferences, templates, and validation rules wherever practical.
- Keep operational workflows, authoring workflows, and quality utilities in
  separate route families unless a module spec explicitly says otherwise.
- Use route-level screens or deliberate modals for complex object details,
  edit, copy, delete/retire, and result inspection.
- Validate OTM table dependencies through the Data Dictionary and use official
  Oracle documentation for technical or functional uncertainty.
- For OTM CSVs, line 1 is table name, line 2 is columns, then values; if dates
  are present, emit the `exec alter session ...` date format line before
  values.
- Do not delete or archive files until the recovery plan is approved.

## Current Git Context

Current branch observed during intake:

```text
codex/master-data-catalog-redesign-evidence
```

Untracked local path observed:

```text
OTM_RESOURCES/
```

Treat `OTM_RESOURCES/` as protected local project material unless the user
explicitly asks otherwise.
