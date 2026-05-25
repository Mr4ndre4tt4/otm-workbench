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
- Master Data dynamic template runtime now blocks mapping when dynamic
  relationship rules exist and the batch has not been relationship-validated.
- Dynamic workbook sheets can include relationship-only fields without forcing a
  fake OTM target column.

Tests:

```text
python -m pytest tests/test_master_data_templates.py -q
```

The current pass covers backend scenario validity. Frontend/browser scenario
expansion should reuse this pack by making the Author stage able to construct
these richer scenario templates from Catalog Core selections instead of relying
on hand-built backend payloads.

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
