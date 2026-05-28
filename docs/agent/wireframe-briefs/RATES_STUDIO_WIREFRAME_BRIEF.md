# Michelangelo Wireframe Brief - Rates Studio

**Status:** ready for Figma wireframe pass after user scope approval
**Date:** 2026-05-26
**Source scope review:** `docs/agent/module-scope/RATES_STUDIO_SCOPE_REVIEW.md`

## 1. Review Context

Screen/flow type:
Tariff/rate batch lifecycle and export workspace.

Primary user task:
Create or inspect a rate batch, resolve validation issues, approve when ready,
export artifacts, and hand off to Load Plan.

User profile:
Rates consultant, functional lead, approver.

Task criticality:
High. Incorrect approval or export can create invalid tariff artifacts.

Input reviewed:
Rates Studio consolidated spec and scope review.

Evidence source:
Repository documentation only. No live UI reviewed.

Assumptions:
Backend owns validation, approval readiness, artifact metadata, and Load Plan
handoff.

## 2. Archetypes

- data workspace;
- workflow/detail;
- critical approval;
- artifact/library manager;
- issue review.

## 3. Route Inventory For Wireframes

```text
/rates
/rates/batches
/rates/batches/new
/rates/batches/:batchId
/rates/batches/:batchId/stage
/rates/batches/:batchId/tables/:tableName
/rates/batches/:batchId/issues
/rates/batches/:batchId/csv-preview
/rates/batches/:batchId/export
/rates/batches/:batchId/approve
/rates/batches/:batchId/artifacts
/rates/batches/:batchId/evidence
/rates/batches/:batchId/load-plan
```

## 4. UX Findings To Design Around

ID:
RATE-UX-01

Severity:
P1 High

Category:
Workflow sequencing and gating

Where:
Batch lifecycle routes.

Evidence:
Approval and export are lifecycle actions with backend readiness and
capability requirements.

Problem:
Showing approve/export as list-row actions can hide the review context.

User impact:
Users may approve or export without seeing blockers, evidence, or readiness.

Recommendation:
Use dedicated approval and export review routes.

Implementation hint:
Show issue summary, validation state, artifact readiness, capability, and
confirmation on the route before action.

Acceptance criteria:
Approval/export cannot be visually confused with lightweight row actions.

---

ID:
RATE-UX-02

Severity:
P2 Medium

Category:
Table/data usability

Where:
Batch library and staged tables.

Evidence:
The ledger identifies unbounded recent lists and dense single-page panels as
cleanup risks.

Problem:
Large rate batches and noisy lists can hide the selected object and issue
counts.

User impact:
Slower inspection and higher chance of selecting the wrong batch/table.

Recommendation:
Use stable filters, selected-row state, row caps/pagination, and explicit issue
counts.

Implementation hint:
Render batch and table lists as compact dense rows with visible selected state.

Acceptance criteria:
The selected batch/table remains obvious after filtering or navigation.

## 5. Required Wireframe States

- no batches;
- batch created but not validated;
- invalid table/column;
- validation blockers;
- CSV preview ready;
- export blocked;
- approval blocked;
- approved batch;
- Load Plan handoff ready;
- artifact download blocked.

## 6. Wireframe Acceptance Criteria

- Batch lifecycle is route-level and stateful.
- Validation issues are grouped by table/rule.
- Approval and export include review summaries.
- Data Dictionary and schema guidance are clearly distinct.
- No real client tariff data appears.

## 7. External Validation Recommended

After Figma:

- Michelangelo review for approval safety;
- route recovery QA plan;
- artifact parity checklist against Rates specs.
