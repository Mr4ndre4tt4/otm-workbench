# GUI Load Plan Cutover Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first functional Load Plan/Cutover GUI workflow slice without stacking disconnected panels.

**Architecture:** Keep the route inside the existing Workbench shell and reuse shared module components. The frontend orchestrates a staged workflow, while backend APIs remain authoritative for package state, checklist items, readiness, handoff eligibility, and disabled outcomes.

**Tech Stack:** React + TypeScript + Vite, TanStack Query, Vitest + Testing Library, Playwright browser QA, FastAPI backend contracts.

---

## Scope

This plan implements the first `OTM-109` GUI slice:

```text
Select package -> create/inspect checklist -> update one checklist item ->
generate checklist readiness -> inspect handoff eligibility -> leave route and
return with backend-owned state visible.
```

It does not implement CSVUTIL build UI, ZIP analysis UI, full review queue UI,
package registration from Rates/Master Data, go/no-go commit, handoff commit,
or artifact download. Those stay separate follow-up slices.

## Files

```text
Modify:
- frontend/src/platform/api.ts
- frontend/src/platform/types/loadPlan.ts
- frontend/src/platform/hooks/loadPlan.ts
- frontend/src/modules/load-plan/LoadPlanView.tsx
- frontend/src/ui/layouts.css
- frontend/src/app/AppFunctionalLoadPlan.test.tsx
- frontend/scripts/functional-load-plan-browser.mjs
- frontend/package.json
- docs/otm-workbench/gui/GUI_FUNCTIONAL_QA_JOURNEYS.md
- docs/otm-workbench/gui/GUI_LOAD_PLAN_VIEW.md

Create:
- frontend/src/app/AppFunctionalLoadPlan.test.tsx
- frontend/scripts/functional-load-plan-browser.mjs
```

## Task 1: Add Load Plan API Client Coverage

**Files:**
- Modify: `frontend/src/platform/api.ts`
- Modify: `frontend/src/platform/types/loadPlan.ts`
- Modify: `frontend/src/platform/hooks/loadPlan.ts`

- [ ] **Step 1: Add PATCH helper**

Add this helper to `frontend/src/platform/api.ts` after `apiPut`:

```ts
export async function apiPatch<T>(
  path: string,
  body: Record<string, unknown>,
  options: RequestOptions = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PATCH",
    headers: headersFor(options, "application/json"),
    body: JSON.stringify(body)
  });
  return parseResponse<T>(response);
}
```

- [ ] **Step 2: Add Load Plan types**

Append these types to `frontend/src/platform/types/loadPlan.ts`:

```ts
export type CutoverChecklistItem = {
  id: string;
  checklist_id: string;
  sequence_index: number;
  category: string;
  label: string;
  description: string;
  status: string;
  method: string;
  evidence_id: string | null;
  required: boolean;
  updated_by: string | null;
  updated_at: string | null;
};

export type CutoverChecklist = {
  id: string;
  package_id: string;
  template_code: string;
  status: string;
  readiness_status: string;
  items: CutoverChecklistItem[];
  summary: {
    total_items: number;
    completed_items: number;
    blocked_items: number;
    required_items: number;
    missing_required_items: number;
  };
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type CutoverChecklistReadiness = {
  checklist_id: string;
  status: string;
  summary: CutoverChecklist["summary"];
  blockers: Array<{
    code: string;
    message: string;
    item_id?: string;
  }>;
  next_actions: string[];
};

export type CutoverHandoffEligibility = {
  package_id: string;
  eligible: boolean;
  status: string;
  blockers: Array<{
    code: string;
    message: string;
  }>;
  next_actions: string[];
};
```

If the backend serializer uses slightly different fields, keep the frontend
types aligned with the actual payload names from `serialize_checklist`,
`generate_checklist_readiness`, and `cutover_handoff_eligibility`.

- [ ] **Step 3: Add hooks and mutations**

Update `frontend/src/platform/hooks/loadPlan.ts` to import `apiPatch` and
`apiPost`, then add:

```ts
export function createCutoverChecklistFromPackage(token: string, packageId: string) {
  return apiPost<CutoverChecklist>(`/api/v1/modules/load-plan/cutover-checklists/from-package/${packageId}`, {}, { token });
}

export function updateCutoverChecklistItem(
  token: string,
  itemId: string,
  payload: { status?: string; method?: string; evidence_id?: string | null }
) {
  return apiPatch<CutoverChecklist>(`/api/v1/modules/load-plan/cutover-checklists/items/${itemId}`, payload, { token });
}

export function generateCutoverChecklistReadiness(token: string, checklistId: string) {
  return apiPost<CutoverChecklistReadiness>(
    `/api/v1/modules/load-plan/cutover-checklists/${checklistId}/readiness`,
    {},
    { token }
  );
}

export function useCutoverHandoffEligibility(token: string | null, packageId: string | null) {
  return useQuery({
    queryKey: ["modules", "load-plan", "cutover-handoff", "eligibility", packageId],
    queryFn: () =>
      apiGet<CutoverHandoffEligibility>(`/api/v1/modules/load-plan/cutover-handoff/eligibility?package_id=${packageId}`, {
        token
      }),
    enabled: Boolean(token && packageId)
  });
}
```

- [ ] **Step 4: Run TypeScript test target**

Run:

```bash
cd frontend
npm run test -- App.test.tsx
```

Expected: existing tests still pass or fail only because the new UI is not
implemented yet.

## Task 2: Write The Functional Load Plan Test

**Files:**
- Create: `frontend/src/app/AppFunctionalLoadPlan.test.tsx`

- [ ] **Step 1: Add failing functional test**

Create a test modeled after `AppFunctionalIntegrationMapping.test.tsx`, with
mock endpoints for:

```text
GET  /api/v1/platform/session/me
GET  /api/v1/platform/navigation
GET  /api/v1/platform/user-preferences
GET  /api/v1/platform/active-context/options
GET  /api/v1/platform/active-context
GET  /api/v1/platform/project-cockpit/summary
GET  /api/v1/modules/load-plan/summary
GET  /api/v1/modules/load-plan/packages
GET  /api/v1/modules/load-plan/packages/package_1
POST /api/v1/modules/load-plan/cutover-checklists/from-package/package_1
PATCH /api/v1/modules/load-plan/cutover-checklists/items/item_1
POST /api/v1/modules/load-plan/cutover-checklists/checklist_1/readiness
GET  /api/v1/modules/load-plan/cutover-handoff/eligibility?package_id=package_1
```

The test must assert:

```text
- Load Plan page renders a staged workflow.
- User clicks the checklist stage.
- User creates checklist from selected package.
- Checklist items are shown as a review queue.
- User updates item_1 to COMPLETE with method MANUAL and evidence id SYN_EVIDENCE_001.
- User generates checklist readiness.
- Handoff eligibility panel shows backend blocker or eligible state.
- User navigates away and returns; package/checklist state is still visible.
- Mutation requests include bearer Authorization.
```

- [ ] **Step 2: Run test and confirm it fails**

Run:

```bash
cd frontend
npm run test -- AppFunctionalLoadPlan.test.tsx
```

Expected: FAIL because `LoadPlanView` does not yet render staged workflow or
checklist actions.

## Task 3: Implement The Staged Load Plan View

**Files:**
- Modify: `frontend/src/modules/load-plan/LoadPlanView.tsx`
- Modify: `frontend/src/ui/layouts.css`

- [ ] **Step 1: Add stages**

Add stage state:

```ts
const loadPlanWorkflowStages = [
  { id: "packages", title: "Packages", status: "1" },
  { id: "checklist", title: "Checklist", status: "2" },
  { id: "readiness", title: "Readiness", status: "3" },
  { id: "handoff", title: "Handoff", status: "4" }
] as const;

type LoadPlanWorkflowStage = (typeof loadPlanWorkflowStages)[number]["id"];
```

Inside `LoadPlanView`, add:

```ts
const [activeStage, setActiveStage] = useState<LoadPlanWorkflowStage>("packages");
const [checklist, setChecklist] = useState<CutoverChecklist | null>(null);
const [readiness, setReadiness] = useState<CutoverChecklistReadiness | null>(null);
const [operationMessage, setOperationMessage] = useState<string | null>(null);
const [operationError, setOperationError] = useState<string | null>(null);
const [isMutating, setIsMutating] = useState(false);
const [evidenceId, setEvidenceId] = useState("SYN_EVIDENCE_001");
```

- [ ] **Step 2: Add mutations**

Add handlers:

```ts
async function handleCreateChecklist() {
  if (!effectivePackageId) return;
  setIsMutating(true);
  setOperationMessage(null);
  setOperationError(null);
  try {
    const created = await createCutoverChecklistFromPackage(token, effectivePackageId);
    setChecklist(created);
    setOperationMessage(`Checklist ${created.template_code} created for selected package.`);
    setActiveStage("checklist");
  } catch (error) {
    setOperationError(error instanceof Error ? error.message : "Could not create checklist.");
  } finally {
    setIsMutating(false);
  }
}

async function handleCompleteChecklistItem(itemId: string) {
  setIsMutating(true);
  setOperationMessage(null);
  setOperationError(null);
  try {
    const updated = await updateCutoverChecklistItem(token, itemId, {
      evidence_id: evidenceId.trim() || null,
      method: "MANUAL",
      status: "COMPLETE"
    });
    setChecklist(updated);
    setOperationMessage("Checklist item updated.");
  } catch (error) {
    setOperationError(error instanceof Error ? error.message : "Could not update checklist item.");
  } finally {
    setIsMutating(false);
  }
}

async function handleGenerateReadiness() {
  if (!checklist) return;
  setIsMutating(true);
  setOperationMessage(null);
  setOperationError(null);
  try {
    const result = await generateCutoverChecklistReadiness(token, checklist.id);
    setReadiness(result);
    setOperationMessage(`Checklist readiness is ${result.status}.`);
    setActiveStage("readiness");
  } catch (error) {
    setOperationError(error instanceof Error ? error.message : "Could not generate readiness.");
  } finally {
    setIsMutating(false);
  }
}
```

- [ ] **Step 3: Render the staged workflow**

Inside `ModuleWorkspaceLayout`, replace always-visible object list with stage
conditional rendering:

```tsx
<div className="load-plan-workflow" aria-label="Load Plan workflow">
  {loadPlanWorkflowStages.map((stage) => (
    <button
      aria-pressed={activeStage === stage.id}
      className={activeStage === stage.id ? "workflow-step workflow-step-active" : "workflow-step"}
      key={stage.id}
      onClick={() => setActiveStage(stage.id)}
      type="button"
    >
      <span>{stage.status}</span>
      <strong>{stage.title}</strong>
    </button>
  ))}
</div>
```

Render:

```text
packages stage: existing ModuleObjectList
checklist stage: create checklist button, evidence input, checklist item rows
readiness stage: generate readiness button, readiness blockers/summary
handoff stage: handoff eligibility from backend query
```

Use `FeedbackMessage`, `Button`, `OperationalPanel`, `BlockerPanel`,
`DetailList`, and `SelectedObjectPanel`. Do not add nested cards.

- [ ] **Step 4: Add CSS**

Append to `frontend/src/ui/layouts.css`:

```css
.load-plan-workflow {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

@media (max-width: 760px) {
  .load-plan-workflow {
    grid-template-columns: 1fr;
  }
}
```

Reuse existing `.workflow-step` styles if present; otherwise use the same
styling already introduced for Integration Mapping staged workflow.

- [ ] **Step 5: Run functional test**

Run:

```bash
cd frontend
npm run test -- AppFunctionalLoadPlan.test.tsx
```

Expected: PASS.

## Task 4: Add Browser QA Script

**Files:**
- Create: `frontend/scripts/functional-load-plan-browser.mjs`
- Modify: `frontend/package.json`

- [ ] **Step 1: Create browser script**

Create a script patterned after `functional-integration-mapping-browser.mjs`
that:

```text
1. Logs in as demo@example.test / DemoPass123!.
2. Opens Load Plan from navigation.
3. If no package exists, records BLOCKED with clear message instead of creating
   unrelated backend setup.
4. Selects first package.
5. Creates cutover checklist.
6. Completes first checklist item with SYN_EVIDENCE_001.
7. Generates readiness.
8. Opens handoff stage and waits for backend eligibility content.
9. Navigates to Catalog or Home and back to Load Plan.
10. Confirms selected package and checklist state remain visible.
11. Fails on console errors or HTTP failures.
```

- [ ] **Step 2: Add package script**

Add to `frontend/package.json`:

```json
"qa:functional:load-plan:browser": "node scripts/functional-load-plan-browser.mjs"
```

- [ ] **Step 3: Run browser QA**

Run:

```bash
cd frontend
npm run qa:functional:load-plan:browser
```

Expected:

```text
{ "status": "passed", "journey": "load-plan-cutover-checklist-readiness-return", ... }
```

If local DB lacks packages, seed one through existing backend APIs only if a
safe synthetic package setup already exists in the script pattern. Otherwise
record the blocker and create a follow-up issue.

## Task 5: Update Docs And Tracking

**Files:**
- Modify: `docs/otm-workbench/gui/GUI_FUNCTIONAL_QA_JOURNEYS.md`
- Modify: `docs/otm-workbench/gui/GUI_LOAD_PLAN_VIEW.md`
- Modify: `docs/otm-workbench/gui/GUI_MODULE_EXPERIENCE_ROADMAP.md`

- [ ] **Step 1: Update QA matrix**

Change the `/load-plan` row from partial/read-only to the new first workflow
slice. Mention checklist creation, item update, readiness generation, handoff
eligibility, and route return-state.

- [ ] **Step 2: Update Load Plan view doc**

Record:

```text
Primary pattern: review queue + staged workflow
First delivered story: package -> checklist -> readiness -> handoff eligibility
Out of current scope: CSVUTIL build UI, ZIP analysis UI, full review queue UI,
go/no-go commit, handoff commit, artifact download.
```

- [ ] **Step 3: Update Linear**

Add a comment to `OTM-109` with delivered scope and validation commands.

## Task 6: Final Verification

Run:

```bash
cd frontend
npm run test -- AppFunctionalLoadPlan.test.tsx guiModuleExperienceArchitectureContract.test.ts
npm run lint
npm run build
cd ..
python -m pytest tests/test_load_plan_cutover_checklist.py tests/test_load_plan_cutover_readiness.py tests/test_load_plan_cutover_handoff.py -q
git diff --check
```

Expected:

```text
All commands pass.
Only CRLF warnings are acceptable in git diff --check output.
```

If a backend test filename differs, run the closest existing Load Plan tests
found by `rg --files tests | rg "load_plan.*(cutover|readiness|handoff)"`.

## Self-Review

Spec coverage:

```text
- One primary story: covered by staged workflow tasks.
- Backend-owned decisions: readiness and handoff remain API responses.
- No stacked panels: covered by roadmap and staged rendering.
- Functional QA: covered by Task 2.
- Browser QA: covered by Task 4.
- Docs/Linear: covered by Task 5.
```

Placeholder scan:

```text
No TBD/TODO placeholders remain. Follow-up scope is explicitly out of scope.
```

Type consistency:

```text
The plan uses CutoverChecklist, CutoverChecklistReadiness, and
CutoverHandoffEligibility consistently across types, hooks, view, and tests.
```
