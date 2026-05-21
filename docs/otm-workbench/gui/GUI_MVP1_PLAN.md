# GUI MVP1 Plan - OTM Workbench

**Status:** planning foundation  
**Linear:** OTM-55  
**Scope:** GUI planning only; no frontend scaffold in this slice.

## 1. Decision

The GUI MVP1 should start with a governed Workbench shell and reusable screen
patterns before any module-specific visual build.

The frontend must render backend contracts instead of owning business rules.
Navigation, module visibility, permissions, lifecycle gates, job status,
artifact metadata, evidence references, and validation decisions remain
backend-owned.

Recommended stack, already aligned with the project foundation docs:

```text
React + TypeScript + Vite
React Router
Workbench UI Kit based on reusable accessible primitives
Vitest + Testing Library
```

## 2. Product Goal

Create an operational workbench for OTM project teams to prepare, validate,
package, review, and evidence technical work across modules.

The GUI should feel like an internal professional tool:

```text
dense but readable,
workflow-oriented,
contract-driven,
module-consistent,
evidence-aware,
safe for repeated operational use.
```

It should not feel like a landing page or marketing site.

## 3. Non-Negotiable Guardrails

```text
- Backend-owned navigation via /api/v1/platform/navigation.
- Backend-owned permissions and capabilities.
- No hardcoded module visibility in frontend.
- No duplication of validation, approval, OTM dependency, or lifecycle rules.
- No real client names or client payloads in UI fixtures, mocks, docs, or screenshots.
- No UI-only status transitions.
- No direct OTM execution from GUI until backend contracts explicitly support it.
- No canvas-heavy/custom interaction before list/detail/review patterns are stable.
```

## 4. MVP1 Delivery Shape

MVP1 should be delivered in phases:

```text
Phase 0 - GUI contracts review
Phase 1 - Workbench shell
Phase 2 - Workbench UI Kit minimum
Phase 3 - shared object display patterns
Phase 4 - first module screens
Phase 5 - module-specific hardening
```

The first usable screen should be the actual workbench shell, not a landing
page.

## 5. Workbench Shell

### 5.1 Responsibilities

```text
- Authenticate session or consume existing local session.
- Fetch /api/v1/platform/navigation.
- Render backend-provided module menu and status.
- Render active context: project, profile, environment, domain.
- Provide global command/action area.
- Provide global job/activity indicator.
- Provide a consistent content layout for modules.
```

### 5.2 Shell Layout

```text
AppChrome
  TopBar
    Product identity
    Active context switcher
    Global search / command entry
    Job/activity indicator
    User menu
  Sidebar
    Navigation groups from backend contract
    Module status indicators
  MainContent
    PageHeader
    Toolbar
    ContentRegion
  RightRail (optional)
    Job details
    Evidence/artifacts
    Contextual help
```

### 5.3 Required States

```text
- Loading navigation
- Navigation fetch error
- No active project/profile/environment
- No permission for module
- Module planned/disabled
- API unavailable/degraded
- Read-only context
```

## 6. Navigation And Information Architecture

The visible menu order should follow the backend module registry while the GUI
groups modules by workflow.

Recommended first grouping:

```text
Cockpit
  Project Cockpit
  Evidence Hub

Build
  Rates Studio
  Data Factory
  Coordinate Quality
  Order Release Generator
  Integration Mapping Studio

Govern
  OTM Catalog Core
  Assets Library
  Load Plan
  Cutover Checklist / CSVUTIL

Admin
  Project/Profile/Admin Foundation
  Developer Tools
```

The backend currently returns a flat list. MVP1 may render flat first and add
grouping later only after the backend contract supports grouping metadata.

## 7. Reusable Page Templates

### 7.1 Module Overview

Use for every module landing screen.

```text
Purpose: show module health, next actions, recent objects, blockers, and recent artifacts.
Primary action: create/import/build the main module object.
Secondary actions: view jobs, view evidence, open settings, export/download where supported.
```

### 7.2 Object List

Use for batches, packages, templates, mappings, assets, jobs, evidence.

```text
Required:
- search
- filters
- status chips
- created/updated metadata
- row action menu
- empty state
- no results state
- error state
```

### 7.3 Object Detail

Use for one batch/package/template/definition.

```text
Header:
- object code/name
- lifecycle status
- primary action
- secondary action menu

Tabs:
- Overview
- Data / Rows / Mappings
- Validation
- Jobs
- Artifacts
- Evidence
- Audit
```

### 7.4 Wizard / Guided Flow

Use only when the backend workflow is step-based.

```text
Examples:
- import payload
- create rate batch
- generate CSVUTIL package
- build Order Release XML
- generate Integration Mapping spec
```

Wizard steps must reflect backend lifecycle gates, not frontend-only assumptions.

### 7.5 Review Queue

Use for validation issues, blockers, load plan findings, and cutover readiness.

```text
Required:
- severity
- category
- affected object
- recommended action
- decision/status
- evidence link
```

## 8. Workbench UI Kit MVP

Minimum reusable components:

```text
AppShell
SidebarNav
TopBar
ContextSwitcher
PageHeader
PageToolbar
StatusChip
SeverityBadge
ModuleStatusBadge
ActionButton
IconButton
DataTable
FilterBar
SearchInput
EmptyState
ErrorState
BlockedState
ReadOnlyBanner
PermissionBanner
Tabs
Drawer
Modal
JobTimeline
ArtifactList
EvidenceList
AuditTimeline
JsonPreview
MarkdownPreview
SchemaTree
MappingTable
```

Custom components should be added only after at least two modules need the same
pattern or a module has a clearly unique interaction.

## 9. Object Display Patterns

### 9.1 Shared Object Types

```text
Job
Artifact
Evidence
Manifest
AuditLog
DomainEvent
Module
Template
Batch
Package
ValidationIssue
```

### 9.2 Status Rendering

Status colors must be semantic, not module-specific:

```text
DRAFT / CREATED / REGISTERED: neutral
RUNNING / IN_PROGRESS: info
SUCCEEDED / APPROVED / READY: success
WARNING / BLOCKED / NEEDS_REVIEW: warning
FAILED / ERROR / REJECTED: danger
ARCHIVED / CANCELLED: muted
```

### 9.3 Action Rendering

Actions should be shown in priority order:

```text
Primary action: one per screen.
Secondary actions: toolbar buttons if common.
Overflow actions: row/menu actions.
Danger actions: separated, confirmed, and backend-authorized.
```

## 10. Module Screen Map

### 10.1 Project Cockpit

```text
Screens:
- Cockpit overview
- Active context selector
- Recent jobs
- Recent artifacts/evidence
- Module readiness summary

Primary action:
- Set active context / continue latest work
```

### 10.2 Rates Studio

```text
Screens:
- Rates overview
- Rate batch list
- Rate batch detail
- Table/row review
- Validation issues
- Approval readiness
- Export artifacts

Primary action:
- Create/import rate batch
```

### 10.3 Load Plan

```text
Screens:
- Load Plan overview
- Package list
- Package detail
- Sequence snapshot
- Review queue
- Cutover readiness
- Cutover package export

Primary action:
- Register package / generate readiness depending on context
```

### 10.4 Evidence Hub

```text
Screens:
- Evidence overview
- Artifact list
- Manifest list
- Evidence list
- Archive package detail
- Download/audit view

Primary action:
- Build archive package when source context supports it
```

### 10.5 OTM Catalog Core

```text
Screens:
- Catalog overview
- Macro object list
- Table list/detail
- Field policy detail
- Load sequence view
- Data dictionary import status

Primary action:
- Review catalog / import dictionary only when backend allows
```

### 10.6 Data Factory / Master Data

```text
Screens:
- Template list
- Template detail
- Batch list
- Batch detail
- Workbook/export artifacts
- Coordinate Quality batch/result detail

Primary action:
- Build workbook or create validation batch
```

### 10.7 Assets Library

```text
Screens:
- Asset list
- Asset detail
- Version history
- Links
- Upload/download audit

Primary action:
- Create asset or upload new version
```

### 10.8 Order Release Generator

```text
Screens:
- Template list/detail
- Batch import
- Batch detail
- XML preview
- XML artifact
- Submit guard/readiness

Primary action:
- Import rows / generate XML artifact
```

### 10.9 Integration Mapping Studio

```text
Screens:
- Definition list
- Definition detail
- Source/target payload artifacts
- Schema document explorer
- Mapping table
- Loops/joins/lookups tabs
- Validation
- Preview
- Markdown spec artifact
- Audit/events

Primary action:
- Create mapping definition
```

MVP1 should keep this table-first. A canvas can be considered later, after the
table/detail workflows prove stable.

### 10.10 Admin Console

```text
Screens:
- Workspace/project/profile/environment administration
- Users/roles/capabilities
- Feature flags
- Active context diagnostics

Primary action:
- Configure project/profile/environment
```

## 11. Backend Contract Gaps Before GUI Build

Before implementing full GUI screens, confirm or add contracts for:

```text
- Navigation grouping metadata, if grouped sidebar is desired.
- Backend-provided available actions per object.
- Consistent pagination/filter/sort contracts for list endpoints.
- Consistent object summary endpoints for module overview pages.
- Artifact download URLs and content metadata.
- Evidence links by source object.
- Permission/capability explanations for disabled actions.
- Active context read/update contract completeness.
- Job polling contract and event timeline contract.
```

Do not solve these by frontend guesses.

Delivered follow-up contracts:

```text
- GET /api/v1/platform/project-cockpit/summary
  documented in GUI_PROJECT_COCKPIT_SUMMARY_CONTRACT.md
- Initial browser-first React/Vite shell
  documented in GUI_SHELL_SCAFFOLD.md
- Initial GUI auth/session flow
  documented in GUI_AUTH_SESSION_FLOW.md
- Initial authenticated context switcher
  documented in GUI_CONTEXT_SWITCHER.md
- Local GUI + FastAPI integration validation
  documented in GUI_LOCAL_INTEGRATION_VALIDATION.md
- Backend-owned theme preferences
  documented in GUI_THEME_PREFERENCES.md
- Module routing foundation
  documented in GUI_MODULE_ROUTING_FOUNDATION.md
- Rates Studio summary view
  documented in GUI_RATES_SUMMARY_VIEW.md
- Rates Studio batch detail panel
  documented in GUI_RATES_BATCH_DETAIL_PANEL.md
- Rates Studio action execution
  documented in GUI_RATES_ACTION_EXECUTION.md
- Rates Studio artifacts and evidence panels
  documented in GUI_RATES_ARTIFACTS_EVIDENCE.md
- Rates Studio artifact download affordance
  documented in GUI_RATES_ARTIFACT_DOWNLOAD.md
- Shared operational panels foundation
  documented in GUI_SHARED_OPERATIONAL_PANELS.md
- Shared metrics foundation
  documented in GUI_SHARED_METRICS.md
- Selected object panel foundation
  documented in GUI_SELECTED_OBJECT_PANEL.md
- Module object list foundation
  documented in GUI_MODULE_OBJECT_LIST.md
- Detail list foundation
  documented in GUI_DETAIL_LIST.md
- Assets Library backend-backed view
  documented in GUI_ASSETS_LIBRARY_VIEW.md
- Evidence Hub backend-backed view
  documented in GUI_EVIDENCE_HUB_VIEW.md
- Load Plan backend-backed view
  documented in GUI_LOAD_PLAN_VIEW.md
- Catalog Core backend-backed view
  documented in GUI_CATALOG_CORE_VIEW.md
- Master Data backend-backed view
  documented in GUI_MASTER_DATA_VIEW.md
- Order Release Generator backend-backed view
  documented in GUI_ORDER_RELEASE_GENERATOR_VIEW.md
- Integration Mapping Studio backend-backed view
  documented in GUI_INTEGRATION_MAPPING_VIEW.md
- GUI frontend architecture and design governance
  documented in GUI_FRONTEND_ARCHITECTURE.md
- GUI frontend architecture cleanup
  documented in GUI_FRONTEND_ARCHITECTURE_CLEANUP.md
- GUI CSS token audit
  documented in GUI_CSS_TOKEN_AUDIT.md
- GUI theme token extraction
  documented in GUI_THEME_TOKEN_EXTRACTION.md
- GUI density token extraction
  documented in GUI_DENSITY_TOKEN_EXTRACTION.md
- GUI sidebar token extraction
  documented in GUI_SIDEBAR_TOKEN_EXTRACTION.md
- GUI responsive token extraction
  documented in GUI_RESPONSIVE_TOKEN_EXTRACTION.md
- GUI shell QA contracts
  documented in GUI_SHELL_QA_CONTRACTS.md
- GUI shared component style extraction
  documented in GUI_SHARED_COMPONENT_STYLE_EXTRACTION.md
- GUI shell style extraction
  documented in GUI_SHELL_STYLE_EXTRACTION.md
- GUI layout style extraction
  documented in GUI_LAYOUT_STYLE_EXTRACTION.md
- GUI base style extraction
  documented in GUI_BASE_STYLE_EXTRACTION.md
- GUI browser QA attempt
  documented in GUI_BROWSER_QA_ATTEMPT.md
- GUI CSS entrypoint contract
  documented in GUI_CSS_ENTRYPOINT_CONTRACT.md
- GUI CSS layer ownership contract
  documented in GUI_CSS_LAYER_OWNERSHIP_CONTRACT.md
- GUI React boundary contract
  documented in GUI_REACT_BOUNDARY_CONTRACT.md
- GUI module navigation contract
  documented in GUI_MODULE_NAVIGATION_CONTRACT.md
- GUI state pattern contract
  documented in GUI_STATE_PATTERN_CONTRACT.md
- GUI action pattern contract
  documented in GUI_ACTION_PATTERN_CONTRACT.md
- GUI object list pattern contract
  documented in GUI_OBJECT_LIST_PATTERN_CONTRACT.md
- GUI selected object pattern contract
  documented in GUI_SELECTED_OBJECT_PATTERN_CONTRACT.md
- GUI detail list pattern contract
  documented in GUI_DETAIL_LIST_PATTERN_CONTRACT.md
```

## 12. Implementation Order

Recommended order:

```text
1. GUI contracts audit against current OpenAPI/routes.
2. Frontend app scaffold: React + TypeScript + Vite.
3. API client foundation and error envelope handling.
4. Workbench shell consuming health + navigation.
5. Workbench UI Kit minimum.
6. Shared jobs/artifacts/evidence panels.
7. Project Cockpit.
8. Rates Studio first useful list/detail.
9. Load Plan + Evidence Hub cross-module views.
10. Integration Mapping Studio table-first views.
11. Assets Library and Order Release Generator.
12. Admin Console.
13. Visual QA, accessibility pass, and Storybook/component docs.
```

## 13. MVP1 Out Of Scope

```text
- Full visual canvas for Integration Mapping.
- Real OTM execution/upload controls not backed by backend safeguards.
- Client-specific examples or screenshots.
- Complex theming or branding system.
- Offline sync UI.
- Real-time collaboration.
- Mobile-first workflow.
- Replacing Swagger/OpenAPI as source of contract truth.
```

## 14. Acceptance Criteria

GUI MVP1 planning is accepted when:

```text
- Workbench shell scope is clear.
- Navigation remains backend-owned.
- Page templates are reusable across modules.
- Module screen map covers current backend modules.
- Backend contract gaps are listed.
- Implementation order is explicit.
- Out-of-scope items prevent visual overreach.
```

## 15. Immediate Next Step

Run a GUI contracts audit:

```text
Input:
- /api/v1/platform/navigation
- /api/v1/platform/modules
- module list/detail/action endpoints
- jobs/artifacts/evidence endpoints

Output:
- GUI_CONTRACT_AUDIT.md
- list of endpoints ready for GUI
- list of endpoint gaps before scaffold
- proposed first frontend PR scope
```
