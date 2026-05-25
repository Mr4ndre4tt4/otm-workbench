# Master Data Functional Scenario QA

**Status:** first backend scenario pack delivered
**Date:** 2026-05-25
**Owner issue:** OTM-119
**Scope:** synthetic OTM-valid Master Data test scenarios for backend and GUI acceptance.

## Purpose

This pack raises Master Data QA from "the module works" to "the module solves
real OTM setup problems with realistic table relationships." Scenarios must be
synthetic, Data Dictionary-backed, and supported by Oracle functional
documentation or explicit user confirmation.

## Source Rules

- Local OTM Data Dictionary 26B is the source of truth for table and column names.
- Oracle Help is used as functional context for setup objects such as TiHi,
  Packaged Item, Ship Unit Spec, Equipment Group Profile, Activity Type
  Capacity, Activity Time Definition, and CSVUtil.
- Tests must not use real client names, locations, identifiers, credentials, or
  payloads.
- Relationship-only workbook fields are allowed when a field is needed to
  validate a same-batch parent/child relationship but is not written to an OTM
  target column.

Oracle Help references consulted:

- <https://docs.oracle.com/en/cloud/saas/transportation/>
- TiHi / Packaged Item / Ship Unit Spec help topics.
- Equipment Group Profile help topics.
- Activity Type Capacity and Activity Time Definition help topics.
- CSVUtil help topics.

## Scenario 1: Operational Location

Goal: prove a Location template can model a usable facility setup instead of
only a flat address upload.

Tables covered:

```text
LOCATION
LOCATION_ADDRESS
LOCATION_CAPACITY
LOCATION_ACTIVITY_TIME_DEF
LOCATION_LOAD_UNLOAD_POINT
EQUIPMENT_GROUP_PROFILE
EQUIPMENT_GROUP_PROFILE_D
```

Functional elements covered:

```text
basic facility identity
address line
calendar-backed capacity reference
activity time definition reference
dock/load-unload point configuration
equipment group profile restriction at location/dock level
equipment group profile detail
same-batch relationship validation before mapping
```

Acceptance:

- dynamic template publishes only after Data Dictionary validation;
- upload parses a synthetic workbook containing all scenario sheets;
- mapping is blocked until dynamic relationship rules are validated;
- relationship validation catches orphan child rows;
- map/build-output/build-csv generates OTM-shaped CSV files for all target tables;
- generated CSV first line is the table name and second line is the OTM column list.

## Scenario 2: Item Packaging

Goal: prove Item setup can cover packaging and TiHi hierarchy, not only a flat
Item row.

Tables covered:

```text
ITEM
SHIP_UNIT_SPEC
PACKAGED_ITEM
TI_HI
```

Functional elements covered:

```text
item identity and type
packaging unit ship-unit spec
transport handling unit ship-unit spec
packaged item linked to item and packaging unit
TiHi sequence linked to packaged item, packaging unit, and transport handling unit
layers and quantity per layer
same-batch relationship validation before mapping
```

Acceptance:

- dynamic template publishes with Data Dictionary and Oracle documentation refs;
- relationship validation requires Item and Ship Unit Spec parents before mapping;
- TiHi output includes `TRANSPORT_HANDLING_UNIT_GID`;
- CSV generation preserves OTM CSV shape and target-column ordering.

## Implementation Notes

Delivered backend changes:

- Catalog Core now classifies Location dependent setup tables as Master Data and
  includes them in the `LOCATION` macro object.
- `GET /api/v1/modules/master-data/scenario-packs` exposes backend-owned
  scenario packs and their complete `draft_payload`.
- Master Data dynamic template runtime now blocks mapping when dynamic
  relationship rules exist and the batch has not been relationship-validated.
- Dynamic workbook sheets can include relationship-only fields without forcing a
  fake OTM target column.
- Backend-owned workbook editor batches now preserve technical metadata rows for
  dynamic mappings that infer sheet ownership from field metadata.
- Relationship-only target columns are parsed as intentional blanks instead of
  data rows.
- Master Data CSV generation now orders output files by
  `target_tables.sequence`, allowing the sheet/story order to stay user-friendly
  while the CSV/Load Plan order follows Data Dictionary dependencies.
- The Author stage can apply a backend-owned scenario pack, show its objective,
  target-table flow, documentation basis, and create the draft from the server
  payload without duplicating the mapping rules in frontend state.
- The Operational Location scenario now reaches Load Plan package intake, ZIP
  analysis, and Cutover readiness with no ZIP analysis structure errors; readiness
  remains blocked only by pending cutover checklist work.
- The Item Packaging scenario now reaches Load Plan package intake, ZIP
  analysis, and Cutover readiness with no ZIP analysis structure errors,
  preserving the `ITEM`, `SHIP_UNIT_SPEC`, `PACKAGED_ITEM`, `TI_HI` technical
  sequence and `TRANSPORT_HANDLING_UNIT_GID` coverage.

Tests:

```text
python -m pytest tests/test_master_data_templates.py -q
python -m pytest tests/test_load_plan_package_intake.py::test_operational_master_data_package_reaches_zip_analysis_and_cutover_readiness -q
python -m pytest tests/test_load_plan_package_intake.py::test_item_packaging_master_data_package_reaches_zip_analysis_and_cutover_readiness -q
npm run test -- AppFunctionalMasterData.test.tsx
npm run qa:functional:master-data:browser
```

The current pass covers backend scenario validity, the React functional GUI
slice, and the browser journey against local FastAPI + Vite. The browser path
selects the backend-owned Location and Item Packaging scenario packs, verifies
each scenario story and hidden manual authoring controls, creates/validates/
publishes each scenario draft, and resets authoring before continuing through
the manual template and batch/export handoff journey.

## Replication Rule For Other Modules

Every module should get an equivalent scenario pack:

```text
1. define real functional scenario;
2. list Data Dictionary tables and dependencies;
3. cite Oracle Help or user-confirmed functional assumptions;
4. create synthetic positive backend flow;
5. create negative/out-of-order backend flow;
6. add GUI journey that performs the same story without stacked disconnected screens;
7. update Linear and GitHub before moving to the next scenario.
```
