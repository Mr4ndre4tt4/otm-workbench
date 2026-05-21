# GUI Module Screen Consistency Audit

**Status:** delivered
**Branch:** `codex/gui-module-screen-consistency-audit`
**Linear:** `OTM-67`
**Scope:** consistency audit for implemented backend-backed module screens.

## 1. Purpose

This audit checks the implemented module screens before the GUI expands into
richer module-specific interactions.

The goal is to keep module screens consistent without moving backend-owned
business rules, lifecycle decisions, validation, action availability, evidence,
or artifact decisions into the frontend.

## 2. Audited Modules

```text
Rates Studio
Catalog Core
Load Plan
Assets Library
Evidence Hub
Master Data
Order Release Generator
Integration Mapping Studio
```

## 3. Shared Template Result

All audited backend-backed modules currently use the core module template:

```text
PageHeader
MetricGrid
ModuleWorkspaceLayout
ModuleObjectList
SelectedObjectPanel
DetailList
StatePanel
```

All audited modules provide:

```text
- top-level loading state
- top-level unavailable/error state
- backend-shaped metrics
- selectable object/work queue list
- selected object details panel
- empty list/detail copy through shared components
- local selection state only
```

## 4. Module Matrix

| Module | Core Template | Actions | Blockers | Operational Artifacts/Evidence | Notes |
|---|---|---|---|---|---|
| Rates Studio | Complete | ActionBar + FeedbackMessage | BlockerPanel | OperationalPanel + ArtifactList for artifacts/evidence | Most complete module surface. |
| Catalog Core | Complete | Not surfaced yet | Not surfaced yet | Not surfaced yet | Uses read-only status where backend data supports it. |
| Load Plan | Complete | Not surfaced yet | Not surfaced yet | Not surfaced yet | Good candidate for package artifacts/jobs once backend contracts expose them. |
| Assets Library | Complete | Not surfaced yet | Not surfaced yet | DetailList for versions | May later need ArtifactList/download affordances for asset files. |
| Evidence Hub | Complete | Not surfaced yet | Not surfaced yet | DetailList for artifact/manifest references | May later need ArtifactList for downloadable evidence artifacts. |
| Master Data | Complete | Not surfaced yet | Not surfaced yet | Not surfaced yet | Template/sheet/field structure is consistent. |
| Order Release Generator | Complete | Not surfaced yet | Not surfaced yet | Not surfaced yet | Needs future generated XML/job/artifact surface when backend exposes it. |
| Integration Mapping Studio | Complete | Not surfaced yet | Not surfaced yet | DetailList for payload/schema/mapping rows | Custom schema tree/mapping table should be handled as documented exception later. |

## 5. Consistent Patterns

The current module screens consistently reuse shared GUI primitives instead of
owning raw layout or visual classes:

```text
- no module-specific page shell
- no module-specific palette
- no raw module workspace grid
- no raw selected-object side panel
- no raw loading/error state panel
- no direct import from internal ui/components/* files
```

## 6. Backend Ownership Check

Backend remains the source of truth for:

```text
- module availability and navigation
- lifecycle/status values
- read-only/active states
- validation decisions
- dependency/load order decisions
- available actions and disabled reasons
- artifact/evidence safety and download links
- jobs and progress
```

The frontend currently derives display-only summaries such as:

```text
- selected object id
- effective first selected item
- count-based ACTIVE/EMPTY presentation status
- string lists for metadata rows
```

These are acceptable UI rendering concerns and should not grow into lifecycle or
permission decisions.

## 7. Gaps

### Gap 1 - Operational Surfaces Are Uneven

Only Rates Studio currently shows the fuller operational surface with
`BlockerPanel`, `OperationalPanel`, and `ArtifactList`.

Other modules may need artifacts, evidence, jobs, blockers, or downloads later,
but those should be added only when backend contracts expose the data and
actions.

### Gap 2 - Action Surfaces Are Uneven

Only Rates Studio currently renders selected-object backend actions with
`ActionBar` and feedback through `FeedbackMessage`.

This is acceptable for now if other module contracts do not yet expose
`available_actions`, but the pattern should be standardized once they do.

### Gap 3 - Long-Label/Responsive Regression Coverage Is Mostly Indirect

The component gallery and shared fixtures cover long labels, but the real module
screens do not yet have module-specific long-label regression tests.

This matters most before adding Integration Mapping schema trees, payload paths,
OTM table names, XML/JSON paths, and generated artifact filenames.

### Gap 4 - Browser Visual Evidence Is Still Blocked

The module audit is code/test/document based. It does not claim screenshot or
pixel evidence.

The Browser plugin was attempted during this audit and failed while creating
the browser-control process with:

```text
CreateProcessWithLogonW failed: 1326
```

Browser attempts are tracked separately in:

```text
GUI_GALLERY_VISUAL_QA_ATTEMPT.md
```

## 8. Follow-Up Issues

Concrete follow-up work should stay separate from this audit:

```text
OTM-69 GUI module operational surfaces - artifacts evidence jobs blockers
OTM-70 GUI module action surfaces - backend actions disabled reasons feedback
OTM-71 GUI module long-label responsive regression coverage
```

## 9. Acceptance Criteria

This audit is accepted when:

```text
- every implemented backend-backed module is checked against the shared template
- gaps are documented without bundling speculative fixes
- follow-up issues exist for concrete gaps
- backend ownership remains explicit
- static tests protect the current consistency baseline
```
