# Michelangelo Wireframe Brief - Master Data / Data Factory

**Status:** ready for Figma wireframe pass after user scope approval
**Date:** 2026-05-26
**Source scope review:** `docs/agent/module-scope/MASTER_DATA_DATA_FACTORY_SCOPE_REVIEW.md`

## 1. Review Context

Screen/flow type:
Modular data-preparation workbench with operational workflow, authoring
workflow, and quality utility workflow.

Primary user task:
Prepare OTM master-data load packages safely, or administer reusable templates,
without confusing operational data prep with template authoring.

User profile:
Functional OTM consultant, implementation lead, and authorized template
administrator.

Task criticality:
High. Wrong mappings, dependency errors, or unsafe exports can cause failed OTM
loads and project rework.

Input reviewed:
Validated module scope, Master Data redesign spec, dynamic template factory
spec, completion review, and governance rules.

Evidence source:
Repository documentation and recorded QA evidence. No live UI or screenshots
were reviewed in this brief.

Assumptions:
Backend owns lifecycle, actions, validation, disabled reasons, and artifact
metadata. Figma wireframes will define target UX, not copy the current UI.

## 2. Archetypes

- data workspace;
- workflow/wizard;
- CRUD form;
- critical operation;
- artifact/library manager;
- diagnostic/result review for quality batches.

## 3. Route Inventory For Wireframes

```text
/master-data
/master-data/factory
/master-data/factory/templates/:templateCode
/master-data/factory/batches/:batchId
/master-data/template-builder
/master-data/template-builder/new
/master-data/template-builder/:templateCode
/master-data/template-builder/:templateCode/edit
/master-data/template-builder/:templateCode/copy
/master-data/template-builder/:templateCode/delete
/master-data/quality
/master-data/quality/lat-lon
/master-data/quality/lat-lon/batches/:batchId
```

## 4. UX Findings To Design Around

ID:
MD-UX-01

Severity:
P1 High

Category:
Information architecture and workflow sequencing

Where:
Master Data module entry and first-level navigation.

Evidence:
The redesign spec states the previous screen mixed operational Data Factory,
Template Builder, and Quality Tools in one staged workflow.

Problem:
Users can mistake template authoring and coordinate quality for mandatory steps
in operational CSV package generation.

User impact:
Wrong task path, avoidable errors, and slower onboarding.

Recommendation:
Wireframe `/master-data` as a clear three-choice hub with recent activity
secondary and no deep workflow controls.

Implementation hint:
Use three route cards with backend-owned counts/status and one visible primary
destination per card.

Acceptance criteria:
A new user can explain the difference between Data Factory, Template Builder,
and Quality Tools from the hub alone.

---

ID:
MD-UX-02

Severity:
P1 High

Category:
Error prevention and recovery

Where:
Batch execution detail.

Evidence:
The spec requires output and CSV actions to be disabled with backend reasons
when validation is missing or blocked.

Problem:
If future wireframes show every action as equally available, users will learn
by failure instead of by visible readiness.

User impact:
Repeated failed clicks and potential wrong export decisions.

Recommendation:
Design batch detail around a `BlockerSummary`, backend-owned available actions,
and stage-specific disabled reasons.

Implementation hint:
Each stage should have a compact status band, primary action, disabled action
reason, and persisted artifact/evidence area.

Acceptance criteria:
The wireframe shows what is blocked and why before the user clicks.

---

ID:
MD-UX-03

Severity:
P2 Medium

Category:
Forms and validation

Where:
Template Builder create/edit.

Evidence:
The dynamic template factory supports N tables, fields, mappings, fixed values,
defaults, relationship rules, documentation refs, and publish validation.

Problem:
A single giant form would make advanced authoring technically complete but
operationally hard to reason about.

User impact:
Higher mapping mistakes and lower trust in template publishing.

Recommendation:
Wireframe Template Builder as a staged authoring workspace with dense tables,
review summaries, and validation blockers.

Implementation hint:
Use Basics, Tables, Fields, Mapping, Review as wizard sections, with a sticky
action bar and clear Back/Cancel behavior.

Acceptance criteria:
Users can see what remains invalid before publishing and can return to the
exact section that needs correction.

## 5. Required Wireframe States

- empty Master Data hub;
- no published templates;
- template detail with available workbook action;
- template detail with upload intent;
- batch before validation;
- batch blocked by relationship validation;
- batch ready for CSV export;
- batch export complete with Load Plan registration;
- Template Builder empty list;
- Template Builder search with normalized filters;
- new template draft validation blockers;
- edit published template requiring draft or next version;
- copy template review;
- delete/retire blocked by active batches;
- Quality Tools empty state;
- Lat/Lon validation result with export available.

## 6. Wireframe Acceptance Criteria

- Operational, authoring, and quality workflows are visually and navigationally
  separate.
- Each detail/edit/copy/delete/result route has a visible return path.
- Primary actions are visible without scrolling to the bottom of long content.
- Dense tables are used for tables, fields, mappings, and validation rows.
- Blocked actions show backend-owned reasons.
- Artifact and evidence references do not expose local paths.
- No real client data appears in examples.
- Mobile/narrow layouts keep long OTM table and field labels from overlapping.

## 7. External Validation Recommended

After Figma wireframes exist:

- Michelangelo review against this brief;
- route-by-route checklist against the redesign spec;
- browser QA plan update for happy, negative, out-of-order, and recovery paths;
- later Playwright validation once implemented.
