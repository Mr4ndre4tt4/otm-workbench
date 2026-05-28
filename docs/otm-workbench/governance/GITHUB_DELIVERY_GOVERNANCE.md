# GitHub Delivery Governance

**Status:** active
**Date:** 2026-05-27
**Replaces:** active Linear delivery-board usage for the current project phase.

## Purpose

GitHub is the active operational delivery layer for OTM Workbench. Repository
docs and code remain the durable source of truth. GitHub Issues, Pull Requests,
Actions, labels, milestones, and optional CodeRabbit review provide delivery
visibility close to the code.

Linear is historical/paused unless the user explicitly reactivates it.

## Operating Model

Use one GitHub Issue per coherent delivery slice. Use one Pull Request per
reviewable implementation or governance checkpoint.

Each delivery slice should have:

- an outcome-based issue title;
- source docs linked in the issue;
- a PR linked to the issue;
- CI results from GitHub Actions;
- CodeRabbit review status when the slice is broad, risky, or review-heavy;
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

When GitHub milestones are not available from the current tool context, create
one version-tracking issue and link child delivery issues from it. The version
issue should state:

- delivery intent;
- included modules or governance controls;
- linked issues and PRs;
- validation gates;
- deferred work.

Recommended version naming:

```text
v0.3-assets-stabilization
v0.4-master-data-foundation
v0.5-order-release-hardening
```

Avoid broad names such as `next`, `misc`, or `cleanup` unless the issue body
defines a tight boundary.

## Issue Cadence

Create or update issues more frequently than commits are pushed:

- one issue per coherent delivery slice;
- one parent/version issue per related group of slices;
- update the issue when the task contract is accepted, implementation starts,
  validation passes, or a deferral is discovered;
- split an issue when the implementation naturally becomes two independent
  reviewable commits.

Do not let more than one meaningful local slice accumulate without either:

- an open GitHub issue;
- a PR comment naming the pending slice; or
- a handoff capsule explaining why GitHub was deferred.

## Commit Granularity

Prefer small commits tied to a single task contract or validation checkpoint.
Good commit units are:

- one backend contract plus focused tests;
- one frontend route/control plus functional and browser QA updates;
- one governance/process update;
- one documentation-only correction.

Avoid commits that mix unrelated module behavior, governance, generated
artifacts, and local workspace cleanup. When the workspace contains parallel
work, stage by file and verify `git diff --cached --name-status` before every
commit.

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

## CodeRabbit Review

CodeRabbit is available as an assistive reviewer. Use it for broad PRs,
security-sensitive work, CI/workflow changes, governance changes, and module
implementation slices where a second review pass is valuable.

Current policy:

- CodeRabbit is recommended, not mandatory.
- Do not make it branch-protection-required yet.
- Do not implement findings blindly.
- Valid findings should become commits, GitHub comments, issues, or documented
  deferrals.
- Draft PR auto-review is disabled in `.coderabbit.yaml` to avoid noisy early
  feedback.

Detailed policy:

- `docs/otm-workbench/governance/CODERABBIT_REVIEW_GOVERNANCE.md`

## Linear Pause Rule

Do not require Linear updates for new slices. Historical docs may still mention
Linear issue IDs as evidence. When touching an active doc, prefer GitHub Issues
and PRs for new tracking references.

If Linear is reactivated later, record that decision in:

- `docs/agent/DECISION_LOG.md`;
- `docs/agent/DELIVERY_PIPELINE.md`;
- `docs/agent/RISK_REGISTER.md`;
- `AGENTS.md`.
