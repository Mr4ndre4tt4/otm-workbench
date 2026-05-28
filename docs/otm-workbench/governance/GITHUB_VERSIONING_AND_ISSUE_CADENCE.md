# GitHub Versioning And Issue Cadence

**Status:** active
**Date:** 2026-05-28
**Tracking issue:** `https://github.com/Mr4ndre4tt4/otm-workbench/issues/194`

## Purpose

Keep delivery visible while the local workspace contains parallel workstreams.
GitHub should show what is being built before a large local batch accumulates.

Repository docs remain the durable source of truth. GitHub Issues, PRs,
Actions, and optional CodeRabbit review are the delivery visibility layer.

## Version Model

Use lightweight version trains for related slices.

Preferred:

- GitHub milestone when milestone management is available.

Fallback:

- one version-tracking issue with linked child issues.

Version names should be outcome-based:

```text
v0.3-assets-stabilization
v0.4-master-data-foundation
v0.5-order-release-hardening
```

Avoid broad buckets such as `next`, `misc`, or `cleanup` unless the issue body
defines a tight boundary.

## Issue Cadence

Create or update a GitHub Issue when:

- a task contract is created;
- implementation starts for a meaningful slice;
- a slice changes product behavior;
- validation passes or fails in a way that affects delivery;
- a follow-up is deferred;
- a new chat or parallel workstream needs a durable handoff point.

Use one issue per coherent delivery slice. Split an issue when the work becomes
two independent reviewable commits.

## Commit Cadence

Prefer small commits mapped to one of:

- backend/API contract plus focused tests;
- frontend route or control plus focused tests and QA script updates;
- documentation/governance update;
- validation or CI correction;
- generated artifact update with explicit evidence.

Before committing:

1. run `git status --short`;
2. stage only the intended files;
3. inspect `git diff --cached --name-status`;
4. run the relevant validation;
5. mention the issue number in the commit body or PR comment when useful.

## PR Cadence

For a long-lived PR, push small commits and add a PR comment after each
reviewable slice with:

- commit SHA;
- issue number;
- summary;
- validation run;
- deferred work;
- any runtime freshness evidence for browser QA.

## Workspace Safety

When unrelated local changes exist:

- do not use broad `git add .`;
- do not stage protected local folders such as `OTM_RESOURCES/` or `outputs/`;
- keep Integration Mapping changes in its dedicated workstream unless the user
  explicitly changes that boundary;
- record any reason GitHub issue updates were deferred in `HANDOFF.md`.
