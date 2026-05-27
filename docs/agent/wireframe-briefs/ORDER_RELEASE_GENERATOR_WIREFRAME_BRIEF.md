# Michelangelo Wireframe Brief - Order Release Generator

**Status:** ready for Figma wireframe pass after user scope approval
**Date:** 2026-05-26
**Source scope review:** `docs/agent/module-scope/ORDER_RELEASE_GENERATOR_SCOPE_REVIEW.md`

## 1. Review Context

Screen/flow type:
Template-guided order release batch generator with XML preview and guarded
submit readiness.

Primary user task:
Choose or create a template, enter order release rows, preview XML, generate an
artifact, and inspect submit readiness.

User profile:
OTM functional consultant, order management lead, implementation tester.

Task criticality:
High. Invalid order release XML can disrupt planning/execution test cycles.

Input reviewed:
Order Release Generator consolidated spec and scope review.

Evidence source:
Repository documentation only. No live UI reviewed.

Assumptions:
Backend owns templates, schema roots, row validation, XML preview, artifacts,
and submit blockers.

## 2. Archetypes

- generator workflow;
- template builder;
- row editor;
- XML preview;
- critical readiness check.

## 3. Route Inventory For Wireframes

```text
/order-release-generator
/order-release-generator/templates/new
/order-release-generator/templates/:templateId
/order-release-generator/templates/:templateId/versions
/order-release-generator/batches/new
/order-release-generator/batches/:batchId
/order-release-generator/batches/:batchId/rows
/order-release-generator/batches/:batchId/preview
/order-release-generator/batches/:batchId/artifacts
/order-release-generator/batches/:batchId/submit-readiness
```

## 4. UX Findings To Design Around

ID:
ORG-UX-01

Severity:
P1 High

Category:
Forms and validation

Where:
Row editor.

Evidence:
The spec says template-guided row editor replaced raw JSON input.

Problem:
Raw JSON entry hides required fields, validation rules, and template defaults.

User impact:
Invalid batches and slower correction.

Recommendation:
Wireframe the row editor as a structured, template-owned form/table with inline
validation and row issue summary.

Acceptance criteria:
Users can identify invalid rows and required fields without reading raw JSON.

---

ID:
ORG-UX-02

Severity:
P1 High

Category:
Feedback and trust

Where:
XML preview and submit readiness.

Evidence:
The spec says raw XML alone is insufficient and submit is guarded.

Problem:
Users may think previewed XML is ready for OTM submission when connection,
credentials, schema, or capability blockers remain.

User impact:
False confidence and unsafe submit expectations.

Recommendation:
Show structured XML summary/provenance and a separate submit readiness route.

Acceptance criteria:
Preview and submit readiness are visually distinct states.

## 5. Required Wireframe States

- no templates;
- template missing schema root;
- no batch rows;
- invalid row;
- preview blocked;
- XML preview ready;
- artifact generated;
- submit blocked;
- submit not implemented/governed.

## 6. Wireframe Acceptance Criteria

- Template and batch flows are separate but linked.
- Row editor is template-guided.
- XML preview includes structured summary, not only raw XML.
- Submit readiness uses backend blockers.
- No real order data appears.

## 7. External Validation Recommended

After Figma:

- Michelangelo review for generator clarity;
- Catalog schema guidance check;
- browser QA plan for invalid row and submit-blocked recovery.
