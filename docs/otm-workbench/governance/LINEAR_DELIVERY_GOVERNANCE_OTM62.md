# Linear Delivery Governance OTM-62

**Status:** active  
**Date:** 2026-05-21  
**Linear:** `OTM-62`  
**Scope:** project visibility and delivery board upkeep for OTM Workbench.

## 1. Purpose

Linear is the project visibility layer.

Repo docs remain the source of durable technical detail. Linear should make the
work understandable at a glance: what is active, what is done, what is blocked,
what is next, and where the repo evidence lives.

## 2. Core Rule

Use one Linear issue per coherent delivery slice.

Do not create one issue per commit, typo fix, screenshot, or tiny doc edit.
Small commits should roll up into the issue that owns the slice.

## 3. When To Create An Issue

Create or update a Linear issue when work has one of these shapes:

```text
- module implementation slice
- backend contract or DB model slice
- GUI screen or shared component slice
- QA/visual evidence slice
- integration/hardening slice
- roadmap/spec intake slice
- governance or delivery-board cleanup slice
```

If the work is only a small correction inside an already-active slice, comment
on the existing issue instead.

## 4. Required Issue Fields

Every meaningful delivery issue should include:

```text
- clear title
- branch or PR reference when available
- scope
- delivered files or contracts
- validation commands/results
- client-data safety note when screenshots, fixtures, payloads, docs, or test
  data are involved
- residual risk or follow-up note
```

## 5. Status Rules

Use statuses this way:

```text
Todo
  Work is known but not currently being executed.

In Progress
  Work is actively being changed, validated, or reconciled.

Done
  Repo artifact exists when needed, validation is recorded, PR/comment is
  updated when relevant, and residual risk is explicit.
```

Do not leave issues In Progress after their scope has been superseded. Mark
them Done with a superseded/completed note pointing to the follow-up evidence.

For module work, distinguish issue completion from module completion:

```text
First functional slice done
  The issue delivered one validated story.

MVP workflow done
  The issue delivered the principal happy path plus obvious blocked/error
  states.

Module complete
  The module satisfies GUI_MODULE_COMPLETION_ACCEPTANCE_CONTRACT.md, including
  authoring/configuration where applicable, generated artifact parity, durable
  state, negative tests, out-of-order UI QA, security/client-data checks, and
  documented residual risks.
```

Do not close a broad module umbrella as complete just because a child delivery
slice is Done.

## 6. Comment Cadence

Add a Linear comment when:

```text
- a meaningful commit is pushed
- a visual QA or browser fallback result is captured
- a blocker appears or is removed
- an issue is closed by a different follow-up issue
- a broad parent issue receives a child completion review
```

Avoid commenting for every small local edit.

## 7. Parent And Child Pattern

Use parent-like umbrella issues for broad concerns:

```text
- GUI foundation integration
- visual QA and accessibility pass
- module roadmap group
- governance and delivery board upkeep
```

Use child-like delivery issues for the concrete artifact:

```text
- OTM-80 component gallery visual QA evidence
- OTM-81 recurring GUI QA matrix
- OTM-82 Rates completion review
- OTM-83 shared operational panels completion review
- OTM-84 GUI QA/accessibility completion review
```

If Linear parent-child links are not maintained directly, include the parent
issue id in the child description and add a parent comment.

## 8. Repo Docs Versus Linear

Use repo docs for durable detail:

```text
- design specs
- backend contracts
- data model decisions
- GUI contracts
- QA matrices and completion reviews
- residual risk lists
```

Use Linear for visibility:

```text
- current status
- links to repo docs
- validation summary
- PR/branch reference
- next action
```

Do not paste large specs into Linear when a repo doc exists.

## 9. PR Update Rule

For PR-backed work, update the PR when:

```text
- a delivery slice is completed
- validation totals change materially
- browser/visual QA evidence is added
- scope changes from implementation to governance/reconciliation
- a major umbrella issue is closed
```

The PR comment should mention the Linear issue, commit hash, files added, and
validation result.

## 10. Client Data Rule

Any issue or comment involving examples, payloads, screenshots, generated files,
or browser evidence must state whether the data is synthetic/client-safe.

Do not add real client names, identifiers, local customer paths, CNPJ, CPF,
secrets, raw production payloads, or customer screenshots to Linear or repo
docs.

## 11. Current GUI Cleanup Baseline

As of 2026-05-21, the current GUI cleanup trail is reconciled:

```text
OTM-58 Done - Rates GUI MVP completion review
OTM-59 Done - shared operational panels completion review
OTM-60 Done - GUI QA/accessibility pass completion review
OTM-65 Done - superseded by component gallery evidence
OTM-77 Done - shell/Project Cockpit visual QA evidence
OTM-78 Done - Rates visual QA evidence
OTM-79 Done - Integration Mapping visual QA evidence
OTM-80 Done - Component Gallery visual QA evidence
OTM-81 Done - recurring GUI accessibility QA matrix
OTM-82 Done - Rates completion review record
OTM-83 Done - operational panels completion review record
OTM-84 Done - QA/accessibility completion review record
```

## 12. Acceptance Criteria

OTM-62 is complete when:

```text
- this governance doc exists in repo
- README links to it
- Linear OTM-62 is updated with this doc and current policy
- PR #181 is commented with the governance completion note
- validation passes for the doc contract
```
