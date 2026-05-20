# GUI Architecture Strategy Design

**Date:** 2026-05-20  
**Linear:** OTM-56  
**Status:** Draft for review  
**Scope:** architecture and visual-system strategy only; no frontend scaffold.

## 1. Decision Summary

The OTM Workbench GUI will be designed as a **web app first**, while remaining
**desktop-ready** from the first architecture decisions.

The first implementation target is a browser-based SPA. A future Windows
desktop app should be able to reuse the same UI, consume the same backend
contracts, and add desktop capabilities through platform adapters instead of
module-specific desktop calls.

The GUI is not the source of truth for business rules. The backend remains the
source of truth for:

```text
- navigation visibility
- permissions and capabilities
- active context
- lifecycle gates
- validation results
- job status
- artifact and evidence metadata
- user preferences
- local/cloud orchestration decisions
```

## 2. Approved Stack

The approved frontend stack is:

```text
React + TypeScript + Vite
React Router
TanStack Query
TanStack Table
React Hook Form
Zod
Radix/shadcn as the technical primitive base
Workbench UI Kit as the official product component layer
Vitest + Testing Library
Playwright
```

The rule is explicit: product modules use the **Workbench UI Kit**, not raw
third-party primitives directly. Radix/shadcn can exist underneath, but the
stable interface for OTM Workbench modules is the internal UI Kit.

## 3. Product Architecture

### 3.1 Target Shape

```text
Workbench GUI
  App Shell
  Module Routes
  Workbench UI Kit
  API Client
  Platform Adapters
    BrowserAdapter
    FutureDesktopAdapter

Backend API
  Platform services
  Modular domain APIs
  Jobs / artifacts / evidence
  User preferences
  Future orchestration for local/cloud execution

Future Local Runtime
  Heavy processing
  Local file handling
  Local cache
  Desktop-only integrations

Future Cloud Services
  Shared templates
  Shared assets/files
  Collaboration
  Sync
  Review/approval history
```

### 3.2 Browser First, Desktop Ready

MVP1 should run in the browser. The frontend architecture must still avoid
browser-only assumptions in product modules.

Examples:

```text
Do not call localStorage directly from feature modules.
Do not call window APIs directly from feature modules.
Do not spread download/file-picker logic across components.
Do not decide local/cloud execution from a button component.
```

Feature modules call product services. Product services use adapters.

## 4. Local-First And Cloud Collaboration Model

The long-term model is hybrid:

```text
Local:
- heavy processing
- large parsing/generation workloads
- local filesystem interactions
- offline-friendly cache where allowed
- desktop install/runtime capabilities

Cloud:
- shared file/template repositories
- shared assets library
- collaboration and review
- permissions and user/project/profile context
- cross-user evidence and history
- sync and backup
```

The GUI should not know whether a job ran locally or in a cloud worker unless
the backend exposes that as display metadata. The GUI asks for an operation;
the backend contract returns job, status, artifact, evidence, and blocker
metadata.

## 5. Boundary Rules

### 5.1 Frontend May Own

```text
- route composition
- visual layout
- local ephemeral UI state
- form draft state before submit
- table column visibility in the current view
- optimistic display only when backend contract permits it
- accessibility and interaction behavior
```

### 5.2 Backend Must Own

```text
- durable user preferences
- business validation
- lifecycle state
- approval/readiness decisions
- permission and capability enforcement
- module availability
- navigation contract
- artifact/evidence truth
- job state and progress
- local/cloud execution routing
```

### 5.3 Shared Contracts

The frontend consumes shared contracts for:

```text
- API error envelope
- pagination
- filter/sort models
- navigation
- actions available for an object
- status/severity enums
- preferences
- jobs and job events
- artifacts/evidence links
```

The GUI must not create its own shadow enum for business decisions.

## 6. Platform Adapters

Platform-specific behavior must be isolated behind adapters.

Initial adapter interfaces to model:

```text
ApiAdapter
FileAdapter
StorageAdapter
DownloadAdapter
NotificationAdapter
JobRunnerAdapter
AuthAdapter
SyncAdapter
DesktopBridgeAdapter
```

MVP1 can implement only browser-safe versions where needed. The important
architectural decision is that product modules depend on the interface, not on
browser or desktop APIs directly.

### 6.1 Browser Adapter Examples

```text
DownloadAdapter.downloadArtifact(url)
NotificationAdapter.toast(message)
StorageAdapter.readEphemeralUiCache(key)
StorageAdapter.writeEphemeralUiCache(key, value)
```

### 6.2 Future Desktop Adapter Examples

```text
FileAdapter.pickLocalFile()
FileAdapter.saveArtifactToFolder()
DesktopBridgeAdapter.getRuntimeStatus()
JobRunnerAdapter.requestLocalExecution(jobRequest)
NotificationAdapter.nativeNotification(message)
```

Desktop APIs must remain opt-in and behind capability checks.

## 7. Backend-Owned User Preferences

User preferences must be backend-owned from MVP1. The frontend may cache for
performance, but it is not the durable source of truth.

Conceptual model:

```text
UserPreference
  id
  user_id
  preference_key
  preference_value_json
  source
  created_at
  updated_at
```

Initial preference keys:

```text
theme.mode = light | dark | system
density.mode = comfortable | compact
sidebar.mode = expanded | collapsed
table.page_size.default = number
```

Default values:

```text
theme.mode = light
density.mode = comfortable
sidebar.mode = expanded
table.page_size.default = 25
```

The frontend resolution order is:

```text
1. Backend preference, if present.
2. Product default from backend preference metadata.
3. Hardcoded emergency fallback only if backend is unavailable during bootstrap.
```

That emergency fallback must be treated as a degraded state, not as normal
application truth.

## 8. Theme Strategy

### 8.1 Modes

The theme system supports:

```text
light - default product mode
dark - explicit user choice
system - follows OS/browser preference
```

The default initial mode is `light`.

### 8.2 Token-First Visual System

No product component should use raw colors, spacing, shadows, or status colors.
Components use semantic tokens.

Initial token families:

```text
color.background
color.surface
color.surface.subtle
color.border
color.border.strong
color.text.primary
color.text.secondary
color.text.muted
color.text.inverse
color.action.primary
color.action.primaryHover
color.action.secondary
color.action.danger
color.status.success
color.status.warning
color.status.danger
color.status.info
color.focus.ring

space.1..space.8
radius.sm
radius.md
radius.lg
shadow.panel
shadow.popover
font.family.sans
font.size.body
font.size.caption
font.size.heading
density.rowHeight
density.controlHeight
```

Light and dark themes provide different token values. Components remain
semantic.

### 8.3 Icon Strategy

Icons must be semantic and registered.

Example registry:

```text
create -> Plus
edit -> Pencil
delete -> Trash
download -> Download
upload -> Upload
validate -> ShieldCheck
warning -> TriangleAlert
error -> CircleAlert
success -> CircleCheck
artifact -> FileArchive
job -> Activity
evidence -> BadgeCheck
mapping -> GitBranch
settings -> Settings
```

Icons generally keep the same symbol in light/dark mode, but color, opacity,
focus, hover, disabled, and status treatments come from theme tokens. If a
special icon treatment is required, it must be added to the icon registry
rather than coded ad hoc in a module.

## 9. Visual Identity

The visual identity target is:

```text
enterprise operational premium
clear
modular
calm
dense but not cramped
technical without feeling raw
consistent across modules
```

The product should not use a different visual personality per module. A module
may have a specific icon or accent marker, but the framework, layout, buttons,
states, and object patterns remain the same.

Recommended baseline:

```text
Default theme: light
Default density: comfortable
Primary visual emphasis: strong typography, clean hierarchy, restrained color
Corner radius: small to medium; avoid bubbly controls
Charts/metrics: decision-oriented, not decorative
Gradients/orbs: avoid as general UI decoration
```

## 10. Workbench UI Kit Governance

### 10.1 Official Component Layer

All modules consume components from the Workbench UI Kit.

Initial categories:

```text
Shell:
- AppShell
- TopBar
- SidebarNav
- ContextSwitcher
- GlobalActivityIndicator

Page:
- PageHeader
- PageToolbar
- ModuleOverviewLayout
- ObjectListLayout
- ObjectDetailLayout
- ReviewQueueLayout
- WizardLayout

Data:
- DataTable
- FilterBar
- SearchInput
- SortControl
- PaginationControl
- StatusChip
- SeverityBadge

Actions:
- Button
- IconButton
- ActionMenu
- SplitButton
- ConfirmDialog

Feedback:
- EmptyState
- ErrorState
- BlockedState
- PermissionBanner
- ReadOnlyBanner
- Toast

Workbench Objects:
- JobTimeline
- ArtifactList
- EvidenceList
- AuditTimeline
- ManifestSummary
- ValidationIssueList

Technical Viewers:
- JsonPreview
- MarkdownPreview
- SchemaTree
- MappingTable
```

### 10.2 Component Rules

```text
- Components support light and dark themes.
- Components support comfortable density from the start.
- Components must not embed module-specific business rules.
- Components expose variants by semantic intent, not raw color.
- Components include loading, disabled, error, empty, and readonly states where applicable.
```

### 10.3 Module Rules

```text
- A new module composes existing page templates.
- A new module can request a new reusable component only after the need is documented.
- A new module cannot bypass backend navigation or permission contracts.
- A new module cannot create a separate visual language.
```

## 11. Exception Register

Complex or fancy interactions are allowed only through an exception process.

Examples that may need exceptions later:

```text
- Integration Mapping visual canvas
- advanced rate table grid
- schema tree diff viewer
- local file batch import assistant
- cutover readiness board
```

Each exception must document:

```text
- why the standard pattern is insufficient
- what user outcome requires the custom interaction
- whether the component can become reusable
- required backend contracts
- required accessibility behavior
- light/dark support
- testing and visual QA scope
```

Exception record location:

```text
docs/otm-workbench/gui/UI_EXCEPTIONS_REGISTER.md
```

## 12. Module Architecture

Frontend modules should be file-system modules with a manifest and bounded
routes.

Conceptual shape:

```text
frontend/src/modules/rates/
  rates.manifest.ts
  rates.routes.tsx
  pages/
  components/
  services/
  types/

frontend/src/modules/integration-mapping/
  integrationMapping.manifest.ts
  integrationMapping.routes.tsx
  pages/
  components/
  services/
  types/
```

Module manifests declare frontend structure only. They do not decide visibility.

Manifest may include:

```text
moduleId
routeBase
localRoutes
primaryObjectTypes
requiredBackendCapabilitiesForDisplayHints
iconKey
```

The backend navigation contract remains authoritative.

## 13. State Management

Recommended state boundaries:

```text
Server state: TanStack Query
Forms: React Hook Form + Zod
Route state: React Router
Ephemeral UI state: local React state or small UI stores
Durable preferences: backend preferences API
Cross-module domain state: backend APIs, not frontend stores
```

Do not create a large global store for backend domain state. It will duplicate
server truth and become stale.

## 14. API Client And Error Handling

The GUI should use one API client foundation with typed request/response
helpers and consistent error envelope handling.

Backend error envelope currently follows:

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable message.",
  "details": {}
}
```

The frontend must render:

```text
- field validation errors near fields
- object/action errors in page-level alerts
- authorization errors as permission states
- job/action errors in job details
- unknown transport errors as degraded API state
```

## 15. Desktop-Ready Constraints

To keep desktop feasible later:

```text
- No direct dependency on browser globals in modules.
- No direct filesystem assumptions in modules.
- API base URL must be configurable.
- Auth/session handling must be abstracted.
- Downloads/uploads use adapters.
- Notifications use adapters.
- Preferences are backend-owned.
- Local engine status is exposed through backend or adapter contracts.
```

Preferred future wrapper candidate is Tauri unless a later requirement needs
Electron-specific APIs. This is not an MVP1 implementation decision.

## 16. Figma And Design Documentation

Figma should mirror the Workbench UI Kit, not individual module experiments.

Recommended Figma structure:

```text
00 Foundations
01 Tokens Light
02 Tokens Dark
03 Components
04 Page Templates
05 Module Examples
06 Exceptions
```

Figma components should map to Workbench UI Kit components and semantic
variants.

## 17. MVP1 Architecture Deliverables

Before frontend scaffold:

```text
1. GUI_MVP1_PLAN.md
2. GUI_ARCHITECTURE_STRATEGY.md or this design spec
3. GUI_CONTRACT_AUDIT.md
4. DESIGN_SYSTEM_FOUNDATION.md
5. COMPONENT_INVENTORY.md
6. UI_EXCEPTIONS_REGISTER.md
```

Before module UI build:

```text
1. Workbench shell
2. UI Kit MVP
3. API client foundation
4. Job/artifact/evidence shared panels
5. Object list/detail templates
```

## 18. Risks

### 18.1 Module Visual Drift

Risk: each module invents its own layout and controls.

Mitigation:

```text
Use Workbench UI Kit and page templates as the only allowed module composition layer.
```

### 18.2 Frontend Business Rule Drift

Risk: frontend duplicates backend lifecycle/validation/permission rules.

Mitigation:

```text
Render backend statuses, validation, blockers, actions, and permissions.
```

### 18.3 Desktop Rework

Risk: browser-only assumptions make desktop expensive later.

Mitigation:

```text
Use platform adapters from the first frontend architecture.
```

### 18.4 Theme Retrofit Cost

Risk: dark mode becomes expensive if components use raw colors.

Mitigation:

```text
Token-first implementation and visual QA in light/dark from component MVP.
```

### 18.5 Preference Tracking Debt

Risk: early preferences live only in local frontend storage and are forgotten.

Mitigation:

```text
Backend-owned user preferences from MVP1.
```

## 19. Out Of Scope

```text
- Creating the React/Vite scaffold.
- Implementing the UI Kit.
- Choosing final Tauri vs Electron implementation.
- Building a desktop installer.
- Implementing cloud sync.
- Implementing local engine execution.
- Designing full visual canvas interactions.
- Creating client-specific demos or screenshots.
```

## 20. Acceptance Criteria

This design is accepted when:

```text
- Web-first and desktop-ready architecture is explicit.
- Backend-first and modularity boundaries are explicit.
- Approved stack is captured.
- Local-heavy/cloud-collaboration future is modeled.
- Platform adapters are named.
- Backend-owned preferences are required from MVP1.
- Light default plus dark/system modes are specified.
- Token-first identity and icon registry are specified.
- Workbench UI Kit governance is specified.
- Exception process is specified.
- No frontend implementation is included.
```

## 21. Recommended Next Step

Create `docs/otm-workbench/gui/GUI_CONTRACT_AUDIT.md`.

The audit should inspect current backend endpoints and identify:

```text
- ready-for-GUI contracts
- missing contracts before shell
- missing contracts before module screens
- preference API requirements
- navigation grouping/action metadata gaps
- artifact/evidence/job display gaps
```

Only after that audit should the React/Vite scaffold be planned.
