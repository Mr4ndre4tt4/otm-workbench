# GUI Module Completion Acceptance Contract

**Status:** active
**Linear:** OTM-115 introduced the rule; applies to every module
**Scope:** cross-module definition of done for GUI + backend workflows.

## 1. Purpose

This contract prevents a first functional slice from being mistaken for a
complete module.

A module can have a delivered slice when one narrow workflow works. A module is
complete only when the workflow matches the real operational scope, exposes the
required authoring/configuration surfaces, generates import-ready artifacts, and
survives negative and out-of-order user behavior.

## 2. Completion Levels

Use these labels consistently in docs and Linear.

```text
First functional slice done
  One primary backend-backed story is implemented and validated.

MVP workflow done
  The main happy path plus obvious blocked/error paths are implemented.

Module complete
  The module satisfies its full module-specific acceptance criteria, including
  authoring, generated artifacts, negative tests, UI resilience, documentation,
  and security/client-data guardrails.
```

Do not mark a module as complete when only the first slice is done.

## 3. Universal Module Completion Criteria

Every module must satisfy these criteria before being called complete.

```text
1. Backend-first product truth
   Navigation, permissions, lifecycle, validation, readiness, artifact metadata,
   evidence, jobs, and blocked reasons come from backend contracts.

2. Real operational workflow
   The module performs the actual user job, not just a read-only inspection or
   polished placeholder. The workflow has a clear primary object, primary action,
   and return-state behavior.

3. Data dictionary and official-source validation
   When a module targets OTM tables, fields, CSVs, XMLs, statuses, references,
   or functional behavior, it validates against the local OTM Data Dictionary
   and records where Oracle official/help documentation or user confirmation was
   used for technical or functional ambiguity.

4. Import/export artifact parity
   Generated artifacts must match the target system format closely enough to be
   used operationally. For OTM CSVs this means table name on line 1, columns on
   line 2, `exec alter session ...` before data rows when date columns exist,
   then values. For XML/JSON/package outputs, the same module-specific parity
   standard must be documented and tested.

5. Authoring and configuration when applicable
   If the module creates reusable templates, mappings, checklists, payload
   definitions, assets, generators, or transformation logic, users must be able
   to author/version/publish those definitions through backend-owned contracts.

6. Friendly operator inputs
   User-facing fields may use helpful labels, grouping, and simplified workbook
   or form shapes, but the backend must persist the mapping from those fields to
   the exact OTM/API target fields.

7. One-to-many and fixed/default mapping when applicable
   Modules that transform user input into output records must support fixed
   values, default values, one input field feeding multiple target fields, and
   grouping multiple target tables/files from one logical user input where the
   module scope requires it.

8. Durable state and recovery
   A user can leave and return to the route without losing backend-owned objects.
   If session-only state remains, it is documented as a gap and the module is
   not complete.

9. Positive, negative, and out-of-order QA
   Tests cover happy path, invalid inputs, invalid lifecycle order, missing or
   mismatched files, repeated clicks, changing selections mid-flow, navigation
   away/back, blocked actions, and recovery from backend errors.

10. UI consistency and accessibility
    The screen uses shared shell/UI patterns, light/dark/system tokens, keyboard
    accessible controls, responsive layouts, and no disconnected stacked panels.

11. Client-data safety and security
    Fixtures, screenshots, generated artifacts, docs, logs, evidence, and Linear
    updates use synthetic/client-safe data only. Upload/download and generated
    artifact paths are guarded against local path leakage and unsafe content.

12. Linear and repo evidence
    Linear records delivered scope, validation commands, residual risk, and links
    to repo docs. Repo docs record the durable contract, tests, and completion
    review.
```

## 4. Required QA Matrix For Module Completion

Each module completion review must include:

```text
- backend pytest happy path
- backend pytest negative lifecycle/input cases
- frontend Vitest happy path
- frontend Vitest disabled/error/blocked states
- browser QA against local FastAPI + Vite with synthetic data
- route leave/return test
- repeated-click or duplicate-submit test for at least one mutating action
- selection-change/reset-state test for staged workflows
- generated artifact content test
- no real client data assertion where payloads/artifacts are serialized
- `git diff --check`
- lint/build or equivalent frontend validation when GUI changed
```

## 5. Master Data Example

Master Data is not complete until it supports:

```text
- template listing/discovery based on OTM Data Dictionary and official/help
  documentation where needed
- template workbook download
- user-filled workbook upload
- OTM CSV/ZIP export in exact CSVUTIL-compatible shape
- UI-driven template authoring from N OTM tables
- friendly labels for template fields
- grouping N OTM tables into user-facing workbook sheets/files
- fixed/default values
- one template field feeding N OTM output fields
- backend validation of target tables, fields, relationships, and lifecycle
- positive, negative, and out-of-order UI/browser QA
```

OTM-114 remains a first functional slice, not module completion. OTM-115 tracks
the true Master Data completion gap.

## 6. Completion Review Rule

Before a module is called complete, create or update a module completion review
document with:

```text
- module scope
- supported user stories
- backend contracts
- generated artifact parity evidence
- authoring/configuration coverage
- positive QA evidence
- negative QA evidence
- out-of-order UI behavior evidence
- security/client-data safety evidence
- known gaps
```

If any item is missing, use `First functional slice done` or `MVP workflow done`
instead of `Module complete`.
