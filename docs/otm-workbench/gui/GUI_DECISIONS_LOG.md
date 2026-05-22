# GUI Decisions Log

**Status:** active  
**Branch:** `codex/gui-decision-log`  
**Scope:** durable GUI/frontend architecture decisions for OTM Workbench.

## 1. Purpose

This log records decisions that affect the GUI architecture, design system,
frontend boundaries, and future desktop path.

Use this log when a choice should remain stable across modules, branches, or
future GUI implementations.

## 2. Decision Format

Each decision should include:

```text
ID:
Status: Proposed | Accepted | Superseded
Date:
Decision:
Reason:
Frontend impact:
Backend ownership:
Tests or guardrails:
Supersedes:
```

## 3. Decisions

### GUI-DEC-001

```text
ID: GUI-DEC-001
Status: Accepted
Date: 2026-05-21
Decision: Build the first GUI as a browser-first React + TypeScript + Vite application.
Reason: This gives the fastest usable workbench while preserving the option for a future desktop wrapper.
Frontend impact: The first GUI runs as a web app and keeps desktop-specific calls out of module screens.
Backend ownership: Backend contracts remain the source of truth for behavior and module data.
Tests or guardrails: React boundary, CSS entrypoint, CSS layer ownership, and contract index tests.
Supersedes: None.
```

### GUI-DEC-002

```text
ID: GUI-DEC-002
Status: Accepted
Date: 2026-05-21
Decision: Keep navigation, module visibility, permissions, lifecycle, actions, jobs, artifacts, evidence, active context, and user preferences backend-owned.
Reason: The GUI must be replaceable by a future frontend or desktop shell without duplicating business rules.
Frontend impact: Frontend renders contracts and owns layout/interaction only.
Backend ownership: Backend owns all behavioral decisions listed in the decision.
Tests or guardrails: Module navigation, action pattern, readiness panel, context summary, context switcher, and preference controls contracts.
Supersedes: None.
```

### GUI-DEC-003

```text
ID: GUI-DEC-003
Status: Accepted
Date: 2026-05-21
Decision: Use shared UI kit and shell components before adding module-specific visual patterns.
Reason: MVP0/MVP1 modules should feel like one product and should not create per-module UI dialects.
Frontend impact: Components such as PageHeader, StatePanel, FeedbackMessage, ArtifactList, BlockerPanel, ModuleObjectList, ModuleWorkspaceLayout, ModuleWorkspaceSide, SelectedObjectPanel, DetailList, MetricGrid, OperationalPanel, StatusChip, Button, ActivityRow, ContextSummary, ContextSwitcher, ReadinessPanel, and PreferenceControls are governed patterns.
Backend ownership: Shared components consume backend-owned data and actions without owning lifecycle or permission rules.
Tests or guardrails: Pattern contract tests plus GUI_CONTRACT_INDEX.md.
Supersedes: None.
```

### GUI-DEC-004

```text
ID: GUI-DEC-004
Status: Accepted
Date: 2026-05-21
Decision: Light mode is the default, with dark and system theme modes available through backend-owned user preferences.
Reason: Light mode is the safest operational default, while dark/system options are required from the start to preserve visual consistency and user preference tracking.
Frontend impact: The shell applies data-theme, data-density, and data-sidebar from backend preference data.
Backend ownership: Backend persists theme_mode, density, sidebar_mode, and follow_system_theme.
Tests or guardrails: Preference controls, CSS layer ownership, theme token, density token, sidebar token, and responsive token checks.
Supersedes: None.
```

### GUI-DEC-005

```text
ID: GUI-DEC-005
Status: Accepted
Date: 2026-05-21
Decision: Future desktop support should prefer Tauri first, with Electron only if required.
Reason: The product should support local heavier processing later while keeping the current web GUI and backend contracts reusable.
Frontend impact: Desktop APIs must stay behind platform/desktop adapters and out of module screens.
Backend ownership: Backend/local services own heavy processing, repositories, jobs, and synchronization contracts.
Tests or guardrails: React boundary contract and frontend architecture documentation.
Supersedes: None.
```

### GUI-DEC-006

```text
ID: GUI-DEC-006
Status: Accepted
Date: 2026-05-21
Decision: Keep Lucide as the MVP1 implementation icon family while evaluating Iconly only as a system-wide Figma/design pilot.
Reason: Lucide is already integrated in React, fits the operational workbench tone, works with currentColor across light/dark tokens, and avoids a premature product-wide icon migration before license and coverage review.
Frontend impact: App and module code continue using Lucide through shared components and shell patterns. No module may mix in a different icon family without an approved exception.
Backend ownership: Backend may provide icon_key metadata later, but the frontend maps those keys through governed shared components.
Tests or guardrails: GUI_DESIGN_SYSTEM_HANDOFF.md, GUI_CONTRACT_INDEX.md, GUI_EXCEPTIONS_REGISTER.md, Button/IconButton pattern tests.
Supersedes: None.
```

### GUI-DEC-007

```text
ID: GUI-DEC-007
Status: Accepted
Date: 2026-05-21
Decision: Complex module screens must use staged workflow storytelling instead of stacking disconnected authoring panels.
Reason: Users need to understand the operational sequence of modules such as Integration Mapping Studio; showing systems, definitions, payloads, rules, and lists at once creates noise and weakens the product model.
Frontend impact: Complex screens render one primary operational stage at a time, with side panels reserved for selected-object context and backend-owned actions.
Backend ownership: The staged UI must not invent lifecycle gates; backend contracts remain the source of truth for readiness, validation, permissions, artifacts, jobs, and evidence.
Tests or guardrails: GUI_STAGED_WORKFLOW_PATTERN_CONTRACT.md and AppFunctionalIntegrationMapping.test.tsx.
Supersedes: None.
```

### GUI-DEC-008

```text
ID: GUI-DEC-008
Status: Accepted
Date: 2026-05-21
Decision: Every module route must choose one primary experience pattern before adding forms, panels, or custom interactions.
Reason: Module screens need a clear operational story; adding independent panels without a chosen pattern creates dense, disconnected workflows and weakens consistency.
Frontend impact: New module work must start from Module Overview, Object List/Detail, Staged Workflow, Tabbed Detail, Review Queue, Operational Surface, or a documented exception.
Backend ownership: Pattern selection does not move lifecycle, permission, readiness, validation, action, artifact, job, evidence, audit, or preference decisions into the frontend.
Tests or guardrails: GUI_MODULE_EXPERIENCE_ARCHITECTURE.md, GUI_IMPLEMENTATION_CHECKLIST.md, GUI_CONTRACT_INDEX.md, and functional QA journey updates.
Supersedes: None.
```

### GUI-DEC-009

```text
ID: GUI-DEC-009
Status: Accepted
Date: 2026-05-22
Decision: A module is not complete until it satisfies the cross-module completion acceptance contract, including authoring/configuration when applicable, generated artifact parity, durable backend-owned state, negative tests, out-of-order UI/browser QA, security/client-data checks, and documented residual risks.
Reason: First functional slices prove a narrow workflow, but operational OTM modules need stronger acceptance before we call them complete.
Frontend impact: Module docs and Linear must distinguish First functional slice done, MVP workflow done, and Module complete. GUI screens must support recovery from realistic human behavior, not only the happy path.
Backend ownership: Backend remains authoritative for validation, lifecycle, readiness, generated artifacts, evidence, jobs, permissions, and blocked reasons.
Tests or guardrails: GUI_MODULE_COMPLETION_ACCEPTANCE_CONTRACT.md, GUI_FUNCTIONAL_QA_JOURNEYS.md, GUI_IMPLEMENTATION_CHECKLIST.md, and guiModuleExperienceArchitectureContract.test.ts.
Supersedes: None.
```

## 4. Change Rule

Do not silently replace accepted GUI decisions. Add a new decision with
`Supersedes:` filled in, then update affected contracts and tests.
