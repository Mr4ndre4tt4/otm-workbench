# GUI Operational List Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-operational-list-patterns`  
**Scope:** compact operational lists for blockers, artifacts, and evidence rows.

## 1. Purpose

`ArtifactList` and `BlockerPanel` are shared UI kit patterns for compact
operational rows that appear around module actions, generated files, evidence,
and blockers.

They centralize artifact row and blocker row markup so module views do not own
raw `artifact-list`, `artifact-list-item`, `blocker-list`, `blocker-item`, or
`blockers-panel` classes.

## 2. Ownership Boundary

`ArtifactList` owns:

```text
- artifact-list container markup
- artifact-list-item row markup
- title/subtitle/meta placement
- optional action versus status placement
```

`BlockerPanel` owns:

```text
- blockers-panel section markup
- blocker-list and blocker-item row markup
- BLOCKED versus READY status chip
- empty blocker state
```

Module views own:

```text
- mapping backend artifacts, evidence, or blockers into UI props
- download action callbacks
- backend-provided codes, messages, status, and metadata
```

## 3. Backend Ownership

These components do not decide whether a blocker exists, whether an artifact is
downloadable, or whether evidence is client-safe. Those decisions remain in the
backend contracts.

## 4. Required Behavior

```text
1. Use ArtifactList for compact artifact/evidence rows with metadata.
2. Use BlockerPanel for blocker summaries and blocker empty state.
3. Keep raw artifact/blocker classes inside ui/components.tsx.
4. Use OperationalPanel around ArtifactList when loading and empty behavior is
   tied to a backend collection.
```

## 5. Guardrails

```text
frontend/src/ui/components.test.tsx
frontend/tests/operationalListPatternContract.test.ts
```

The tests verify rendering and prevent module views from recreating raw
artifact or blocker list markup.
