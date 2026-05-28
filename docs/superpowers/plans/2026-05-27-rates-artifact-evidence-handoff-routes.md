# Rates Artifact Evidence Handoff Routes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add route-level Rates screens for artifacts, evidence, and Load Plan handoff.

**Architecture:** Extend the existing `RatesSummaryView` route-mode switch instead of creating a new route family. Reuse the current batch detail, artifacts, evidence, and generic backend action helpers so the UI remains backend-owned.

**Tech Stack:** React, React Router, TanStack Query, Vitest, Testing Library, FastAPI backend endpoints.

---

### Task 1: RED Test

**Files:**
- Modify: `frontend/src/app/AppFunctionalRates.test.tsx`

- [ ] Add assertions in the direct lifecycle route test for `Artifacts`,
  `Evidence`, and `Load Plan handoff`.
- [ ] Mock `/api/v1/modules/load-plan/packages/from-rates/batch_ready`.
- [ ] Run `npm test -- src/app/AppFunctionalRates.test.tsx` and confirm it
  fails because the route titles/panels do not exist yet.

### Task 2: Route Implementation

**Files:**
- Modify: `frontend/src/modules/rates/RatesSummaryView.tsx`

- [ ] Add `artifacts`, `evidence`, and `load-plan` to the recognized route
  suffixes.
- [ ] Add route titles/descriptions and route destination buttons.
- [ ] Render route-level artifact and evidence `OperationalPanel` instances.
- [ ] Render a Load Plan handoff panel with batch scope, catalog path,
  readiness counts, and a `Register Load Plan package` action.
- [ ] Invalidate Rates and Load Plan package queries after successful handoff.

### Task 3: Verification

**Files:**
- Modify: `docs/agent/VALIDATION_REPORT.md`
- Modify: `docs/agent/HANDOFF.md`

- [ ] Run `npm test -- src/app/AppFunctionalRates.test.tsx`.
- [ ] Run `npm run build`.
- [ ] Run browser QA against a local backend/frontend and capture a screenshot
  under `var/qa/`.
- [ ] Record the results and residual risks in the validation and handoff docs.
