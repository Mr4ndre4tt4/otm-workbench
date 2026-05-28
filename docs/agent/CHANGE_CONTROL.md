# Change Control

**Status:** active
**Date:** 2026-05-26

## Purpose

Change control keeps scope, roadmap, docs, and implementation aligned as the
project is reorganized.

## Change Types

Use one or more:

- scope change;
- roadmap change;
- delivery pipeline change;
- architecture change;
- priority change;
- documentation change;
- validation strategy change;
- feature boundary change;
- deprecation or replacement change;
- project north star change.

## Required Change Record

Every meaningful direction change should record:

```text
Date:
Change type:
Decision:
Reason:
Impacted docs:
Impacted code/tests:
Risks:
Validation:
Owner:
Status:
```

## GitHub Versioning Checkpoint

When a direction change affects delivery cadence, module order, or what counts
as a reviewable slice, record the change in GitHub as well as in repo docs:

- create or update a governance issue;
- link affected delivery issues or PR comments;
- decide whether the change belongs to an active version/milestone;
- keep commits focused enough that a future agent can map each commit to a task
  contract, issue, or validation checkpoint.

## Documentation Sync Checklist

Before a change is done, check:

- `docs/agent/PROJECT_NORTH_STAR.md`
- `docs/agent/CURRENT_SCOPE.md`
- `docs/agent/ROADMAP.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/CHANGE_CONTROL.md`
- `docs/agent/DECISION_LOG.md`
- `docs/agent/RISK_REGISTER.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`
- `docs/agent/DOCUMENT_INVENTORY.md`
- `AGENTS.md`

## Chat Continuity Rule

Any change that could be continued by a later chat must leave a handoff capsule
in `docs/agent/HANDOFF.md`. The capsule records status, intentional changes,
validation run, validation not run, evidence, open risks, and next-chat intake
notes. A new chat must run the intake gate in
`docs/agent/CHAT_CONTINUITY_WORKFLOW.md` before implementation or acceptance
claims.

## Archive Rule

Do not delete stale docs. Preferred process:

1. classify as superseded or archive-candidate;
2. identify replacement document;
3. ask for approval;
4. move to `archive/YYYY-MM-DD/deprecated-docs/`;
5. create or update `archive/YYYY-MM-DD/INDEX.md`;
6. update `DOCUMENT_INVENTORY.md`.

## Challenge Format

Use this format when a requested change increases confusion or risk:

```text
Concern:
Impact:
Recommended alternative:
Documents impacted:
Decision needed:
```
