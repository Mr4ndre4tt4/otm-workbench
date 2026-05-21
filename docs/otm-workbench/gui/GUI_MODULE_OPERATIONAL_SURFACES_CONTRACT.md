# GUI Module Operational Surfaces Contract

**Status:** delivered  
**Branch:** `codex/gui-module-operational-surfaces`  
**Linear:** `OTM-69`  
**Scope:** module-level operational surfaces for artifacts, evidence, jobs, and blockers.

## 1. Purpose

Backend-backed module screens should expose operational surfaces through shared
patterns instead of creating module-specific panels for every artifact, evidence
item, job, blocker, or generated file.

This contract defines when a module may add those surfaces and which shared
components own the rendering.

## 2. Source Components

Use the existing shared UI contracts:

```text
ModuleWorkspaceLayout
SelectedObjectPanel
OperationalPanel
ArtifactList
BlockerPanel
ActivityRow
StatePanel
StatusChip
FeedbackMessage
```

Do not create module-local replacements for:

```text
- artifact rows
- evidence rows
- job rows
- blocker rows
- operational panel shells
- loading/empty/error/blocked panels
```

## 3. Backend Ownership

Operational surfaces render backend-owned facts. They do not decide those facts.

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

Frontend may map backend payloads into display props only:

```text
- title
- subtitle
- meta lines
- status labels
- selected object id
- empty copy
- loading copy
```

## 4. Surface Slots

Every backend-backed module screen has three possible operational slots:

```text
1. Workspace side slot
   Selected-object details, safe metadata, references, and backend actions.

2. Below-workspace blocker slot
   Blocking validation, setup, dependency, or readiness issues.

3. Below-workspace activity grid
   Artifacts, evidence, recent jobs, generated outputs, and secondary queues.
```

Modules should leave a slot absent until the backend exposes a contract for it.
Do not add decorative empty panels just to make every screen look fuller.

## 5. Required States

Operational surfaces must support these states through shared components and
backend-provided metadata:

```text
- loading
- empty
- no results
- error/unavailable
- warning
- success
- blocked
- disabled by permission
- read-only
```

If a state is not yet represented by a backend contract, record it as a module
gap instead of inferring it locally.

## 6. Module Matrix

| Module | Current operational surface | Next allowed extension |
|---|---|---|
| Rates Studio | Blockers, artifacts, evidence, selected-object actions | Jobs/progress if backend exposes job collection |
| Catalog Core | Selected object metadata only | Dependencies/blockers when catalog validation exposes them |
| Load Plan | Selected object metadata only | Package artifacts and processing jobs |
| Assets Library | Selected object metadata and versions | Downloadable assets through artifact metadata |
| Evidence Hub | Evidence references and safe artifact metadata | Download affordances only through guarded backend URLs |
| Master Data | Template/sheet/field metadata only | Generated template artifacts and review blockers |
| Order Release Generator | Template metadata only | XML artifacts, preview jobs, and import jobs |
| Integration Mapping Studio | Payload/schema/mapping metadata | Payload artifacts, preview jobs, and mapping blockers |

## 7. Client-Safe Rules

Operational examples and tests must use synthetic content only.

Do not render or add fixtures containing:

```text
- real client names
- real payload values
- real document identifiers
- local artifact file paths
- raw XML/JSON payload bodies
- secrets
```

Artifact and evidence rows may show safe metadata such as file name, content
type, size, status, artifact type, and client-safe flags when those fields come
from backend contracts.

## 8. Implementation Rule

When adding a new module operational surface:

```text
1. Confirm the backend endpoint/contract already exposes the data.
2. Map backend data into shared UI props in the module view.
3. Use OperationalPanel for collection loading/empty behavior.
4. Use ArtifactList for compact artifact/evidence/generated-file rows.
5. Use BlockerPanel for blocker summaries.
6. Use ActivityRow for job/activity rows.
7. Keep actions in ActionBar/Button patterns with backend disabled reasons.
8. Add or update tests for the module and static contract.
9. Update this matrix when a module gains a new operational surface.
```

## 9. Guardrails

This contract is enforced by:

```text
frontend/tests/guiModuleOperationalSurfacesContract.test.ts
frontend/tests/operationalPanelPatternContract.test.ts
frontend/tests/operationalListPatternContract.test.ts
frontend/tests/activityRowPatternContract.test.ts
frontend/tests/statePatternContract.test.ts
```

The guardrails keep the contract discoverable, require backend ownership to stay
explicit, and prevent module screens from inventing local operational markup.

## 10. Acceptance Criteria

This contract is accepted when:

```text
- the contract is linked from GUI_CONTRACT_INDEX.md
- the current module matrix is documented
- shared component ownership is explicit
- backend-owned decisions stay out of frontend-only rules
- required operational states are listed
- client-safe content rules are explicit
- static tests cover discoverability and core wording
```
