# Chat Continuity Workflow

**Status:** active
**Date:** 2026-05-27

## Purpose

Chat context can be incomplete after a handoff, model compaction, new thread, or
tool/plugin transition. The repository docs and code are the durable memory.
This workflow prevents a new chat from acting on partial memory and requires
the previous chat to leave enough evidence for safe continuation.

## Failure Modes

Known context-loss possibilities:

- conversation summary omits a recent correction, rollback, or user decision;
- screenshots or QA evidence come from a stale local runtime;
- the next chat sees only part of the dirty worktree and assumes all changes
  are intentional;
- plugin/tool state is not carried over, including browser sessions, Figma
  selections, GitHub context, historical Linear context, or local server
  processes;
- the prior chat updated code but not `HANDOFF.md`, `VALIDATION_REPORT.md`,
  `DECISION_LOG.md`, or `RISK_REGISTER.md`;
- a temporary implementation attempt remains in the worktree without being
  documented as partial, reverted, or blocked;
- the next chat follows an older roadmap/spec instead of the current scope;
- the new chat accepts inherited memory without checking source-of-truth docs.

## Previous Chat Exit Gate

Before ending a work session, the acting agent must update the handoff when any
meaningful analysis, implementation, validation, or scope decision occurred.
The handoff must include:

- current objective and whether it is complete, partial, blocked, or deferred;
- files intentionally changed in the session;
- files touched only temporarily and then reverted or abandoned;
- exact validation commands run and results;
- validation that was not run and why;
- screenshots/evidence paths, including runtime freshness result when browser
  QA was used;
- open risks, assumptions, and unresolved user decisions;
- recommended next step and the first docs/files the next chat should read;
- any local server, browser, plugin, Figma, GitHub, or reactivated Linear state
  that matters for continuation.

If code was changed but the exit gate cannot be completed, the agent must mark
the session as incomplete in `docs/agent/HANDOFF.md` and explain the missing
validation. Do not leave a silent partial state.

## New Chat Intake Gate

At the start of a new chat, before implementing or making product claims, the
agent must rebuild context from durable sources:

1. read `AGENTS.md`;
2. read `docs/agent/HANDOFF.md`, starting from the newest sections;
3. read `docs/agent/VALIDATION_REPORT.md`, starting from the newest sections;
4. read `docs/agent/DECISION_LOG.md` for decisions after the last known task;
5. read `docs/agent/RISK_REGISTER.md` for open risks relevant to the task;
6. read `docs/agent/CURRENT_SCOPE.md` and `docs/agent/DELIVERY_PIPELINE.md`;
7. run `git status --short` and treat unrelated changes as user-owned;
8. inspect the diff for files the task will touch before editing;
9. if browser QA or screenshots are involved, run the runtime freshness gate in
   `docs/agent/DELIVERY_PIPELINE.md`;
10. state the recovered current state briefly before proceeding.

The new chat must not rely on conversational memory alone when memory conflicts
with docs, tests, or code. The source of truth order is:

```text
user's latest instruction
-> repository code and tests
-> active docs under docs/agent/
-> external boards/tools only after verification
-> inherited chat memory
```

## Stop Conditions

Stop and ask for clarification or first repair the docs when:

- `HANDOFF.md` and the worktree disagree about what changed;
- the newest user instruction contradicts active scope docs;
- validation evidence references screenshots from a stale runtime;
- a changed file has no clear owner or relation to the task;
- a module appears complete in memory but not in validation/docs;
- required plugin/tool state cannot be reconstructed and affects correctness.

## Required Handoff Capsule

Every session that changes behavior, docs, tests, QA evidence, GitHub,
or design artifacts must leave this capsule in `docs/agent/HANDOFF.md`:

```text
## YYYY-MM-DD <Task Or Incident Name>

Status:
Scope:
Files intentionally changed:
Validation run:
Validation not run:
Evidence:
Open risks:
Next chat intake notes:
Recommended next step:
```

The capsule can be concise, but it must be specific enough for a new chat to
continue without relying on hidden conversation memory.
