# Michelangelo Wireframe Brief - Load Plan / Cutover

**Status:** ready for Figma wireframe pass after user scope approval
**Date:** 2026-05-26
**Source scope review:** `docs/agent/module-scope/LOAD_PLAN_CUTOVER_SCOPE_REVIEW.md`

## 1. Review Context

Screen/flow type:
Package lifecycle, review queue, readiness, and governed cutover handoff.

Primary user task:
Take packages from source modules through review, CSVUTIL, sequence, readiness,
exports, go/no-go, and handoff.

User profile:
Cutover lead, functional consultant, project lead.

Task criticality:
Very high. Incorrect handoff can move unready packages into cutover.

Input reviewed:
Load Plan / Cutover consolidated spec and scope review.

Evidence source:
Repository documentation only. No live UI reviewed.

Assumptions:
Backend owns package readiness, sequence, blockers, evidence, and handoff
eligibility.

## 2. Archetypes

- critical operation;
- workflow/detail;
- review queue;
- artifact/export manager;
- readiness dashboard.

## 3. Route Inventory For Wireframes

```text
/load-plan
/load-plan/packages
/load-plan/packages/:packageId
/load-plan/packages/:packageId/checklist
/load-plan/packages/:packageId/readiness
/load-plan/packages/:packageId/csvutil
/load-plan/packages/:packageId/zip-review
/load-plan/packages/:packageId/sequence
/load-plan/packages/:packageId/exports
/load-plan/packages/:packageId/go-no-go
/load-plan/packages/:packageId/handoff
```

## 4. UX Findings To Design Around

ID:
LP-UX-01

Severity:
P0 Blocker

Category:
Safety for critical actions

Where:
Go/no-go and handoff.

Evidence:
The spec says cutover is governed and handoff depends on backend eligibility.

Problem:
A handoff action without a review route can hide blockers or evidence gaps.

User impact:
Unready packages may be treated as ready for cutover.

Recommendation:
Wireframe handoff as a critical review route with blocker summary, evidence
requirements, eligibility, and confirmation.

Implementation hint:
Use `ConfirmationReview`, `BlockerSummary`, and backend-owned eligibility.

Acceptance criteria:
Handoff cannot appear available unless backend eligibility is shown as true.

---

ID:
LP-UX-02

Severity:
P1 High

Category:
Information architecture

Where:
Load Plan hub and package detail.

Evidence:
The spec warns against putting the entire cutover journey on one page.

Problem:
CSVUTIL, ZIP review, sequence, readiness, exports, and handoff can overload a
single screen.

User impact:
Users may miss the next required step or act out of order.

Recommendation:
Use package detail as a route index and move each major operation to a
route-level screen.

Acceptance criteria:
The hub and package detail remain scannable and every operation has a route.

## 5. Required Wireframe States

- no packages;
- package imported but not reviewed;
- checklist incomplete;
- ZIP analysis warnings;
- review queue item unresolved;
- readiness blocked;
- sequence generated;
- export ready;
- go/no-go blocked;
- handoff ineligible;
- handoff committed.

## 6. Wireframe Acceptance Criteria

- Package is the primary object.
- Cutover remains inside Load Plan.
- Every critical action has a review screen.
- Blockers and evidence requirements are visible before action.
- No real client package data or local paths appear.

## 7. External Validation Recommended

After Figma:

- Michelangelo review for critical operation safety;
- route recovery QA plan;
- out-of-order cutover journey checklist.
