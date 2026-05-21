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
Frontend impact: Components such as PageHeader, StatePanel, ModuleObjectList, ModuleWorkspaceLayout, ModuleWorkspaceSide, SelectedObjectPanel, DetailList, MetricGrid, OperationalPanel, StatusChip, Button, ActivityRow, ContextSummary, ContextSwitcher, ReadinessPanel, and PreferenceControls are governed patterns.
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

## 4. Change Rule

Do not silently replace accepted GUI decisions. Add a new decision with
`Supersedes:` filled in, then update affected contracts and tests.
