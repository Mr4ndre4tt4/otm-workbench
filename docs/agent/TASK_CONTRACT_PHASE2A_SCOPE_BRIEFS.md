# Phase 2A Scope Recovery And Wireframe Brief Task Contract

**Date:** 2026-05-26
**Status:** supporting historical slice

## Objective

Validate the first two module scope rows, Master Data / Data Factory and Catalog
Core, and prepare Michelangelo wireframe briefs for later visual work.

## Original User Request

The user approved continuing after the initial governance baseline. The agreed
next step was to review the module scope ledger module by module, starting with
Master Data / Data Factory and Catalog Core, before generating
wireframes.

## Interpreted Scope

This slice creates documentation only:

- module scope review for Master Data / Data Factory;
- module scope review for Catalog Core;
- Michelangelo wireframe brief for Master Data / Data Factory;
- Michelangelo wireframe brief for Catalog Core;
- updates to ledger, decisions, risks, handoff, and validation report.

## Out Of Scope

- Figma/Penpot frame creation.
- Code cleanup.
- Route removal.
- UI implementation.
- Backend/API changes.
- Linear/GitHub updates.
- Archiving docs.

## Allowed Files Or Areas

- `docs/agent/`

## Protected Files Or Areas

- `src/`
- `frontend/`
- `tests/`
- `migrations/`
- `OTM_RESOURCES/`
- `output/`
- existing module specs outside `docs/agent/`

## Acceptance Criteria

- Master Data / Data Factory has a scope review that records original intent,
  current evidence, validated target scope, cleanup watchlist, wireframe inputs,
  and open decisions.
- Catalog Core has the same.
- Both modules have Michelangelo wireframe briefs with task context,
  archetypes, route inventory, states, findings, and acceptance criteria.
- The module scope ledger links to these artifacts.
- Decisions, risks, handoff, and validation report are updated.
- `git diff --check` passes.

## Validation Plan

- Run `git diff --check`.
- Run `git status --short`.
- Confirm the four new review/brief docs exist.
- Do not run backend/frontend tests because this is documentation-only.

## Risks

- Marking a module "validated" too early could imply permission to clean or
  implement. This slice validates only for wireframe brief preparation.
- Catalog Core is shared infrastructure; its wireframe must not become a
  normal-user technical overload.
- Master Data has delivered UI slices; the wireframe work must still start from
  validated scope, not from copying the current implementation.

## Challenge Notes

No cleanup should occur until the user explicitly approves the module scope and
wireframes/mockups.

## Decision

Proceed with documentation-only Phase 2A scope review and wireframe briefs.
