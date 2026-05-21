# GUI Shared Operational Panels Completion Review OTM-59

**Status:** completed  
**Date:** 2026-05-21  
**Branch:** `codex/gui-foundation-integration-pr-plan`  
**Linear:** `OTM-59`  
**PR:** #181

## 1. Purpose

Close the shared module panels workstream for jobs, artifacts, evidence,
blockers, and operational activity rows.

This review records the shared GUI foundation that future modules should reuse
instead of creating module-local panels, artifact rows, blocker lists, or job
activity rows.

## 2. Delivered Shared Components

The operational surface foundation is delivered through:

```text
OperationalPanel
ArtifactList
BlockerPanel
ActivityRow
StatePanel
StatusChip
FeedbackMessage
Button
```

These components are exported from the shared UI kit and are available to module
views through `frontend/src/ui/components.tsx`.

## 3. Delivered Contracts

Supporting contracts:

```text
GUI_SHARED_OPERATIONAL_PANELS.md
GUI_OPERATIONAL_PANEL_PATTERN_CONTRACT.md
GUI_OPERATIONAL_LIST_PATTERN_CONTRACT.md
GUI_ACTIVITY_ROW_PATTERN_CONTRACT.md
GUI_MODULE_OPERATIONAL_SURFACES_CONTRACT.md
GUI_ACCESSIBILITY_QA_MATRIX.md
```

## 4. Current Consumers

Current module and shell consumers include:

```text
Project Cockpit recent jobs
Project Cockpit recent evidence
Rates Studio blockers
Rates Studio batch artifacts
Rates Studio batch evidence
Evidence Hub selected evidence references
Integration Mapping payload/schema operational metadata
Component Gallery synthetic operational examples
```

## 5. Backend Ownership

The shared components own rendering only.

Backend remains authoritative for:

```text
- whether artifacts exist
- whether an artifact can be downloaded
- whether evidence is client-safe
- job status and progress
- blocker codes and blocker messages
- disabled reasons
- lifecycle gates
- read-only or blocked state
- permission and capability decisions
```

Frontend module code may map backend payloads into display props, but it must
not infer operational truth from local UI state.

## 6. Guardrails

Static and component tests enforce the pattern:

```text
frontend/tests/guiModuleOperationalSurfacesContract.test.ts
frontend/tests/operationalPanelPatternContract.test.ts
frontend/tests/operationalListPatternContract.test.ts
frontend/tests/activityRowPatternContract.test.ts
frontend/tests/statePatternContract.test.ts
frontend/src/ui/components.test.tsx
frontend/tests/guiSharedOperationalPanelsCompletionReviewOtm59.test.ts
```

The guardrails prevent:

```text
- raw panel card markup in app/module screens
- raw artifact-list or blocker-list markup outside shared components
- raw activity-row markup outside ActivityRow
- OperationalPanel usage without accessible labels
- module-local replacements for shared operational surfaces
```

## 7. Client Data Guardrail

Operational examples and tests must use synthetic content only.

Do not render or add fixtures containing:

```text
- real client names
- real payload values
- real document identifiers
- local artifact file paths
- raw XML/JSON payload bodies
- CNPJ or CPF values
- secrets
```

## 8. Completion Criteria

OTM-59 is complete because:

```text
- shared operational panel/list/activity components exist
- current consumers use shared components
- backend ownership is documented
- module operational surface matrix is documented
- client-safe operational content rules are documented
- static tests enforce centralization and accessible labels
- future extensions have a documented path
```

## 9. Residual Risk

Future backend job/progress endpoints, artifact download contracts, Evidence
Hub download actions, import jobs, mapping preview jobs, or generated-file
workflows should extend these patterns rather than creating module-specific
copies.

When a module gains a new operational surface, update
`GUI_MODULE_OPERATIONAL_SURFACES_CONTRACT.md` and use
`GUI_ACCESSIBILITY_QA_MATRIX.md` for visual, keyboard, responsive, console, and
client-data-safe QA.
