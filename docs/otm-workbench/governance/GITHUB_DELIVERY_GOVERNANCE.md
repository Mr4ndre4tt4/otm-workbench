# GitHub Delivery Governance

**Status:** active
**Date:** 2026-05-27
**Replaces:** active Linear delivery-board usage for the current project phase.

## Purpose

GitHub is the active operational delivery layer for OTM Workbench. Repository
docs and code remain the durable source of truth. GitHub Issues, Pull Requests,
Actions, labels, and milestones provide delivery visibility close to the code.

Linear is historical/paused unless the user explicitly reactivates it.

## Operating Model

Use one GitHub Issue per coherent delivery slice. Use one Pull Request per
reviewable implementation or governance checkpoint.

Each delivery slice should have:

- an outcome-based issue title;
- source docs linked in the issue;
- a PR linked to the issue;
- CI results from GitHub Actions;
- validation evidence in the PR body or comments;
- docs, risk, and handoff updates when behavior or direction changes.

## Recommended Labels

Keep labels intentionally small:

- `scope`
- `frontend`
- `backend`
- `docs`
- `qa`
- `governance`
- `blocked`
- `scope-risk`

Do not create a large taxonomy unless the project outgrows this set.

## Milestones

Use milestones for phase-level grouping, not detailed planning:

- Governance Reset
- UI Phase Cleanup
- Context Segregation
- Settings
- Cockpit
- Rates
- Assets
- Master Data
- Integration
- Order Release

## Pull Request Rules

Every PR should answer:

- what changed;
- which module or governance control changed;
- which issue it resolves or advances;
- what validation was run;
- what remains out of scope;
- what risks or follow-ups remain.

For UI evidence, the PR must mention whether the runtime freshness gate was
checked before screenshots:

1. source navigation test;
2. live `/api/v1/platform/navigation` query on the same backend used by the
   browser;
3. visual confirmation that excluded top-level modules are absent.

## GitHub Actions

CI is the default confidence gate. The initial workflow runs:

- backend pytest suite;
- frontend Vitest suite;
- frontend production build.

Browser QA remains local/manual until the runtime and fixture story is stable
enough to automate reliably.

## Linear Pause Rule

Do not require Linear updates for new slices. Historical docs may still mention
Linear issue IDs as evidence. When touching an active doc, prefer GitHub Issues
and PRs for new tracking references.

If Linear is reactivated later, record that decision in:

- `docs/agent/DECISION_LOG.md`;
- `docs/agent/DELIVERY_PIPELINE.md`;
- `docs/agent/RISK_REGISTER.md`;
- `AGENTS.md`.
