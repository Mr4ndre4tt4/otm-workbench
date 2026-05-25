# OTM 26A WSDL/XSD Discovery

**Status:** phase 3 crosswalk in progress
**Linear:** `OTM-162`  
**Source folders:**

```text
C:\Users\Enzo Trabalho\Documents\Projetos\OTM General\Integration\wsdl\26a-GenericNameSpace
C:\Users\Enzo Trabalho\Documents\Projetos\OTM General\Integration\xsd\26A
```

## Guardrails

This discovery uses local OTM 26A WSDL/XSD contract files only. It does not use
client-specific payload values.

Findings must be validated technically and functionally before they become
solution roadmap issues.

## Phase Plan

```text
1. Technical inventory: files, namespaces, imports, services, operations,
   root elements, and type counts.
2. Functional domain map: Transmission, Shipment, Order, Rate, Item,
   Location/Contact, Finance, GTM, DBXML/GenericTransaction, and services.
3. Extract reusable contracts: schema path catalog, field cardinality,
   enumerations, service payloads, integration mapping helpers, generators,
   and validators.
4. Module insights: Integration Mapping, Order Release Generator, Rates,
   Master Data, Catalog Core, Assets/Evidence, Jobs/Processing.
5. Validation and roadmap: compare against Data Dictionary and Oracle
   functional docs where needed, then create/update roadmap issues.
```

## Phase 1 - Technical Inventory

### WSDL Services

| WSDL | Target namespace | Service | Operations |
|---|---|---|---|
| `AgentService.wsdl` | `http://xmlns.oracle.com/apps/otm/AgentService` | `AgentService` | `processAgent` |
| `CommandService.wsdl` | `http://xmlns.oracle.com/apps/otm/CommandService` | `CommandService` | `xmlExport`, `xmlImport`, `exportProjectDefinition`, `exportObjectGroup` |
| `DriverService.wsdl` | `http://xmlns.oracle.com/apps/otm/DriverService` | `DriverService` | `processAction` |
| `MessageService.wsdl` | `http://xmlns.oracle.com/apps/otm/MessageService` | `MessageService` | `receiveMessage`, `receiveMessageAck` |
| `OrderMovementService.wsdl` | `http://xmlns.oracle.com/apps/otm/OrderMovementService` | `OrderMovementService` | `processAction` |
| `OrderReleaseService.wsdl` | `http://xmlns.oracle.com/apps/otm/OrderReleaseService` | `OrderReleaseService` | `processAction` |
| `SellSideShipmentService.wsdl` | `http://xmlns.oracle.com/apps/otm/SellSideShipmentService` | `SellSideShipmentService` | `processAction` |
| `TransmissionService.wsdl` | `http://xmlns.oracle.com/apps/otm/TransmissionService` | `TransmissionService` | `execute`, `publish` |

First interpretation:

```text
- TransmissionService is the broad XML integration entry point.
- CommandService is important for DBXML import/export and project/object-group
  export scenarios.
- Agent/Driver/OrderMovement/OrderRelease/SellSideShipment services expose
  action-oriented contracts backed by AgentService-style messages.
- MessageService is a generic message receive/ack channel.
```

### XSD Domain Inventory

| XSD | Imports | Top-level elements | Complex types |
|---|---|---:|---:|
| `Agent.xsd` | `Common.xsd` | `Agent`, `AgentAction`, `ShipmentAction`, `OrderReleaseAction`, `OrderMovementAction`, `SellSideShipmentAction`, `DriverAction` | 9 |
| `AgentService.xsd` | `Service.xsd`, `Agent.xsd` | `AgentMessage`, `AgentReplyMessage` | 2 |
| `Common.xsd` | none | shared scalar/types only | 17 |
| `Configuration.xsd` | `TransmissionCommon.xsd` | `User`, `CSVDataLoad` | 5 |
| `ContentSource.xsd` | `Common.xsd` | `ContentSourceRequest`, `ContentSourceResponse`, `Content`, `ContentSourceAck`, `ContentAck` | 0 |
| `DBXML.xsd` | none | `sql2xml`, `DBObject`, `Query`, `ObjectSet`, `Entity`, `xml2sql`, `TRANSACTION_SET`, `importResponse` | 4 |
| `Document.xsd` | `TransmissionCommon.xsd`, `LocationContact.xsd` | `Document` | 5 |
| `Finance.xsd` | `TransmissionCommon.xsd`, `LocationContact.xsd`, `Shipment.xsd`, `Item.xsd` | `Accrual`, `Billing`, `AllocationBase`, `Invoice`, `Voucher`, `FinancialSystemFeed`, `Claim`, `ExchangeRate`, `WorkInvoice` | 73 |
| `GenericTransaction.xsd` | `TransmissionCommon.xsd`, `LocationContact.xsd`, `Shipment.xsd`, `Rate.xsd`, `Order.xsd`, `ShipUnit.xsd` | `Topic`, `GenericStatusUpdate`, `RemoteQuery`, `RemoteQueryReply`, `DataQuerySummary`, `TransactionAck` | 36 |
| `GTM.xsd` | `TransmissionCommon.xsd`, `LocationContact.xsd`, `Shipment.xsd`, `Order.xsd`, `Document.xsd`, `Item.xsd` | `GtmContact`, `GtmRegistration`, `GtmTransaction`, `GtmDeclaration`, `GtmBond`, `ServiceRequest`, `ServiceResponse` | 84 |
| `Item.xsd` | `TransmissionCommon.xsd`, `LocationContact.xsd` | `ItemMaster`, `Item`, `HazmatItem`, `HazmatGeneric`, `Sku`, `SkuTransaction`, `SkuEvent`, `PartnerItem` | 43 |
| `Job.xsd` | `TransmissionCommon.xsd`, `LocationContact.xsd`, `Order.xsd`, `Finance.xsd` | `Job` | 9 |
| `LocationContact.xsd` | `TransmissionCommon.xsd` | `Location`, `Contact`, `ContactGroup`, `Corporation`, `ActivityTimeDef`, `PartySite` | 41 |
| `Message.xsd` | `Common.xsd` | `BaseMessageHeader`, `BaseMessageBody`, `Message`, `MessageBody`, `TextContent`, `XMLContent`, `MessageAck`, `MessageReport` | 8 |
| `Order.xsd` | `TransmissionCommon.xsd`, `LocationContact.xsd`, `ShipUnit.xsd`, `Item.xsd` | `TransOrder`, `TransOrderLink`, `TransOrderStatus`, `Release`, `ReleaseInstruction`, `OBShipUnit`, `OBLine`, `OrderMovement`, `Quote` | 49 |
| `Planning.xsd` | `TransmissionCommon.xsd`, `LocationContact.xsd` | `Itinerary`, `XLane`, `Mileage`, `RouteTemplate`, `BulkPlan`, `BulkRating`, `BulkContMove`, `BulkTrailerBuild`, `FleetBulkPlan`, `ServiceTime` | 26 |
| `Rate.xsd` | `TransmissionCommon.xsd` | `RATE_OFFERING`, `RATE_GEO`, `X_LANE` | 6 |
| `Service.xsd` | `Common.xsd` | `Pk`, `ShipmentPk`, `SellSideShipmentPk`, `OrderReleasePk`, `OrderMovementPk`, `DriverPk`, `ServiceReplyMessage` | 6 |
| `Shipment.xsd` | `TransmissionCommon.xsd`, `LocationContact.xsd`, `ShipUnit.xsd`, `Item.xsd`, `Order.xsd`, `Rate.xsd`, `Document.xsd` | `PlannedShipment`, `ActualShipment`, `ShipmentStatus`, `SShipUnit`, `ShipmentLink`, `ShipStop`, `Equipment`, `TenderOffer`, `TenderResponse`, `Voyage`, `Driver`, `PowerUnit`, `Device` | 136 |
| `ShipUnit.xsd` | `TransmissionCommon.xsd`, `LocationContact.xsd`, `Item.xsd` | no top-level domain element found in first pass | 12 |
| `Transaction.xsd` | almost all core domain XSDs | umbrella transaction include file | 0 |
| `Transmission.xsd` | `TransmissionCommon.xsd` | `Transmission`, `TransmissionAck`, `TransmissionHeader` | 6 |
| `TransmissionCommon.xsd` | none | `TransmissionReport`, `TransactionHeader`, `IntSavedQuery`, `GLogXMLTransaction` | 104 |

Service-wrapper XSDs:

```text
- DriverService.xsd
- OrderMovementService.xsd
- OrderReleaseService.xsd
- SellSideShipmentService.xsd
- ShipmentService.xsd
```

These import `AgentService.xsd` and expose action/reply message elements.

Screening/service XSDs:

```text
- RestricedPartyScreeningService.xsd
- SanctionedTerritoryScreeningService.xsd
```

These are specialized service contracts and should be treated as future scope
unless a concrete GTM/compliance workflow enters the roadmap.

## Phase 2 - Functional Domain Map, First Pass

### Transmission Backbone

Evidence:

```text
Transmission.xsd imports TransmissionCommon.xsd and exposes:
- Transmission
- TransmissionAck
- TransmissionHeader

Transaction.xsd imports the major domain files:
- Planning
- Configuration
- ShipUnit
- Rate
- Order
- Shipment
- GenericTransaction
- Finance
- Job
- Document
- GTM
```

Implication:

```text
Transmission should become the primary schema root for Integration Mapping
Studio sample parsing, XSD-driven path browsing, and XML artifact validation.
```

### Rate Domain

Evidence:

```text
Rate.xsd top-level elements:
- RATE_OFFERING
- RATE_GEO
- X_LANE
```

Implication:

```text
Rates Studio can use XSD-derived XML structures as a second validation source
beside CSVUTIL/Data Dictionary. This is useful for future XML export/import
helpers, but CSVUTIL order and table dependencies must continue to come from
Data Dictionary and current OTM CSV rules.
```

### Master Data Domain

Evidence:

```text
LocationContact.xsd top-level elements include:
- Location
- Contact
- ContactGroup
- Corporation
- ActivityTimeDef
- PartySite

Item.xsd top-level elements include:
- ItemMaster
- Item
- HazmatItem
- HazmatGeneric
- Sku
- SkuTransaction
- SkuEvent
- PartnerItem
```

Implication:

```text
Master Data Template Factory can use XSD path catalogs for user-friendly
template authoring and XML validation, but CSV output must remain
Data-Dictionary/table-first.
```

### Order Release / Shipment Integration

Evidence:

```text
Order.xsd top-level elements include:
- Release
- ReleaseInstruction
- OBShipUnit
- OBLine
- OrderMovement

Shipment.xsd top-level elements include:
- PlannedShipment
- ActualShipment
- ShipStop
- Equipment
- TenderOffer
- TenderResponse
```

Implication:

```text
Order Release Generator and Integration Mapping Studio should share an
XSD-derived schema/path index instead of each module maintaining local path
selectors. PlannedShipment-to-external JSON mapping is especially aligned with
the existing Integration Mapping scenario.
```

### DBXML / Command Service

Evidence:

```text
DBXML.xsd exposes:
- sql2xml
- xml2sql
- DBObject
- ObjectSet
- Entity
- TRANSACTION_SET
- importResponse

CommandService.wsdl exposes:
- xmlExport
- xmlImport
- exportProjectDefinition
- exportObjectGroup
```

Implication:

```text
This is relevant for Cutover, Catalog Core, Assets Library, and evidence:
DBXML artifacts can become first-class backend artifacts with schema-aware
validation, import/export metadata, and traceable evidence.
```

## Phase 2.1 - Prioritized Root Path Samples

The first path extraction was run with an XML parser, not text matching. The
parser follows named `complexType`, anonymous `complexType`, `sequence`,
`choice`, `complexContent`, and `extension` nodes inside the same XSD file.

Limitations of this pass:

```text
- It does not yet resolve named types across imported XSD files.
- It samples paths up to a controlled depth and row count.
- It is good enough for functional shape and first product insights, but not
  yet a complete schema catalog.
```

### Transmission

Representative paths:

```text
/Transmission
/Transmission/TransmissionHeader
/Transmission/TransmissionHeader/Version
/Transmission/TransmissionHeader/TransmissionType
/Transmission/TransmissionHeader/TransmissionCreateDt
/Transmission/TransmissionHeader/TransactionCount
/Transmission/TransmissionHeader/SenderSystemID
/Transmission/TransmissionHeader/UserName
/Transmission/TransmissionHeader/Password
/Transmission/TransmissionHeader/AckSpec
/Transmission/TransmissionHeader/ProcessGrouping
/Transmission/TransmissionHeader/NotifyInfo
/Transmission/TransmissionBody
/Transmission/TransmissionBody/GLogXMLElement
```

Technical interpretation:

```text
Transmission is the envelope. `TransmissionBody/GLogXMLElement` is the
repeatable payload container. Integration Mapping and XML generators should
treat Transmission as a wrapper around domain payloads, not as the only
business object.
```

Product insight:

```text
The app should eventually model "schema root" separately from "envelope":
for example, Transmission -> GLogXMLElement -> PlannedShipment/Release/etc.
This matters for Integration Mapping and Order Release Generator because users
often think in business documents, while OTM imports/exports may require the
Transmission wrapper.
```

### PlannedShipment

Representative paths:

```text
/PlannedShipment
/PlannedShipment/Shipment
/PlannedShipment/Shipment/ShipmentHeader
/PlannedShipment/Shipment/ShipmentHeader/ShipmentGid
/PlannedShipment/Shipment/ShipmentHeader/ShipmentRefnum
/PlannedShipment/Shipment/ShipmentHeader/TransactionCode
/PlannedShipment/Shipment/ShipmentHeader/PlannedShipmentInfo
/PlannedShipment/Shipment/ShipmentHeader/ServiceProviderGid
/PlannedShipment/Shipment/ShipmentHeader/RateOfferingGid
/PlannedShipment/Shipment/ShipmentHeader/RateGeoGid
/PlannedShipment/Shipment/ShipmentHeader/ShipmentCost
/PlannedShipment/Shipment/ShipmentHeader2
/PlannedShipment/Shipment/SEquipment
/PlannedShipment/Shipment/SEquipment/SEquipmentGid
/PlannedShipment/Shipment/SEquipment/EquipmentGroupGid
/PlannedShipment/Shipment/SEquipment/Equipment
```

Technical interpretation:

```text
PlannedShipment is a wrapper around `Shipment`. The schema shows rich header,
cost, refnum, equipment, and downstream shipment structures. It aligns with
the synthetic NDD-like mapping scenario already used in Integration Mapping.
```

Product insight:

```text
Integration Mapping should gain an XSD-backed path catalog for
PlannedShipment/Shipment so users can search official paths even when a sample
payload is incomplete. This would directly improve the NDD-style accelerator.
```

### Release

Representative paths:

```text
/Release
/Release/SendReason
/Release/ReleaseGid
/Release/TransactionCode
/Release/ReplaceChildren
/Release/TransOrderGid
/Release/ReleaseHeader
/Release/ReleaseHeader/ReleaseName
/Release/ReleaseHeader/RateServiceGid
/Release/ReleaseHeader/ServiceProviderGid
/Release/ReleaseHeader/TransportModeGid
/Release/ReleaseHeader/EquipmentGroupGid
/Release/ShipFromLocationRef
/Release/ShipToLocationRef
/Release/TimeWindow
/Release/DeclaredValue
/Release/ReleaseLine
/Release/ReleaseLine/ReleaseLineGid
/Release/ReleaseLine/PackagedItemRef
/Release/ReleaseLine/ItemQuantity
/Release/ReleaseLine/PackageDimensions
/Release/ReleaseLine/PackagedItemSpecRef
/Release/ReleaseLine/NumLayersPerShipUnit
/Release/ReleaseLine/QuantityPerLayer
/Release/ReleaseLine/TransportHandlingUnitRef
/Release/ReleaseLine/Refnum
```

Technical interpretation:

```text
`TransactionCode` is required at the Release root. Release lines are repeatable.
Header fields include many planning/rating constraints. This shape is useful
for the Order Release Generator, but it is too broad to expose raw as a single
flat form.
```

Product insight:

```text
Order Release Generator should use backend-owned templates grouped by business
story: header/source-destination/time window, line/item/quantity/package, and
ship-unit/handling-unit settings. The raw XSD path catalog should support the
template builder, not replace curated templates.
```

### Location

Representative paths:

```text
/Location
/Location/TransactionCode
/Location/LocationGid
/Location/LocationName
/Location/Address
/Location/Address/AddressLine1
/Location/Address/City
/Location/Address/ProvinceCode
/Location/Address/PostalCode
/Location/Address/CountryCode3Gid
/Location/Address/Latitude
/Location/Address/Longitude
/Location/Address/CountyQualifier
/Location/LocationRefnum
/Location/LocationRefnum/LocationRefnumQualifierGid
/Location/LocationRefnum/LocationRefnumValue
/Location/Contact
/Location/LocationRole
/Location/Corporation
/Location/ServiceProvider
/Location/EquipmentGroupProfileGid
/Location/LoadUnloadPoint
```

Technical interpretation:

```text
Location has a required `Address` object and a required `TransactionCode`.
It also directly exposes refnums, contacts, roles, corporation/service
provider information, equipment group profile, and load/unload point concepts.
```

Product insight:

```text
This validates the user's Master Data acceptance scenario: location templates
should include basic customer/location fields, address, activity/dock-related
concepts, and equipment group profile restrictions. Data Dictionary remains
the table/load-order source for CSVUTIL, while XSD can provide XML path and
functional grouping hints.
```

### Item

Representative paths:

```text
/Item
/Item/TransactionCode
/Item/ItemGid
/Item/ItemName
/Item/Description
/Item/EffectiveDate
/Item/ExpirationDate
/Item/CommodityGid
/Item/NMFCClassGid
/Item/STCCGid
/Item/HTSGid
/Item/AccessorialCodeGid
/Item/SpecialServiceGid
/Item/Remark
/Item/ItemFeature
/Item/ItemFeature/ItemFeatureQualGid
/Item/ItemFeature/ItemFeatureValue
/Item/Refnum
/Item/UnitOfMeasure
/Item/PricePerUnit
```

Technical interpretation:

```text
Item supports recursive/nested Item structures, refnums, text, commodity,
classification, and features. This means the future path catalog must handle
cycles and cap recursion safely.
```

Product insight:

```text
Master Data and Order Release Generator should not present recursive Item
paths directly to users. They need curated "Item basics", "packaging/class",
and "reference/features" sections backed by the schema catalog.
```

### RATE_OFFERING

Representative paths:

```text
/RATE_OFFERING
/RATE_OFFERING/SendReason
/RATE_OFFERING/RATE_OFFERING_ROW
/RATE_OFFERING/RATE_OFFERING_ROW/RATE_OFFERING_GID
/RATE_OFFERING/RATE_OFFERING_ROW/RATE_OFFERING_XID
/RATE_OFFERING/RATE_OFFERING_ROW/RATE_OFFERING_TYPE_GID
/RATE_OFFERING/RATE_OFFERING_ROW/RATE_OFFERING_DESC
/RATE_OFFERING/RATE_OFFERING_ROW/SERVPROV_GID
/RATE_OFFERING/RATE_OFFERING_ROW/CURRENCY_GID
/RATE_OFFERING/RATE_OFFERING_ROW/TRANSPORT_MODE_GID
/RATE_OFFERING/RATE_OFFERING_ROW/EQUIPMENT_GROUP_PROFILE_GID
/RATE_OFFERING/RATE_OFFERING_ROW/RATE_SERVICE_GID
/RATE_OFFERING/RATE_OFFERING_ROW/RATE_VERSION_GID
/RATE_OFFERING/RATE_OFFERING_ROW/TARIFF_NAME
```

Technical interpretation:

```text
Rate XSDs are row/table-shaped. `RATE_OFFERING_ROW` is repeatable and many
field names match table-like OTM column names.
```

Product insight:

```text
Rates Studio can use Rate.xsd as an XML/export schema companion, but the CSV
module should remain table-first. This XSD is especially useful to enrich
labels, documentation, and XML artifact validation around Rate Offering.
```

### RATE_GEO

Representative paths:

```text
/RATE_GEO
/RATE_GEO/SendReason
/RATE_GEO/RATE_GEO_ROW
/RATE_GEO/RATE_GEO_ROW/RATE_GEO_GID
/RATE_GEO/RATE_GEO_ROW/RATE_GEO_XID
/RATE_GEO/RATE_GEO_ROW/RATE_OFFERING_GID
/RATE_GEO/RATE_GEO_ROW/X_LANE_GID
/RATE_GEO/RATE_GEO_ROW/EQUIPMENT_GROUP_PROFILE_GID
/RATE_GEO/RATE_GEO_ROW/RATE_SERVICE_GID
/RATE_GEO/RATE_GEO_ROW/MIN_COST
/RATE_GEO/RATE_GEO_ROW/TOTAL_STOPS_CONSTRAINT
/RATE_GEO/RATE_GEO_ROW/DOMAIN_NAME
/RATE_GEO/RATE_GEO_ROW/EFFECTIVE_DATE
/RATE_GEO/RATE_GEO_ROW/EXPIRATION_DATE
```

Technical interpretation:

```text
RATE_GEO links back to RATE_OFFERING and X_LANE concepts. It also exposes cost,
stop, equipment, service, domain, and effective/expiration fields.
```

Product insight:

```text
Rates validation and generated documentation can use the XSD to explain why a
rate geo belongs to an offering and lane, while Data Dictionary continues to
validate real table dependencies and CSV import order.
```

### DBXML

Representative paths:

```text
/DBObject
/DBObject/Name
/DBObject/Predicate

/xml2sql
/xml2sql/TransactionCode
/xml2sql/SchemaOwner
/xml2sql/UpdateCache
/xml2sql/RaiseEvents
/xml2sql/CommitScope
/xml2sql/ManagedTables
/xml2sql/ManagedTables/Table
/xml2sql/TRANSACTION_SET
```

Technical interpretation:

```text
`xml2sql` wraps control metadata and a `TRANSACTION_SET`. The transaction set
allows arbitrary content through `xsd:any processContents="skip"`.
```

Product insight:

```text
DBXML support should be governed as a backend artifact workflow rather than a
fully schema-expanded editor. The app can validate wrapper fields, managed
tables, and evidence, but payload internals need Data Dictionary and/or domain
specific validators.
```

## Phase 2.2 - Cardinality and Enumerations

Observed patterns:

```text
- `TransactionCodeType` is the most important reusable enum discovered so far:
  I, U, IU, UI, D, RC, RP, R, II, DR, NP.
- Service.xsd has small enums for service object type, action type, result
  detail, and reply status.
- Most domain files model structure through complex types and documentation
  annotations rather than many local simpleType enumerations.
- Cardinality is highly useful: roots often require TransactionCode, row-like
  rate objects are repeatable, refnums/remarks/lines are often unbounded, and
  Location requires Address.
```

Product insight:

```text
The first reusable schema feature should be a path/cardinality/documentation
catalog, not an enum-heavy validation engine. Enumerations should be extracted
where present, but most validation value sets will still need Data Dictionary,
OTM reference data, or official functional docs.
```

## Phase 3 - Reusable Contract Candidates

These are candidates only. They are not roadmap commitments yet.

| Candidate | Source evidence | Potential modules |
|---|---|---|
| XSD schema path index | All domain XSDs, especially `Transmission.xsd`, `Shipment.xsd`, `Order.xsd`, `LocationContact.xsd`, `Item.xsd`, `Rate.xsd` | Integration Mapping, Order Release Generator, Master Data, Rates |
| Service operation catalog | 8 WSDLs and operation/message names | Catalog Core, Developer Tools, Integration Mapping |
| XML artifact validator | Transmission/DBXML/Order/Shipment/Rate root elements | Assets Library, Evidence Hub, Jobs Processing |
| DBXML import/export helper | `DBXML.xsd`, `CommandService.wsdl` | Cutover Checklist, Catalog Core, Assets Library |
| Action-service helper | Agent/action service XSD/WSDL wrappers | Order Release Generator, Jobs Processing |

## Phase 4 - Initial Product Insights

### Integration Mapping Studio

The strongest immediate insight is an XSD-backed source/target schema registry.

Potential improvement:

```text
- Register OTM 26A schemas as backend-owned schema packs.
- Let mappings select official OTM source roots such as Transmission,
  PlannedShipment, Release, Location, RATE_GEO, or RATE_OFFERING.
- Generate searchable path trees from XSD instead of only uploaded samples.
- Validate source paths against XSD when a sample payload is partial.
```

Why it matters:

```text
The current module is already good at sample-driven mapping. XSD packs would
make it a stronger accelerator because users could start from an official OTM
contract before they have perfect sample files.
```

### Order Release Generator

Potential improvement:

```text
- Move template field definitions toward XSD-backed Release and ShipUnit paths.
- Validate generated XML against the Order/Transmission schema pack.
- Offer separate outputs for Transmission XML and DBXML-style artifacts where
  applicable.
```

### Master Data Template Factory

Potential improvement:

```text
- Use LocationContact and Item XSDs to enrich template authoring labels,
  grouped sections, XML path hints, and artifact validation.
- Keep Data Dictionary as the source of CSV table/column/load-order truth.
```

### Rates Studio

Potential improvement:

```text
- Add XSD-derived semantic grouping for RATE_OFFERING, RATE_GEO, and X_LANE.
- Use it for documentation, artifact validation, and future XML helpers.
- Keep CSVUTIL generation governed by Data Dictionary and existing rate
  package contracts.
```

### Assets / Evidence / Jobs

Potential improvement:

```text
- Store WSDL/XSD-derived schema packs as governed assets.
- Link generated artifacts to the schema pack used for validation.
- Add job runs for "parse schema pack", "validate XML", and "extract path
  catalog" with Evidence Hub outputs.
```

## Phase 3.1 - Workbench Contract Crosswalk

This crosswalk compares the OTM 26A WSDL/XSD discovery with the current backend
contracts in `src/otm_workbench`. It is a technical/functional fit analysis,
not yet a roadmap commitment.

| Module | Current Workbench contract | 26A contract fit | Gap or opportunity |
|---|---|---|---|
| Catalog Core | `MACRO_OBJECT_SEED` already models `RATE_OFFERING`, `RATE_RECORD`, `ITEM`, `REGION`, and `LOCATION` with Data Dictionary tables and load order. | Strong fit. `Rate.xsd` exposes `RATE_OFFERING`, `RATE_GEO`, and `X_LANE`; `LocationContact.xsd` exposes `Location`; `Item.xsd` exposes `Item`. | Add optional links from macro objects to schema roots and service operations. Keep Data Dictionary as table/load-order truth. |
| Integration Mapping Studio | Persisted schema documents and nodes are generated from uploaded XML/JSON payload samples. | Strong fit as a complement. `Transmission`, `PlannedShipment`, `Release`, `Location`, and JSON targets can share an official path catalog. | Add backend-owned schema packs and XSD-derived path browsing so users can start from official OTM roots even when samples are incomplete. |
| Master Data Template Factory | Scenario packs already cover operational `LOCATION` and `ITEM` templates with user-friendly fields mapped to OTM tables. | Strong fit. `Location` confirms address, coordinates, refnums, activity/dock concepts; `Item` confirms item, classification, UOM, price, and recursive item complexity. | Add XSD path/documentation hints to template fields while keeping CSV output governed by Data Dictionary and OTM CSVUTIL rules. |
| Order Release Generator | Curated synthetic template generates a `Transmission` XML wrapper with `Release` and `ReleaseLine` data. | Strong fit. `Order.xsd` exposes `Release`; `Transmission.xsd` confirms the envelope pattern. | Map template columns to official Release paths, add TransactionCode handling, and validate generated XML against schema-pack metadata. |
| Rates Studio | Rates remain table-first and CSVUTIL-first, with catalog macro objects for offering/record/lane concepts. | Strong fit as a semantic companion. Rate XSD roots are row/table-shaped and mirror OTM table naming. | Use XSD metadata for labels, docs, and future XML validation, but keep table dependencies and CSV package order from Data Dictionary. |
| Assets Library / Evidence Hub | Assets and evidence already govern generated files and QA outputs. | Strong fit. WSDL/XSD files can become governed assets and validation evidence sources. | Add schema packs as first-class assets; link XML validation jobs and evidence records to the schema pack version used. |
| Jobs Processing | Jobs already run module workflows and validations. | Strong fit for long-running parsing and validation. | Add jobs for schema-pack ingestion, path catalog extraction, XML validation, and WSDL operation indexing. |

### Existing Implementation Notes

```text
- Integration Mapping currently parses schema trees from sample XML/JSON only.
- Order Release Generator currently emits Transmission/TransmissionBody/
  GLogXMLElement/Release without schema-pack validation.
- Master Data scenario packs already align with Location and Item functional
  groupings, including location address/capacity/activity/dock/equipment
  restriction and item/packaging/ship-unit concepts.
- Catalog Core macro objects already map the most important discovered OTM
  roots to Data Dictionary tables.
```

Technical interpretation:

```text
The schema-pack feature should be shared infrastructure. Building XSD parsing
inside only Integration Mapping, Order Release, or Master Data would duplicate
the same official OTM path/catalog logic across modules.
```

## Phase 3.2 - Proposed Intermediate Data Contracts

These contracts are intentionally small and backend-owned. They would let future
modules reuse the same OTM 26A knowledge without embedding XSD files directly in
each workflow.

| Contract | Purpose | Key fields |
|---|---|---|
| `SchemaPack` | Versioned governed bundle of XSD/WSDL files. | `code`, `otm_version`, `source_type`, `asset_id`, `source_path`, `namespace_count`, `status` |
| `SchemaRoot` | Searchable official root element or service payload root. | `schema_pack_id`, `root_name`, `domain_area`, `xsd_file`, `root_type`, `envelope_role`, `recommended_modules` |
| `SchemaPath` | Flattened path catalog with structure and docs. | `schema_root_id`, `path`, `node_name`, `data_type`, `min_occurs`, `max_occurs`, `is_required`, `is_repeatable`, `documentation`, `source_file` |
| `ServiceOperation` | WSDL operation catalog. | `schema_pack_id`, `wsdl_file`, `service_name`, `operation_name`, `input_message`, `output_message`, `fault_message`, `related_roots` |
| `MacroObjectSchemaLink` | Bridge between Catalog Core macro objects and official XML roots. | `macro_object_code`, `schema_root_id`, `relationship_role`, `confidence`, `notes` |

Recommended sequencing:

```text
1. Store schema packs as Assets Library records.
2. Parse XSD roots and paths through Jobs Processing.
3. Expose roots/paths through Catalog Core APIs.
4. Let Integration Mapping, Master Data, Rates, and Order Release consume the
   same schema catalog.
5. Emit validation results into Evidence Hub.
```

## Phase 3.3 - Decisions and Validation Needed

Validated by local code cross-check:

```text
- Catalog Core already names the main rate, item, and location macro objects
  that appear in the 26A XSD set.
- Master Data Location and Item scenario packs are functionally aligned with
  the 26A LocationContact and Item domains.
- Integration Mapping needs an official schema path source because current path
  trees depend on uploaded samples.
- Order Release Generator already uses the correct broad envelope direction,
  but needs schema-aware field/path validation before it can be considered
  contract complete.
```

Still needs functional/technical validation before roadmap conversion:

```text
1. Confirm whether OTM 26A is the baseline version or one supported version
   among many.
2. Confirm whether schema packs are global assets, project assets, or both.
3. Confirm the first Order Release output contract: Transmission-wrapped
   Release versus narrower OrderRelease service action.
4. Decide how far DBXML support should go in MVP0: wrapper validation only,
   artifact generation, or CommandService import/export orchestration.
5. Validate schema-pack path extraction against Oracle official docs for each
   module before using it as user-facing guidance.
```

## Validation Questions Before Roadmap

```text
1. Are these OTM 26A files the target baseline version for MVP0/MVP1, or should
   the app support multiple OTM versions from the start?
2. Should schema packs be treated as global system assets, per-project assets,
   or both?
3. For Integration Mapping, should XSD path catalogs supplement uploaded sample
   payloads or become the primary authoring source?
4. For Order Release Generator, should the first validated XML output be
   Transmission-wrapped Release or a narrower OrderRelease service action?
5. For DBXML, should we prioritize local generation/validation first, or direct
   CommandService import/export workflow later?
```

## Next Phase Tasks

```text
1. Extract element-path samples for the highest-value roots:
   Transmission, PlannedShipment, Release, Location, Item, RATE_OFFERING,
   RATE_GEO, DBObject, xml2sql.
2. Identify simpleType/enumeration/cardinality constraints if present or prove
   that the provided XSDs mostly model structure through complex types.
3. Compare XSD root/domain names against existing Catalog Core macro-object and
   Master Data template concepts.
4. Produce a validated module-impact matrix before creating roadmap issues.
5. Prototype a schema-pack ingestion contract and decide whether it belongs
   first in Assets Library, Catalog Core, or Jobs Processing.
```
