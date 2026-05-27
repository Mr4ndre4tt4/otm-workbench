# Michelangelo Wireframe Brief - Catalog Core

**Status:** ready for Figma wireframe pass after user scope approval
**Date:** 2026-05-26
**Source scope review:** `docs/agent/module-scope/CATALOG_CORE_SCOPE_REVIEW.md`

## 1. Review Context

Screen/flow type:
Read-only OTM catalog, Data Dictionary, reference, and schema guidance explorer.

Primary user task:
Find whether an OTM macro object, table, column, reference value, or schema path
can be safely used by another module.

User profile:
Functional lead, technical consultant, DBA/MASTER for guarded diagnostics, and
module implementers using Catalog as shared OTM truth.

Task criticality:
High. Wrong Catalog guidance can cause invalid templates, mappings, exports,
load plans, and integration artifacts.

Input reviewed:
Catalog Core route-separation spec, completion review, schema-pack contract
spec, functional validation matrix, and governance rules.

Evidence source:
Repository documentation and recorded QA evidence. No live UI or screenshots
were reviewed in this brief.

Assumptions:
Catalog Core is read-only for normal users. Backend owns labels, readiness,
validation, reference policy, schema guidance role, and confidence.

## 2. Archetypes

- data workspace;
- diagnostic console;
- reference browser;
- technical metadata inspector;
- validation form;
- report/dashboard for schema guidance readiness.

## 3. Route Inventory For Wireframes

```text
/catalog
/catalog/macro-objects/:macroObjectCode
/catalog/tables
/catalog/tables/:tableName
/catalog/reference-options
/catalog/schema-guidance
```

## 4. UX Findings To Design Around

ID:
CAT-UX-01

Severity:
P1 High

Category:
Information architecture

Where:
Catalog hub.

Evidence:
The Catalog spec says the prior hub behaved like a dense inspector with macro
objects, metrics, schema guidance, validation forms, tables, load plan, and
cross-checks competing on one route.

Problem:
If the hub becomes a wall of every catalog capability, users cannot identify
whether they need macro-object, table, reference, or schema guidance.

User impact:
Slow lookup, wrong validation path, and low confidence in Catalog as source of
truth.

Recommendation:
Wireframe `/catalog` as a compact decision hub with macro-object discovery and
clear utility links.

Implementation hint:
Keep deep tables, schema paths, reference lists, and macro-object details on
route-level screens.

Acceptance criteria:
A user can choose the correct Catalog route within one scan of the hub.

---

ID:
CAT-UX-02

Severity:
P1 High

Category:
Feedback, system status, and trust

Where:
Schema guidance and macro-object detail.

Evidence:
The schema-pack validation matrix says XSD/WSDL roots are contract guidance,
while Data Dictionary remains CSV/load-order truth.

Problem:
Wireframes that present schema paths as final functional advice could mislead
users into treating XML contract paths as Data Dictionary load rules.

User impact:
Incorrect templates, mappings, CSV expectations, or implementation advice.

Recommendation:
Show guidance readiness, confidence, source status, and blocked states directly
beside schema links and paths.

Implementation hint:
Use distinct labels such as `Contract guidance`, `Data Dictionary crossed`,
`Oracle official pinned`, `Technical only`, and `Blocked`.

Acceptance criteria:
Users can tell whether a schema recommendation is ready, technical-only, or
blocked.

---

ID:
CAT-UX-03

Severity:
P2 Medium

Category:
Forms and validation

Where:
Table, column, and reference validation.

Evidence:
Catalog route specs require validation panels to show backend error/blocker and
keep recovery action next to the form that caused it.

Problem:
If validation feedback appears far from the inputs, users may not know what to
change.

User impact:
Slower recovery and repeated invalid validation attempts.

Recommendation:
Place validation forms and results in the same bounded region, with a clear
reason and next safe action.

Implementation hint:
Use inline `StatusFeedback` plus a compact `BlockerSummary`; keep raw
technical payloads hidden.

Acceptance criteria:
Unknown table, blocked usage, unknown column, and invalid reference states show
actionable recovery copy next to the input.

## 5. Required Wireframe States

- Catalog hub with macro-object list and utility links;
- empty or unavailable Data Dictionary state;
- macro-object detail with schema links ready;
- macro-object detail with blocked schema links;
- table explorer search result;
- unknown table validation;
- table detail with many columns;
- unknown column validation;
- reference options list with active domain scope;
- reference value outside active domain;
- no schema packs indexed;
- schema guidance readiness summary;
- root selected with path rows;
- path search no results;
- schema indexing hidden or disabled for normal user.

## 6. Wireframe Acceptance Criteria

- Catalog hub stays compact and does not render full detail panels.
- All drill-down routes have visible Back actions.
- Data Dictionary truth and schema guidance are visually distinct.
- Backend-owned confidence/readiness/status labels are shown where decisions
  depend on them.
- Validation results appear beside the relevant form.
- Local file paths, raw schema content, credentials, and real client data are
  not represented.
- Long table, column, root, and XML-path labels wrap or truncate safely.
- Admin-only schema indexing is not exposed as a normal-user action.

## 7. External Validation Recommended

After Figma wireframes exist:

- Michelangelo review against this brief;
- cross-check with schema-pack functional validation matrix;
- verify Catalog does not become an operational module;
- later Playwright validation for route recovery and validation states.
