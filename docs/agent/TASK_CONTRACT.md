# Governance Reorganization Task Contract

**Date:** 2026-05-26
**Status:** supporting historical slice

## Objective

Create the first Solon governance baseline for OTM Workbench so the project can
be reorganized in phases before more module redesign or implementation work.

## Original User Request

The user asked to reorganize the project in stages:

- reorganize project governance;
- recover the original scope of each module;
- validate and update that scope in the new governance structure;
- structure next steps;
- later, use each module spec with Michelangelo to create wireframes;
- after validated wireframes and mockups, create the application plan;
- first application step should clean unnecessary code, modules, and screens;
- then run structured module development with tests, acceptance, docs, and
  orchestrated software process.

## Interpreted Scope

This slice creates the governance baseline only. It does not redesign screens,
change product behavior, create Penpot frames, move files, delete code, or
archive documents.

## Out Of Scope

- Code cleanup or route removal.
- Source code refactors.
- Penpot wireframe creation.
- GitHub delivery updates.
- Archiving or deleting files.
- Changing module implementation order after this baseline without a recorded
  decision.

## Allowed Files Or Areas

- `docs/agent/`
- `AGENTS.md`
- `docs/otm-workbench/README.md`

## Protected Files Or Areas

- `src/`
- `frontend/`
- `tests/`
- `migrations/`
- `OTM_RESOURCES/`
- `output/`
- existing GUI/module specs except for links or references approved later

## Acceptance Criteria

- A short governance entry layer exists under `docs/agent/`.
- The current project direction is captured.
- The initial module scope ledger exists.
- The recovery plan is reversible and does not delete or move files.
- The roadmap separates governance, scope recovery, Figma wireframes, cleanup,
  and module development. The current visual consolidation target is now Figma
  for the limited UI phase.
- The delivery pipeline defines how future module work moves from spec to
  wireframe to implementation.
- Risks, decisions, and handoff are recorded.
- Root entry docs point future agents to `docs/agent/`.

## Validation Plan

- Confirm all new docs are present.
- Confirm no source code files changed.
- Run `git diff --check`.
- Review `git status --short`.

## Risks

- There are many existing GUI docs; the first inventory may be category-level
  rather than final file-by-file classification.
- Some old docs may contain valid historical evidence and should not be archived
  until their replacement path is explicit.
- `OTM_RESOURCES/` is currently untracked; it must remain protected.

## Challenge Notes

The requested cleanup should not start with deletion. The safe path is:
inventory, classify, approve archive candidates, then move files reversibly to
`archive/YYYY-MM-DD/` only after confirmation.

## Decision

Proceed with a documentation-only governance baseline. Defer destructive
cleanup, Figma work, and source-code changes to later approved slices.
