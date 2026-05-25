# General Solution QA - 2026-05-25

**Scope:** module-level solution assessment, functional web QA, UX architecture review, and pipeline updates.

**Environment:**

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`
- Browser QA user: `demo@example.test`
- Data policy: synthetic data only; no real client data used.

## 1. Executive Assessment

The application is no longer a set of disconnected prototype screens. The main
modules now follow a consistent shell, backend-owned navigation, light/default
theme, staged workflows, object detail panels, guarded actions, and route return
state.

The functional baseline is strong for MVP0: automated browser journeys passed
for all implemented modules, and React functional tests passed.

The main remaining risk is product clarity, not basic functionality. Several
modules technically work, but some first states still require the user to infer
the next operational action from a stage list. The next hardening round should
make every module answer, in the first viewport:

```text
Where am I?
What object am I working on?
What is the next recommended action?
Why is it blocked, if blocked?
What evidence/artifact will this action create?
```

## 2. Verification Evidence

### Browser Functional QA

After seeding the local synthetic demo user, the full browser journey set passed:

```text
qa:functional:shell:browser                  passed
qa:functional:rates:browser                  passed
qa:functional:catalog:browser                passed
qa:functional:master-data:browser            passed
qa:functional:coordinate-quality:browser     passed
qa:functional:load-plan:browser              passed
qa:functional:assets:browser                 passed
qa:functional:evidence:browser               passed
qa:functional:order-release:browser          passed
qa:functional:integration-mapping:browser    passed
qa:functional:admin:browser                  passed
```

The first browser attempt failed before application interaction because the
local backend did not contain `demo@example.test / DemoPass123!`. This is a
reproducibility gap in QA/dev setup, not a module UI regression. It was captured
as `OTM-141` and addressed with an explicit local CLI bootstrap command:

```powershell
python -m otm_workbench.cli bootstrap-qa-user
```

### React Functional QA

```text
npm run qa:functional
Test Files: 11 passed
Tests: 18 passed
```

The run emitted the known jsdom warning:

```text
Not implemented: navigation to another Document
```

No failing React functional tests were observed.

### Manual Web Review

The in-app browser loaded the main routes and reported no console errors for:

```text
/home
/rates
/catalog
/master-data
/load-plan
/assets
/evidence
/order-release-generator
/integration-mapping
/admin
```

The in-app browser screenshot command timed out twice during this run. External
Playwright screenshots were captured outside the repository under a local temp
folder for visual inspection. They are not committed because they are QA
artifacts, not product source.

## 3. Module Assessment

| Module | Functional status | UX/product assessment | Main gap |
|---|---|---|---|
| Shell / Project Cockpit | Browser QA passed | Solid shell, preferences, context panel, navigation and empty state. | Needs reproducible demo seed for local QA; context onboarding should be more explicit for a clean DB. |
| Rates Studio | Browser QA passed | Strong object list/detail workflow and a good reference implementation. | List density can degrade after many QA-generated batches. |
| OTM Catalog Core | Browser QA passed | Clear validation-oriented utility with backend-owned table/column/reference checks. | Good MVP0 slice; future value depends on deeper guided reference browsing only if needed. |
| Master Data / Data Factory | Browser QA passed | Broadest workflow and meets current acceptance scope, including templates, workbook, upload, output, export, direct import guard, Load Plan handoff, and backend-owned next-action guidance from template/batch actions. | Advanced spreadsheet audit remains future. |
| Coordinate Quality | Browser QA passed | Correctly embedded in Data Factory as a quality stage rather than a detached module. | External provider governance and map diagnostics remain future. |
| Load Plan / Cutover | Browser QA passed | Functional and valuable end-to-end; CSVUTIL, readiness, review, exports, Go/No-Go, handoff, and next-action guidance are connected. Out-of-order chaos QA now confirms package switching clears checklist items, readiness counts, CSVUTIL artifact ids/rows, dirty evidence draft, and stale success feedback. | Dedicated backend `available_actions` for cutover packages should replace the temporary UI-derived next-action sequence later. |
| Assets Library | Browser QA passed | Staged lifecycle is much improved; create/version/link/lifecycle make sense. Out-of-order chaos QA now confirms dirty metadata drafts, selected upload files, and link target drafts do not leak when the selected asset changes. | High-volume target/evidence lists need density and filtering hardening later. |
| Evidence Hub | Browser QA passed | Useful for client-safe evidence review, download and archive creation. | Archive drill-down and high-volume filtering are future improvements. |
| Order Release Generator | Browser QA passed | Good generator workflow for template -> batch -> preview -> artifact -> guarded submit. Out-of-order chaos QA now confirms template switching clears active batch, stale preview, stale submit guard, stale extra row, previous-template-only fields, and previous row values. | Richer row/template authoring and governed submit remain future. |
| Integration Mapping Studio | Browser QA passed | Backend is materially stronger after executable preview slices; UI can author and validate rules, the Rules stage has grouped review, join-binding authoring/review is visible, alias-backed mappings can be selected in the UI, invalid mappings can be removed through a backend-owned action, required target scenario packs are visible as a checklist, response handling rules are backend-owned and visible in review/spec output, guided transform config authoring exists for CONSTANT, DATE_FORMAT, FILTER_BY_QUALIFIER, and COUNT_DISTINCT, schema node search and backend-owned mapping suggestions reduce path-hunting, suggestion scoring now handles exact matches, ambiguous exact matches, and first OTM-context semantics, and the preview engine executes first-slice qualifier extraction, count-distinct aggregation, explicit multi-hop join-binding provenance, mixed header + loop alias mappings, loop-scoped lookup values, constant values, date formatting, and artifact-level executable JSON assertions for the synthetic NDD-like browser scenario. | To become a full accelerator for NDD-like mappings, it still needs broader Catalog/Data Dictionary synonym coverage, richer schema path facets, and dedicated aggregation objects if needed. |
| Admin Console | Browser QA passed | Functional setup, capability, feature flag, jobs and audit visibility. | Advanced edit/delete/pagination and volume management remain future. |

## 4. Findings Added To Pipeline

| Linear | Priority | Finding |
|---|---:|---|
| `OTM-141` | High | Browser functional scripts require a synthetic demo user, but local backend does not seed it automatically or document a command. |
| `OTM-142` | High | Staged modules need a backend-owned next-action panel so users do not infer the workflow from steps alone. First slice delivered for Data Factory and Load Plan. |
| `OTM-143` | Medium | Operational lists become noisy after seeded QA volume; need stronger filters, density and truncation. |
| `OTM-144` | High | Integration Mapping needs a grouped executable review table for NDD-like mappings. First slice delivered in the Rules stage. |
| `OTM-145` | High | Integration Mapping backend needed cross-collection multi-hop joins, qualifier filters and aggregations. First slice delivered for FILTER_BY_QUALIFIER and COUNT_DISTINCT; multi-hop joins moved to explicit binding follow-up `OTM-147`. |
| `OTM-147` | High | Backend join-binding contract delivered for multi-hop relationships and scalar preview provenance. |
| `OTM-148` | High | Staged Rules UI authoring/review delivered for Integration Mapping join bindings. |
| `OTM-149` | High | Scalar downstream mappings can read from join-binding aliases, and missing aliases block executable preview instead of falling back to global XML traversal. |
| `OTM-150` | High | Loop-scoped target mappings can read from join-binding aliases and materialize `Entregas[]` rows with source/target item provenance. |
| `OTM-151` | High | Alias-backed mappings now validate missing/out-of-scope aliases and the UI exposes an alias source selector during mapping authoring. |
| `OTM-152` | High | Synthetic NDD-like browser scenario now downloads and inspects executable preview artifacts for mixed header + `Entregas[]` alias mappings and loop-scoped lookup output. |
| `OTM-153` | High | Negative browser QA delivered for Integration Mapping alias/path recovery, blocked preview messaging, backend-owned mapping removal, and correction without route reload. |
| `OTM-154` | High | Required target scenario-pack checklist delivered for synthetic NDD-like Integration Mapping validation and browser recovery. |
| `OTM-155` | High | Backend-owned Integration Mapping response handlers delivered with schema-path validation, Rules-stage authoring/review, generated spec rows, and browser QA. |
| `OTM-156` | Medium | Guided transform config authoring delivered for CONSTANT and DATE_FORMAT, with React functional QA and browser preview artifact assertions. |
| `OTM-157` | Medium | Guided transform config authoring delivered for FILTER_BY_QUALIFIER and COUNT_DISTINCT, with React functional QA and browser preview artifact assertions. |
| `OTM-158` | Medium | Schema node search and deterministic mapping suggestions delivered for Integration Mapping Rules stage, with React/browser QA. |
| `OTM-159` | Medium | Integration Mapping suggestions moved to a backend-owned contract with schema ownership validation, explicit Rules-stage load/apply UI, React QA, and browser QA. |
| `OTM-160` | Medium | Integration Mapping backend suggestion scoring now covers exact matches, ambiguous exact matches, and first OTM-context suggestions for stop sequence and refnum access key scenarios. |
| `OTM-146` | Medium | Add destructive/out-of-order browser journeys by module to test human recovery behavior. Integration Mapping, Load Plan, Assets Library, and Order Release Generator chaos slices delivered through `npm run qa:chaos:browser`. |

## 5. Recommended Next Queue

1. Fix QA/dev reproducibility first: `OTM-141`.
2. Browser-QA the `NextActionPanel` first slice and then roll it out to the next staged modules: `OTM-142`.
3. Continue Integration Mapping accelerator hardening: broader Catalog/Data Dictionary synonym coverage, schema path facets, and complex expression usability.
4. Continue chaos/out-of-order browser QA for Data Factory: `OTM-146`.
5. Harden list density and high-volume states: `OTM-143`.

## 6. Acceptance Bar Going Forward

For each module, `tests pass` is not enough. A module should be considered ready
only when:

```text
- Backend owns rules, permissions, lifecycle and available actions.
- UI has a clear primary object and next action.
- Empty, blocked, invalid, success and return-state behavior are tested.
- Browser QA includes at least one negative or out-of-order path.
- Generated artifacts/evidence are visible and client-safe.
- Documentation records what is complete and what remains explicit future scope.
```
