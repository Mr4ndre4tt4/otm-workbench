# Test Scenario And Fixture Strategy

**Status:** active planning baseline
**Date:** 2026-05-27

## Purpose

Every module delivery must include planned test scenarios and valid synthetic
fixture files when the module needs import/export, document, payload, or
artifact behavior.

The fixture suite should prove the real operational workflow, not only render
happy-path UI examples.

## Universal Rules

- Use synthetic data only.
- Include explicit `client/domain`, `environment`, and visibility/access-policy
  scope in operational fixture records.
- Large files are required when performance, pagination, streaming, ZIP
  packaging, validation summaries, or browser responsiveness are part of the
  risk.
- OTM CSV fixtures must follow OTM CSV shape:
  - line 1: table name;
  - line 2: columns;
  - values after columns;
  - when date columns exist, emit the `exec alter session ...` date format line
    before values.
- Validate OTM table dependencies, required fields, and load-order uncertainty
  through the Data Dictionary and official Oracle documentation.
- Store generated test fixtures in a dedicated synthetic fixture location chosen
  by the implementation plan. Do not place real client exports in the repo.

## Baseline Scenario Matrix

Every active module should cover:

| Scenario family | Required examples |
|---|---|
| Happy path | User can complete the primary workflow with scoped synthetic data. |
| Negative input | Invalid required fields, invalid files, malformed payloads, bad references. |
| Out-of-order | User tries export, approval, handoff, submit, or publish before prerequisites. |
| Permission | Normal user denied, scoped user allowed, `DBA` visible override where applicable. |
| Context isolation | Same object names across two domains/environments do not leak. |
| Route recovery | Stale IDs, missing IDs, direct deep links, session-ended recovery. |
| Repeated action | Duplicate submit/download/export clicks are guarded. |
| Selection change | Mid-flow object/context changes reset dependent state safely. |
| Generated artifact | Output content is valid and matches module parity rules. |
| Evidence | Artifacts, screenshots, and audit events are client-safe and scoped. |

## Fixture Types By Module

| Module | Fixture types |
|---|---|
| Settings | `json`, `csv`, `md` for scoped projects, client/domains, environments, users, roles, grants, access policies, and audit exports. |
| Cockpit | `json`, `md`, optional `pdf` for project-info references, public/private context examples, accelerator permissions, session recovery, and secure-vault metadata placeholders. |
| Rates Studio | OTM-shaped `csv`, large `csv`, `zip`, `json`, `md`, optional `pdf` for rate batches, staged tables, validation reports, approval notes, generated CSVUTIL packages, and Load Plan handoff. |
| Assets Library | `pdf`, `docx`, `md`, `json`, `csv`, `xml`, image-like binary placeholder if needed, plus version/checksum metadata for guarded download and archive tests. |
| Master Data / Data Factory | OTM-shaped `csv`, workbook-like fixtures where supported, large `csv`, `zip`, `json`, `md`, and validation reports for template builder, upload, export, and Quality Tools. |
| Integration Mapping | `xml`, `xsd`, `xslt`, `json`, `md`, large payload samples, generated spec `md`, and mapping validation evidence. |
| Order Release Generator | `xml`, `json`, `csv`, `md`, large batch rows, XML preview artifacts, row-level invalid cases, and submit-readiness reports. |
| Load Plan | `zip`, OTM-shaped `csv`, `json`, `md`, `pdf` or `docx` handoff packets, checklist evidence, readiness exports, sequence files, and go/no-go records. |

## Synthetic Fixture Location

Baseline synthetic fixtures live under:

```text
tests/fixtures/synthetic/
```

Current baseline files:

| File | Module | Purpose |
|---|---|---|
| `manifest.json` | cross-module | Fixture manifest with synthetic scope metadata. |
| `rates/rate_geo_cost.csv` | Rates / Load Plan | OTM-shaped CSV with date session line. |
| `integration/planned_shipment.xml` | Integration Mapping | Source XML payload. |
| `integration/delivery_payload.json` | Integration Mapping | Target JSON payload. |
| `integration/shipment_to_delivery.xslt` | Integration Mapping | Minimal valid XSLT transform. |
| `order-release/order_release_batch.json` | Order Release | Synthetic batch rows. |
| `master-data/location_upload.xlsx` | Master Data | Workbook upload baseline. |
| `assets/client_safe_note.md` | Assets | Client-safe markdown asset. |
| `assets/client_safe_asset.docx` | Assets | Client-safe DOCX asset. |
| `load-plan/cutover_handoff.md` | Load Plan | Handoff note baseline. |
| `load-plan/cutover_handoff.pdf` | Load Plan | Handoff packet baseline. |
| `load-plan/csvutil_package.zip` | Load Plan | CSVUTIL-style package baseline. |

These files are intentionally small. Large/performance fixtures must be created
inside module-specific scenario folders when the module slice needs them.

## Module Revalidation Template

Before implementation starts for a module, create or update a module test plan
with:

```text
Module:
Desired user outcome:
Primary object:
Required Figma board:
Required routes/states:
Required backend contracts:
Required fixture files:
Data Dictionary checks:
Oracle documentation checks:
Happy scenarios:
Negative scenarios:
Out-of-order scenarios:
Permission scenarios:
Context-isolation scenarios:
Generated artifact assertions:
Browser QA scenarios:
Evidence to capture:
Known gaps:
```

## Oracle And Data Dictionary Gate

Use the Data Dictionary first for table names, columns, dependencies, load
order, and CSV shape. Use official Oracle documentation for functional behavior
or technical ambiguity that the Data Dictionary does not answer.

If neither source confirms the behavior, record the assumption in the module
test plan and do not treat the module as complete.
