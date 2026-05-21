# GUI Design System Handoff

**Status:** delivered
**Branch:** `codex/gui-design-system-handoff`
**Linear:** `OTM-68`
**Scope:** Figma handoff path, icon-family evaluation, and design-system governance.

## 1. Purpose

This document defines how the current OTM Workbench GUI foundation should move
into a reusable design-system handoff without changing product behavior or
forking visual language by module.

The handoff source of truth is the implemented GUI foundation:

```text
frontend/src/styles.css
frontend/src/ui/tokens/
frontend/src/ui/components.tsx
frontend/src/ui/components/
frontend/src/app/shell/
frontend/src/app/routes/ComponentGalleryRoute.tsx
docs/otm-workbench/gui/GUI_COMPONENT_GALLERY_PLAN.md
```

## 2. Current Implementation Baseline

The current GUI is a browser-first React + TypeScript + Vite application with:

```text
- backend-owned navigation, active context, preferences, actions, artifacts,
  evidence, jobs, lifecycle, and validation decisions
- shared shell components
- shared UI kit barrel at frontend/src/ui/components.tsx
- internal UI kit ownership files under frontend/src/ui/components/
- CSS token files for theme, density, sidebar, and responsive behavior
- internal component gallery at /__gui/component-gallery
```

The Figma handoff should mirror this baseline. It should not invent alternate
module layouts, alternate palettes, or frontend-owned lifecycle rules.

## 3. Figma Foundation Structure

When a Figma file is created or updated, use this page structure:

```text
00 Cover and Governance
01 Foundations - Color, Type, Spacing, Radius, Shadow
02 Theme Modes - Light, Dark, System Notes
03 Shell - WorkbenchShell, Sidebar, Topbar, Preferences
04 Components - Buttons, IconButton, StatusChip, StatePanel, FeedbackMessage
05 Module Workspace - PageHeader, MetricGrid, ModuleWorkspaceLayout
06 Lists and Panels - ModuleObjectList, SelectedObjectPanel, DetailList
07 Operational - OperationalPanel, ArtifactList, BlockerPanel, ActivityRow
08 Forms and Context - LoginPanel, ContextSummary, ContextSwitcher, ReadinessPanel
09 Module Screens - Rates, Catalog, Load Plan, Assets, Evidence, Master Data,
   Order Release Generator, Integration Mapping
10 Exceptions and Future Patterns
```

Each page should show:

```text
- light mode default
- dark mode variant where relevant
- compact density where layout changes
- collapsed sidebar where shell changes
- loading, empty, error, blocked, disabled, read-only, success, warning, danger
- synthetic-only content
```

## 4. Token Handoff

The current code tokens are semantic CSS variables:

```text
--bg
--surface
--surface-subtle
--text
--muted
--border
--accent
--accent-strong
--success
--warning
--danger
--shadow
```

Figma variables should be named semantically, not by raw hex value:

```text
color/background/default
color/surface/default
color/surface/subtle
color/text/default
color/text/muted
color/border/default
color/action/default
color/action/strong
color/status/success
color/status/warning
color/status/danger
effect/shadow/default
```

The source of truth for actual values remains code until a formal token sync
workflow exists. Figma may mirror tokens, but it must not silently redefine
them.

## 5. Component Handoff

Figma components should map to the public GUI contracts, not internal
implementation files.

| Figma Component | Code Source | Notes |
|---|---|---|
| Button | `Button` | Primary, secondary, disabled. |
| IconButton | `IconButton` | Requires accessible label in code and tooltip/title in design notes. |
| StatusChip | `StatusChip` | Status semantics remain backend-owned. |
| StatePanel | `StatePanel` | Loading/unavailable now; future variants stay shared. |
| FeedbackMessage | `FeedbackMessage` | Inline success/error only. |
| PageHeader | `PageHeader` | Module title, label, description, backend actions. |
| MetricGrid | `MetricGrid` | Operational metrics, not decorative dashboard cards. |
| ModuleWorkspaceLayout | `ModuleWorkspaceLayout` | Standard object/detail workspace. |
| ModuleObjectList | `ModuleObjectList` | Selectable work queue/list. |
| SelectedObjectPanel | `SelectedObjectPanel` | Selected object identity and metadata. |
| DetailList | `DetailList` | Compact field/table/mapping rows. |
| OperationalPanel | `OperationalPanel` | Jobs, artifacts, evidence, operational collections. |
| ArtifactList | `ArtifactList` | Compact artifacts/evidence rows. |
| BlockerPanel | `BlockerPanel` | Backend-owned blockers. |
| ActivityRow | `ActivityRow` | Recent jobs/evidence/activity summaries. |

## 6. Icon Family Decision

Current implementation default:

```text
Lucide
```

Recommendation for MVP1:

```text
Keep Lucide as the implementation icon family.
```

Reasons:

```text
- already installed and integrated in React
- simple stroke icons fit the operational workbench tone
- accessible names are handled through shared IconButton labels
- works across light/dark modes through currentColor/token styling
- low migration cost and good enough coverage for shell/preference/status needs
```

Iconly V3.0 / Iconly Pro Community can be evaluated as a Figma/design pilot,
but should not replace Lucide in code until these criteria are checked:

```text
- license permits the intended product, repository, client, and handoff usage
- icon coverage matches backend action/icon_key needs
- variants work in light and dark modes without per-module overrides
- React integration is straightforward or SVG export governance is clear
- accessibility labels remain code-owned through IconButton/ActionBar
- desktop wrapper usage is allowed
- the whole system migrates together instead of mixing families per module
```

No module may choose a different icon family independently. A module-specific
icon departure requires an entry in `GUI_EXCEPTIONS_REGISTER.md`.

## 7. Figma Pilot Scope

If Iconly is piloted, limit the first pilot to:

```text
- theme controls: light, dark, system
- density control
- sidebar collapse/expand
- generic action: run, approve, download, upload, refresh
- status/severity: ready, blocked, warning, error, success
```

Do not pilot with client-specific payloads, real customer names, real
identifiers, or screenshots from customer data.

## 8. Handoff Rules

```text
1. Code contracts remain authoritative for behavior.
2. Figma mirrors tokens and components; it does not create new lifecycle rules.
3. Component names in Figma should match code contract names.
4. New visual variants require a code contract or documented exception.
5. Use synthetic content only.
6. Keep light mode as default.
7. Every dark mode component must use token variables, not manual recoloring.
8. Do not mix Lucide, Iconly, or any other family per module.
```

## 9. License Review Rule

Before any icon pack, Figma community asset, exported SVG set, or paid design
asset becomes part of the product handoff, run a dedicated license and coverage
review:

```text
- intended product usage
- repository storage rights
- customer/client handoff rights
- desktop wrapper redistribution rights
- commercial usage limits
- attribution requirements
- coverage against backend action/icon_key needs
```

Do not copy external icons into the repository or ship them in the product until
that review is documented. Figma may reference candidate icon families for
evaluation, but implementation remains on Lucide for MVP1.

## 10. Acceptance

This handoff is accepted when:

```text
- Lucide remains the MVP1 implementation default
- Iconly is treated as an optional system-wide pilot, not a module choice
- Figma page structure is defined
- token/component mapping is documented
- backend ownership remains explicit
- no real client data is introduced
```
