# Schema Pack Functional Validation Matrix

**Status:** hardening started
**Date:** 2026-05-25
**Linear:** `OTM-163` follow-up track
**Related spec:** `docs/otm-workbench/modules/schema_pack_contract_catalog_spec.md`

## Objective

Validate the high-value OTM 26A schema roots and path guidance before they are
shown to users as functional advice in Integration Mapping Studio, Order Release
Generator, Master Data Template Factory, and Rates Studio.

The Schema Pack parser can tell us what exists in XSD/WSDL. It cannot, by
itself, prove that a path is the right implementation pattern for a tariff,
master data template, or integration scenario. This matrix records which roots
are safe to use now, which need Data Dictionary cross-checks, and which need
Oracle official documentation or user confirmation.

## Guardrails

```text
- Do not commit raw WSDL/XSD content, endpoint addresses, local source paths,
  client names, credentials, payloads, or environment identifiers.
- Data Dictionary remains the operational source of truth for CSVUtil tables,
  columns, dependencies, and load order.
- XSD/WSDL roots are companion contract guidance for XML, mapping, validation,
  and documentation hints.
- Oracle official documentation is required before turning uncertain OTM
  behavior into UI guidance.
- Any remaining uncertainty must stay marked as USER_CONFIRMATION_NEEDED.
- Evidence must store client-safe source references and validation summaries,
  not raw customer data.
```

## Official References Pinned So Far

| Area | Oracle reference | Current use |
|---|---|---|
| Integration | [Integration Overview](https://docs.oracle.com/en/cloud/saas/transportation/25c/otmit/integration-overview.html) | Confirms Transmission XML as a primary integration message and separates business-process integration from data-tier integration. |
| CSVUtil / Data Management | [Loading CSV Data via the User Interface](https://docs.oracle.com/en/cloud/saas/transportation/26a/otmdm/loading-csv-data-via-user-interface.html) | Confirms CSV upload is a Data Management / Integration Manager path and keeps CSV-specific rules outside XSD inference. |
| Rates | [Rate Offering](https://docs.oracle.com/en/cloud/saas/transportation/26a/otmol/planning/rate_manager/create_rate_offering.htm?agt=index) | Confirms Rate Offering as the contractual/rating header and its relationship to rate records, constraints, equipment, service provider, and qualification. |
| Rates | [Rate Record](https://docs.oracle.com/en/cloud/saas/transportation/25c/otmol/planning/rate_manager/create_rate_record.htm) | Confirms rate records depend on rate offerings and hold lane/cost details. |
| Master Data - Item | [Packaged Item](https://docs.oracle.com/en/cloud/saas/transportation/25c/otmol/planning/material_manager/create_pack_info.htm) | Confirms item, packaged item, packaging unit, TiHi, weight/volume, and shipping setup relationship. |
| Master Data - Location | [Location Transport Handling Unit Capacity](https://docs.oracle.com/en/cloud/saas/transportation/26a/otmol/planning/location_manager/location_transport_handling_unit_capacity.htm) | Confirms location-specific THU capacity constraints and TiHi/full-layer handling guidance. |
| Order Release | [Order Management](https://docs.oracle.com/en/cloud/saas/transportation/26a/otmol/configuration/setting_up_otm/order_management.htm) | Confirms order release as the transportation requirement used for planning and execution. |
| Order Release | [Order Releasing Process](https://docs.oracle.com/en/cloud/saas/transportation/25c/otmol/planning/order_manager/create_order_release.htm) | Confirms release split/use cases and relationship to order bases/release instructions. |

## Validation Matrix

| Module | Root / contract | Data Dictionary tables to cross-check | Oracle status | Backend contract status | Use now | Blocked until |
|---|---|---|---|---|---|---|
| Integration Mapping Studio | `Transmission` | Not table-driven; map to XML integration metadata and payload roots | ORACLE_OFFICIAL_PINNED | Delivered via `source_schema_root_id` / `target_schema_root_id` | Yes, as XML envelope/path browser | UI guidance must label it as XML contract, not CSV load order |
| Integration Mapping Studio | `PlannedShipment` / `Shipment` paths | Shipment domain tables only when mapping to CSV/DB artifacts | ORACLE_OFFICIAL_PINNED | Delivered as generic root reference and Catalog Core `SHIPMENT` macro object | Yes, for sample/path browsing | Functional mapping recipes need scenario evidence and path-level review |
| Integration Mapping Studio | External target schemas | Not OTM Data Dictionary | USER_CONFIRMATION_NEEDED | Delivered as generic root reference | Yes, if synthetic/non-client target contract | Do not infer business semantics without user-provided spec |
| Order Release Generator | `Transmission` + `Release` | `ORDER_RELEASE` family, release lines/ship units, locations, items, refnums | ORACLE_OFFICIAL_PINNED | Delivered via template `transmission_schema_root_id` and `release_schema_root_id` | Yes, for XML preview envelope summary | Scenario generator still needs Data Dictionary-backed field/table mapping for CSV/db.xml companions |
| Master Data Template Factory | `Location` | `LOCATION`, address/contact/refnum/capacity/activity time/dock/equipment profile related tables | ORACLE_OFFICIAL_PARTIAL | Delivered via `schema_root_ids` | Yes, as authoring hint only | Template generation must use Data Dictionary table dependencies before marking complete |
| Master Data Template Factory | `Item`, `ItemMaster`, packaged item, ship unit spec paths | `ITEM`, packaged item, TiHi/package, ship unit specification related tables | ORACLE_OFFICIAL_PINNED | Delivered via `schema_root_ids` | Yes, as authoring hint only | Field aliases/fixed values/n-to-n mappings need tested table-level exports |
| Rates Studio | `RATE_OFFERING` | `RATE_OFFERING`, rate version/service/mode/provider/equipment/capacity/accessorial references | ORACLE_OFFICIAL_PINNED | Delivered via batch `schema_root_ids` | Yes, as XML companion evidence | CSV sequencing remains Data Dictionary-only |
| Rates Studio | `RATE_GEO` | Rate record/lane/cost/accessorial/unit-break related tables | ORACLE_OFFICIAL_PINNED | Delivered via batch `schema_root_ids` | Yes, as XML companion evidence | Path aliases must handle XSD `RATE_GEO` versus user-facing `RateGeo` naming |
| Rates Studio | `X_LANE` | Lane/geography dependency tables | ORACLE_OFFICIAL_PARTIAL | Supported as a root if indexed | Limited, root visible only | Need Data Dictionary and Oracle functional confirmation before UI guidance |
| Catalog Core | `SchemaRoot` / `SchemaPath` / `ServiceOperation` | Macro-object links to Data Dictionary tables | TECHNICALLY_VALIDATED | APIs delivered read-only | Yes, as backend-owned catalog | Functional confidence field needed before UI exposes recommendations |
| Assets / Evidence / Jobs | Schema packs and index jobs | Not table-driven | TECHNICALLY_VALIDATED | Indexing/evidence delivered | Yes, client-safe summaries only | Asset promotion and retention policy before multi-project sharing |

## Naming And Alias Normalization

The XSD root names are not always the names users expect in the UI or the names
used in CSV/table conversations.

Recommended backend-owned alias examples:

| Canonical schema root | User-facing label | CSV/Data Dictionary family |
|---|---|---|
| `RATE_OFFERING` | Rate Offering | `RATE_OFFERING` |
| `RATE_GEO` | Rate Record / Rate Geo | rate record and lane/cost families |
| `X_LANE` | Lane | lane/geography families |
| `Release` | Order Release | order release families |
| `PlannedShipment` | Planned Shipment | shipment/integration payload family |
| `Location` | Location | location/address/contact/capacity families |
| `Item` / `ItemMaster` | Item / Item Master | item/packaged item/ship unit setup families |

Aliases should live in backend-owned metadata so future GUIs, desktop apps, and
automation jobs consume the same vocabulary.

Backend status:

```text
- `GET /api/v1/catalog/schema-roots` now returns `root_display_label`,
  `canonical_root_name`, `schema_root_aliases`, and `data_dictionary_family`.
- The `root_name` filter accepts known aliases such as `RateGeo` and resolves
  them to canonical XSD roots such as `RATE_GEO`.
- Macro-object schema links return the same root naming metadata.
- `GET /api/v1/catalog/macro-objects/{code}/data-dictionary-cross-check`
  returns target table validation plus linked schema roots and source-reference
  readiness without exposing schema pack source paths.
- Cross-check summaries expose `guidance_ready` and `readiness_status`; a macro
  object with zero schema links is `BLOCKED_SCHEMA_LINKS`.
- Schema Pack indexing auto-links known roots to macro objects only when the
  source reference is pinned and client-safe.
- `GET /api/v1/catalog/schema-guidance/readiness` summarizes guidance readiness
  across macro objects for dashboards and backlog triage.
- Catalog Core now seeds `ORDER_RELEASE` as a transactional macro object for
  XML/schema guidance, blocked for CSVUtil/cutover in MVP0.
- Catalog Core now seeds `SHIPMENT` as a transactional macro object for
  Integration Mapping XML/schema guidance, blocked for CSVUtil/cutover in MVP0.
- `Transmission` is explicitly serialized as `ENVELOPE_ONLY`, not as a macro
  object, so it can support XML envelope browsing without implying table load
  guidance.
- `GET /api/v1/catalog/schema-roots` supports `schema_guidance_role` filtering
  so the UI can stage envelopes separately from macro-object roots.
```

## Next Hardening Slices

```text
1. Add a functional-confidence field to schema-root/module links:
   TECHNICAL_ONLY, ORACLE_OFFICIAL_PINNED, DATA_DICTIONARY_CROSSED,
   USER_CONFIRMED, BLOCKED.
   Status: backend field/API slice started in OTM-164.
2. Add source references to evidence records using safe URLs and document
   labels, not copied Oracle content or raw local files.
3. Build a Data Dictionary cross-check report for Location, Item, Rate Offering,
   Rate Geo, Release, and Planned Shipment macro objects.
   Status: first backend endpoint slice started in OTM-164.
4. Add root alias normalization so APIs can present user-friendly labels while
   preserving canonical XSD names.
   Status: backend serializer/filter slice started in OTM-164.
5. Only after the above, define the UI path-picker/guidance contract.
```

## Roadmap Issues To Track

```text
- Validate high-value Schema Pack roots against Data Dictionary and Oracle docs.
- Add functional confidence and source reference metadata to schema links.
- Normalize SchemaRoot aliases for Rates, Master Data, Order Release, and
  Integration Mapping.
- Design UI path picker as a staged workflow: choose pack, choose root, inspect
  paths, link to module, review evidence.
- Add scenario QA using synthetic data for Location, Item/Packaged Item, Rate
  Offering/Rate Geo, Order Release, and the NDD-style integration mapping.
```
