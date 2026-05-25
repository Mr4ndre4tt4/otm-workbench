# OTM 26A WSDL/XSD Discovery

**Status:** phase 1 complete, phase 2 started  
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
```
