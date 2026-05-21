# GUI Frontend Architecture Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the current GUI shell, preferences, routing, and module views out of `frontend/src/app/App.tsx` while preserving backend-owned behavior and all existing tests.

**Architecture:** Keep the current React/Vite GUI behavior unchanged while moving code into clear ownership folders: `app/shell`, `app/routes`, `platform/preferences`, and `modules/*`. Shared visual primitives remain in `ui/`; module views consume backend hooks and shared components without adding business rules.

**Tech Stack:** React, TypeScript, Vite, React Router, TanStack Query, Vitest, Testing Library, ESLint.

---

## Files And Responsibilities

```text
frontend/src/app/App.tsx
  Keep only app composition, auth gate, preference loading, and shell mounting.

frontend/src/app/shell/SidebarNav.tsx
  Render backend navigation items and active state.

frontend/src/app/shell/PageHeader.tsx
  Shared page title/description/action header.

frontend/src/app/shell/ContextSummary.tsx
  Render active project/profile/environment/domain context summary.

frontend/src/app/shell/ContextSwitcher.tsx
  Update active backend project/profile/environment/domain context.

frontend/src/app/shell/PreferenceControls.tsx
  Persist theme, density, and sidebar preferences through backend contracts.

frontend/src/app/routes/WorkbenchRoute.tsx
  Route backend navigation items to module views.

frontend/src/app/routes/moduleDescriptions.ts
  Central module description map.

frontend/src/app/routes/routeUtils.ts
  Shared navigation active-state helper.

frontend/src/modules/{module}/
  One folder per delivered module view, each with View.tsx, meta.ts, and index.ts.

frontend/src/platform/preferences/hooks.ts
  Preference-specific re-export surface if useful after extraction.

frontend/src/app/App.test.tsx
  Keep existing behavioral coverage. Add one import-boundary smoke test if extraction creates exported helpers.

docs/otm-workbench/gui/GUI_FRONTEND_ARCHITECTURE_CLEANUP.md
  Record the final extracted folder model and ownership rules.
```

## Task 1: Add A Behavior Lock Before Extraction

**Files:**
- Modify: `frontend/src/app/App.test.tsx`

- [ ] **Step 1: Add a route fallback assertion to the existing shell tests**

Add this test inside `describe("App shell", () => { ... })` near the routing tests:

```tsx
  it("keeps unknown backend routes behind the module unavailable state", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/v1/platform/session/login")) {
        return jsonResponse({ access_token: "token-1", token_type: "bearer" });
      }
      if (url.endsWith("/api/v1/platform/navigation")) {
        return jsonResponse({
          items: [{ id: "rates", label: "Rates Studio", path: "/rates", status: "ACTIVE" }],
          total: 1,
          page: 1,
          page_size: 50
        });
      }
      if (url.endsWith("/api/v1/platform/user-preferences")) {
        return jsonResponse({
          theme_mode: "light",
          follow_system_theme: false,
          density: "comfortable",
          sidebar_mode: "expanded"
        });
      }
      return jsonResponse({ detail: "Unexpected request" }, 404);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/missing-module");
    await userEvent.type(screen.getByLabelText("Email"), "synthetic.user@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "synthetic-password");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Module unavailable" })).toBeInTheDocument();
    expect(screen.getByText("Use the backend-owned navigation menu to open an available module.")).toBeInTheDocument();
  });
```

- [ ] **Step 2: Run the focused test file**

Run:

```bash
cd frontend
npm run test -- App.test.tsx
```

Expected: all `App.test.tsx` tests pass. If this fails because helper names differ, inspect existing test helper names and adjust only the new test wiring, not production code.

- [ ] **Step 3: Commit the behavior lock**

```bash
git add frontend/src/app/App.test.tsx
git commit -m "test: lock gui routing fallback behavior"
```

## Task 2: Extract Routing Utilities And Module Descriptions

**Files:**
- Create: `frontend/src/app/routes/moduleDescriptions.ts`
- Create: `frontend/src/app/routes/routeUtils.ts`
- Modify: `frontend/src/app/App.tsx`

- [ ] **Step 1: Create `moduleDescriptions.ts`**

```ts
export const MODULE_DESCRIPTIONS: Record<string, string> = {
  admin: "Workspace, project, profile, environment, users, roles, capabilities, and feature flag administration.",
  assets: "Shared library for templates, payloads, generated files, specs, and reusable implementation assets.",
  catalog: "Canonical OTM catalog foundation for macro objects, load plans, data dictionary alignment, and module contracts.",
  dev_tools: "Internal diagnostics and development utilities exposed only behind admin and feature flag controls.",
  evidence: "Client-safe evidence, manifests, artifacts, and implementation audit trail across modules.",
  integration_mapping: "Table-first integration definitions, systems, endpoints, schema trees, mappings, joins, loops, and lookups.",
  load_plan: "Load package intake, CSVUtil planning, review queues, cutover readiness, and handoff controls.",
  master_data: "Template factory and master data batch preparation for backend-first OTM implementation flows.",
  order_release_generator: "Order release template, batch, XML preview, artifact, and job orchestration workspace.",
  rates: "Rate batch preparation, validation, approval, CSV preview, export artifacts, and load package handoff."
};
```

- [ ] **Step 2: Create `routeUtils.ts`**

```ts
import type { NavigationItem } from "../../platform/types";

export function isNavigationItemActive(item: NavigationItem, currentPath: string) {
  if (item.id === "home" && (currentPath === "/" || currentPath === "/home")) return true;
  return currentPath === item.path || currentPath.startsWith(`${item.path}/`);
}
```

- [ ] **Step 3: Update `App.tsx` imports**

Add:

```ts
import { MODULE_DESCRIPTIONS } from "./routes/moduleDescriptions";
import { isNavigationItemActive } from "./routes/routeUtils";
```

Remove the local `MODULE_DESCRIPTIONS` constant and local `isNavigationItemActive` function from `App.tsx`.

- [ ] **Step 4: Run tests**

```bash
cd frontend
npm run test -- App.test.tsx
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/App.tsx frontend/src/app/routes/moduleDescriptions.ts frontend/src/app/routes/routeUtils.ts
git commit -m "refactor: extract gui route metadata"
```

## Task 3: Extract Shell Components

**Files:**
- Create: `frontend/src/app/shell/ActionBar.tsx`
- Create: `frontend/src/app/shell/PageHeader.tsx`
- Create: `frontend/src/app/shell/SidebarNav.tsx`
- Create: `frontend/src/app/shell/ContextSummary.tsx`
- Create: `frontend/src/app/shell/ContextSwitcher.tsx`
- Create: `frontend/src/app/shell/PreferenceControls.tsx`
- Create: `frontend/src/app/shell/index.ts`
- Modify: `frontend/src/app/App.tsx`

- [ ] **Step 1: Move `ActionBar` and `PageHeader`**

Create `frontend/src/app/shell/ActionBar.tsx`:

```tsx
import { Button } from "../../ui/components";
import type { AvailableAction } from "../../platform/types";

export function ActionBar({ actions }: { actions: AvailableAction[] }) {
  return (
    <div className="action-bar">
      {actions.map((action) => (
        <Button disabled={action.disabled} key={action.key} variant={action.variant === "primary" ? "primary" : "secondary"}>
          {action.label}
        </Button>
      ))}
    </div>
  );
}
```

Create `frontend/src/app/shell/PageHeader.tsx`:

```tsx
import type { AvailableAction } from "../../platform/types";
import { ActionBar } from "./ActionBar";

export function PageHeader({
  actions,
  description,
  label,
  title
}: {
  actions?: AvailableAction[];
  description: string;
  label: string;
  title: string;
}) {
  return (
    <header className="page-header">
      <div>
        <p className="section-label">{label}</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {actions ? <ActionBar actions={actions} /> : null}
    </header>
  );
}
```

- [ ] **Step 2: Move `SidebarNav` and context helpers**

Create `SidebarNav.tsx` by moving the existing `navIcon` and `SidebarNav` implementations from `App.tsx`. Import `NavigationItem` and `UserPreferences` from `../../platform/types`, `StatusChip` from `../../ui/components`, and `isNavigationItemActive` from `../routes/routeUtils`.

Create `ContextSummary.tsx` by moving the existing `ContextSummary` implementation unchanged.

Create `ContextSwitcher.tsx` by moving the existing `ContextSwitcher` implementation unchanged and importing `ApiError`, `updateActiveContext`, `useEnvironments`, `useProfiles`, `useProjects`, `Button`, and `useQueryClient`.

- [ ] **Step 3: Move `PreferenceControls`**

Create `PreferenceControls.tsx` by moving the existing implementation unchanged and importing `Monitor`, `Moon`, `PanelLeftClose`, `PanelLeftOpen`, `Rows3`, `Sun`, `ApiError`, `updateUserPreferences`, `IconButton`, `UserPreferences`, and `useQueryClient`.

- [ ] **Step 4: Create shell barrel**

```ts
export { ActionBar } from "./ActionBar";
export { ContextSummary } from "./ContextSummary";
export { ContextSwitcher } from "./ContextSwitcher";
export { PageHeader } from "./PageHeader";
export { PreferenceControls } from "./PreferenceControls";
export { SidebarNav } from "./SidebarNav";
```

- [ ] **Step 5: Update `App.tsx`**

Import shell components:

```ts
import { ContextSwitcher, PageHeader, PreferenceControls, SidebarNav } from "./shell";
```

Remove the local shell component implementations from `App.tsx`. Keep behavior unchanged.

- [ ] **Step 6: Run lint and tests**

```bash
cd frontend
npm run lint
npm run test -- App.test.tsx
```

Expected: lint passes and all `App.test.tsx` tests pass.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/App.tsx frontend/src/app/shell
git commit -m "refactor: extract gui shell components"
```

## Task 4: Extract Module Views Into `modules/*`

**Files:**
- Create: `frontend/src/modules/rates/RatesSummaryView.tsx`
- Create: `frontend/src/modules/assets/AssetsLibraryView.tsx`
- Create: `frontend/src/modules/evidence/EvidenceHubView.tsx`
- Create: `frontend/src/modules/load-plan/LoadPlanView.tsx`
- Create: `frontend/src/modules/catalog/CatalogCoreView.tsx`
- Create: `frontend/src/modules/master-data/MasterDataView.tsx`
- Create: `frontend/src/modules/order-release-generator/OrderReleaseGeneratorView.tsx`
- Create: `frontend/src/modules/integration-mapping/IntegrationMappingView.tsx`
- Create: `frontend/src/modules/index.ts`
- Modify: `frontend/src/app/App.tsx`

- [ ] **Step 1: Move one module first, Rates**

Create `frontend/src/modules/rates/RatesSummaryView.tsx` by moving:

```text
severityStatus
booleanStatus
rateBatchMeta
RatesSummaryView
```

Import the same hooks, types, shared UI components, and `PageHeader` from `../../app/shell`.

- [ ] **Step 2: Run focused test**

```bash
cd frontend
npm run test -- App.test.tsx
```

Expected: all tests pass. This confirms the first module extraction pattern before moving the rest.

- [ ] **Step 3: Move remaining module views**

Move each view and its direct meta helper into the corresponding module file:

```text
assets -> assetMeta, AssetsLibraryView
evidence -> evidenceMeta, EvidenceHubView
load-plan -> loadPlanPackageMeta, LoadPlanView
catalog -> catalogMacroMeta, CatalogCoreView
master-data -> masterDataTemplateMeta, MasterDataView
order-release-generator -> orderReleaseTemplateMeta, OrderReleaseGeneratorView
integration-mapping -> integrationDefinitionMeta, IntegrationMappingView
```

If `booleanStatus` is needed by multiple modules, create:

```ts
// frontend/src/modules/moduleStatus.ts
export function booleanStatus(value: number) {
  return value > 0 ? "ACTIVE" : "EMPTY";
}
```

If `severityStatus` remains Rates-only, keep it in the Rates module.

- [ ] **Step 4: Create module barrel**

Create `frontend/src/modules/index.ts`:

```ts
export { AssetsLibraryView } from "./assets/AssetsLibraryView";
export { CatalogCoreView } from "./catalog/CatalogCoreView";
export { EvidenceHubView } from "./evidence/EvidenceHubView";
export { IntegrationMappingView } from "./integration-mapping/IntegrationMappingView";
export { LoadPlanView } from "./load-plan/LoadPlanView";
export { MasterDataView } from "./master-data/MasterDataView";
export { OrderReleaseGeneratorView } from "./order-release-generator/OrderReleaseGeneratorView";
export { RatesSummaryView } from "./rates/RatesSummaryView";
```

- [ ] **Step 5: Update `App.tsx` imports**

```ts
import {
  AssetsLibraryView,
  CatalogCoreView,
  EvidenceHubView,
  IntegrationMappingView,
  LoadPlanView,
  MasterDataView,
  OrderReleaseGeneratorView,
  RatesSummaryView
} from "../modules";
```

Remove module view implementations and module-only helper functions from `App.tsx`.

- [ ] **Step 6: Run verification**

```bash
cd frontend
npm run lint
npm run test
```

Expected: lint passes and the full frontend test suite passes.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/App.tsx frontend/src/modules
git commit -m "refactor: extract gui module views"
```

## Task 5: Split Platform Hooks By Domain Without Changing Public Imports

**Files:**
- Create: `frontend/src/platform/hooks/platform.ts`
- Create: `frontend/src/platform/hooks/rates.ts`
- Create: `frontend/src/platform/hooks/assets.ts`
- Create: `frontend/src/platform/hooks/evidence.ts`
- Create: `frontend/src/platform/hooks/loadPlan.ts`
- Create: `frontend/src/platform/hooks/catalog.ts`
- Create: `frontend/src/platform/hooks/masterData.ts`
- Create: `frontend/src/platform/hooks/orderReleaseGenerator.ts`
- Create: `frontend/src/platform/hooks/integrationMapping.ts`
- Modify: `frontend/src/platform/hooks.ts`

- [ ] **Step 1: Create domain hook files**

Move hooks by endpoint family into the files listed above. Preserve function names and implementation bodies.

Keep `frontend/src/platform/hooks.ts` as a compatibility barrel:

```ts
export * from "./hooks/platform";
export * from "./hooks/rates";
export * from "./hooks/assets";
export * from "./hooks/evidence";
export * from "./hooks/loadPlan";
export * from "./hooks/catalog";
export * from "./hooks/masterData";
export * from "./hooks/orderReleaseGenerator";
export * from "./hooks/integrationMapping";
```

- [ ] **Step 2: Run TypeScript and tests**

```bash
cd frontend
npm run build
npm run test
```

Expected: build and tests pass. Existing imports from `../platform/hooks` continue working.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/platform/hooks.ts frontend/src/platform/hooks
git commit -m "refactor: split platform hooks by domain"
```

## Task 6: Document The Extracted Ownership Model

**Files:**
- Create: `docs/otm-workbench/gui/GUI_FRONTEND_ARCHITECTURE_CLEANUP.md`
- Modify: `docs/otm-workbench/gui/GUI_MVP1_PLAN.md`

- [ ] **Step 1: Create cleanup doc**

```md
# GUI Frontend Architecture Cleanup

**Status:** planned implementation slice

## Goal

Extract the first GUI implementation into clear frontend ownership folders
without changing behavior, backend contracts, or visual identity.

## Target Ownership

```text
app/      shell, route orchestration, auth gate
platform/ backend API hooks, types, auth, preferences, future desktop adapters
ui/       reusable primitives, components, layouts, states, tokens
modules/ backend-backed module views and domain-specific widgets
```

## Guardrails

```text
- no business rule migration to frontend
- no redesign during extraction
- no real client data in tests or docs
- no direct desktop APIs in module views
- no new module-specific visual framework
```

## Verification

```text
npm run lint
npm run test
npm run build
```
```

- [ ] **Step 2: Update MVP1 plan delivered follow-up contracts**

Add:

```text
- GUI frontend architecture cleanup plan
  documented in GUI_FRONTEND_ARCHITECTURE_CLEANUP.md
```

- [ ] **Step 3: Commit**

```bash
git add docs/otm-workbench/gui/GUI_FRONTEND_ARCHITECTURE_CLEANUP.md docs/otm-workbench/gui/GUI_MVP1_PLAN.md
git commit -m "docs: plan gui architecture cleanup"
```

## Task 7: Final Verification And PR Handoff

**Files:**
- Verify all modified frontend and docs files.

- [ ] **Step 1: Run full frontend verification**

```bash
cd frontend
npm run lint
npm run test
npm run build
```

Expected:

```text
lint passes
all Vitest tests pass
Vite production build succeeds
```

- [ ] **Step 2: Run repository hygiene checks**

```bash
git diff --check
rg -n "CNPJ|CPF|ChangeMe123|admin@example|OTM1\\.ACC|NDD real" frontend/src docs/otm-workbench/gui
```

Expected: `git diff --check` has no errors. The sensitivity scan has no hits other than existing negative assertions that intentionally verify forbidden internals are not rendered.

- [ ] **Step 3: Confirm untracked resources remain untouched**

```bash
git status --short --branch
```

Expected: only intended tracked changes are staged or committed. `OTM_RESOURCES/` may remain untracked and must not be committed.

- [ ] **Step 4: Push branch**

```bash
git push -u origin codex/gui-frontend-architecture-cleanup
```

Expected: branch is published and GitHub returns a PR creation URL.

## Self-Review

Spec coverage:

```text
- Backend/frontend ownership boundary: Tasks 2, 3, 4, 5, 6.
- Module UI consistency: Tasks 3, 4, 6.
- Backend-owned preferences: Task 3.
- Desktop-ready boundary: Task 6.
- Incremental extraction roadmap: Tasks 1 through 7.
- No custom interaction expansion: all tasks are extraction-only.
```

Placeholder scan:

```text
No provisional markers are intentionally used. Each task has exact files,
commands, and expected results.
```

Type consistency:

```text
Existing exported component and hook names are preserved. `App.tsx` remains the
composition entrypoint. `frontend/src/platform/hooks.ts` remains a compatibility
barrel so current imports do not need to change in the same slice.
```
