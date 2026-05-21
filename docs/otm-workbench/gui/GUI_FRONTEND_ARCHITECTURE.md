# GUI Frontend Architecture

**Status:** proposed for review  
**Branch:** `codex/gui-frontend-architecture`  
**Scope:** frontend architecture, UI consistency, design system governance, and desktop-ready boundaries.

## 1. Decision

OTM Workbench should continue as a browser-first React application, designed so
a future desktop client can consume the same backend contracts without changing
module behavior.

The frontend must stay a renderer and interaction layer. The backend remains the
source of truth for navigation, permissions, lifecycle, user preferences,
actions, validation, jobs, artifacts, evidence, and OTM-specific decisions.

Recommended baseline:

```text
React + TypeScript + Vite
React Router
TanStack Query
Workbench UI Kit
CSS variables / design tokens
Vitest + Testing Library
Future desktop wrapper: Tauri first, Electron only if required
```

## 2. Product Direction

Visual direction:

```text
operational technical clean
```

The GUI should feel like a professional implementation workbench: dense enough
for repeated operational use, clear enough for functional users, and consistent
across modules.

Use cockpit/dev-tool treatments only where they help the work:

```text
jobs
evidence
logs
audit trail
validation issues
payload/schema inspection
mapping diagnostics
```

Avoid landing-page composition, decorative cards, one-off module palettes,
large marketing-style hero areas, and custom UI per module.

## 3. Ownership Boundary

### Backend Owns

```text
- navigation and module visibility
- module status and lifecycle
- user permissions and disabled action explanations
- available actions and action priority
- project/profile/environment/domain context
- user preferences
- validation decisions
- OTM table/dependency rules
- jobs and progress
- artifacts and downloads
- evidence, manifests, audit trail
- server-side pagination/filter/sort contracts when available
```

### Frontend Owns

```text
- layout composition
- visual hierarchy
- accessible interaction
- local selection state
- loading/empty/error/blocked/read-only states
- rendering backend-provided actions
- theme token application
- responsive behavior
- safe client-side affordances
```

The frontend must not duplicate validation, approval, cutover, upload, OTM
dependency, or lifecycle rules.

## 4. Application Layers

Target structure:

```text
frontend/src/
  app/
    App.tsx
    shell/
    routes/

  platform/
    api.ts
    hooks/
    types/
    auth/
    preferences/
    desktop/

  ui/
    tokens/
    base.css
    components.css
    layouts.css
    primitives/
    components/
    layouts/
    states/
    patterns/
    icons/

  modules/
    rates/
    catalog/
    load-plan/
    assets/
    evidence/
    master-data/
    order-release-generator/
    integration-mapping/
```

The current GUI has intentionally grown inside `App.tsx` while the first module
views were being proven. The next architecture step is extraction, not visual
reinvention.

## 5. Module Structure

Each module should follow the same shape:

```text
modules/{module-id}/
  routes.tsx
  hooks.ts
  types.ts
  pages/
  components/
  tests/
  README.md
```

Module-local components are allowed only when they are genuinely domain
specific. Reusable display patterns must move to `ui/`.

Examples:

```text
Reusable:
- ModuleObjectList
- SelectedObjectPanel
- DetailList
- MetricGrid
- StatusChip
- ActionBar
- StatePanel

Domain-specific:
- SchemaTree
- MappingTable
- CsvPreviewTable
- XmlPreview
- LoadSequenceView
- ValidationIssueQueue
```

## 6. Design Tokens

The design system should define semantic tokens instead of raw page colors.

Required token groups:

```text
color.background.*
color.surface.*
color.text.*
color.border.*
color.status.*
color.action.*
space.*
radius.*
shadow.*
font.*
zIndex.*
```

Status colors must be semantic:

```text
DRAFT / CREATED / REGISTERED -> neutral
RUNNING / IN_PROGRESS -> info
SUCCEEDED / APPROVED / READY -> success
WARNING / BLOCKED / NEEDS_REVIEW -> warning
FAILED / ERROR / REJECTED -> danger
ARCHIVED / CANCELLED -> muted
```

Pages and module components should consume tokens through shared classes or
component variants, not hardcoded color values.

## 7. Light And Dark Mode

Light mode remains the default.

Supported preference values:

```text
theme_mode: light | dark | system
density: comfortable | compact
sidebar_mode: expanded | collapsed
```

These preferences are backend-owned through:

```text
GET /api/v1/platform/user-preferences
PUT /api/v1/platform/user-preferences
```

The frontend applies preferences through root shell attributes:

```text
data-theme
data-density
data-sidebar
```

Dark mode must use explicit tokens. It should not rely on automatic inversion or
module-level overrides.

Icons must remain consistent across modes. The current Lucide set is acceptable
as an implementation default. Iconly or another family can be evaluated later,
but the decision should be system-wide, not per module.

## 8. Page Templates

Every backend-backed module should start from a shared page template.

### Module Overview

```text
PageHeader
MetricGrid
Primary object list or work queue
Selected object panel
Artifacts/evidence/jobs when supported
Backend-owned actions
```

### Object Detail

```text
Header with status
Summary fields
Tabs or detail sections
Validation
Artifacts
Evidence
Jobs
Audit
```

### Review Queue

```text
Severity
Category
Affected object
Backend recommendation
Decision/status
Evidence link
```

### Guided Flow

Use only when the backend exposes a step-based workflow. Wizard steps must
reflect backend gates.

## 9. Interaction States

Every reusable pattern must support:

```text
loading
empty
no results
error
blocked
disabled by permission
read-only
success
warning
danger
stale/degraded API
```

Disabled actions should show backend-provided reasons when available.

## 10. Desktop-Ready Boundary

The web app should not call desktop APIs from module screens.

Future desktop-specific functions belong behind adapters:

```text
platform/desktop/
  desktopApi.ts
  fileDialog.ts
  localProcess.ts
  localBackend.ts
```

Modules should call product-level services only. The same module screen should
work in:

```text
- browser against local FastAPI
- browser against remote backend
- Tauri desktop against local FastAPI
- future hybrid local/cloud setup
```

Heavy local engines can live behind backend/job contracts. Shared templates,
assets, artifacts, and collaborative metadata can later use cloud-backed
repositories without changing module UI contracts.

## 11. Extraction Roadmap

Recommended next architecture sequence:

```text
1. Split current App.tsx into shell, routing, preferences, and module views.
2. Move shared UI components into clearer ui/components and ui/patterns groups.
3. Move platform hooks/types into endpoint-oriented files.
4. Create modules/* folders for delivered views.
5. Introduce token files for theme, status, density, and layout.
6. Add component-level tests for shared UI patterns.
7. Add Storybook or an internal component gallery after tokens stabilize.
8. Add desktop adapter skeletons only when the first desktop use case appears.
```

This should be done incrementally. Do not pause module value delivery for a
large frontend rewrite.

## 12. Governance Rules

Before adding a new screen, component, or visual variant, answer:

```text
1. Is the data contract backend-owned?
2. Does an existing shared component cover this?
3. If not, is the new component reusable or domain-specific?
4. Does it support light and dark mode through tokens?
5. Does it support required interaction states?
6. Does it avoid real client data in tests/docs?
7. Does it expose only backend-authorized actions?
8. Does it work in browser now and desktop later?
```

Exceptions must be documented when a module needs a custom interaction.

## 13. Initial Exceptions To Allow

The following custom patterns are expected later and should be designed
deliberately:

```text
- Integration Mapping schema tree and mapping table
- XML/JSON payload preview with safe redaction
- CSVUtil/load package sequence viewer
- Validation issue queue
- Job timeline
- Evidence package explorer
- Coordinate Quality map/latlon diagnostics
```

These should still use shared tokens, shared states, and backend-owned action
contracts.

## 14. Acceptance Criteria

This architecture is accepted when:

```text
- frontend/backend ownership is explicit
- module UI consistency rules are clear
- light/dark/density preferences remain backend-owned
- desktop future is supported through adapters
- extraction roadmap is incremental
- custom interactions require documented exceptions
- no module needs to invent its own visual framework
```

## 15. Immediate Next Step After Review

After this document is reviewed, create an implementation plan for a frontend
architecture cleanup slice:

```text
- extract shell/preferences/routing from App.tsx
- create initial modules/* folders
- preserve existing UI behavior
- keep all existing tests green
- keep CSS entrypoint, CSS layer ownership, and React boundary contracts green
- add docs for the new folder ownership model
```
