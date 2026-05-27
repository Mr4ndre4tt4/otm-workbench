# Context Segregation Model Ledger

**Date:** 2026-05-27
**Status:** active implementation control

This ledger classifies model families before any migration adds or changes
scope columns. It protects shared technical metadata from accidental
client/domain duplication while making operational records explicit about
project, environment, OTM domain, Public View, and access policy.

## Classification Key

| Classification | Meaning |
|---|---|
| `global` | Shared platform or technical metadata. Do not partition per client/domain unless a later spec explicitly reclassifies it. |
| `setup-scope` | Settings-owned configuration that defines projects, environments, users, roles, grants, or active context. |
| `public-capable` | Record may be explicit Public View or private operational data. Must never treat null scope as public. |
| `private-operational` | Client/domain work record. Must carry or inherit project, environment, domain, visibility, and access-policy scope. |
| `inherits-parent-scope` | Child record is not independently visible. It must be accessed through a scoped parent. |
| `needs-review` | Requires product or Oracle/Data Dictionary review before migration. |

## Required Operational Scope

Private operational parent records should resolve to:

```text
project_id
environment_id
profile_id, where profile-specific behavior exists
domain_name
visibility or visibility_scope
access_policy_id or equivalent grant/policy binding
```

Public View must be explicit, normally through `domain_name = PUBLIC` plus a
public visibility value. `DBA` visibility is a query/grant behavior, not a data
shortcut.

## Platform And Settings

| Model | Current Scope Fields | Classification | Scope Owner | Migration Expectation | Notes |
|---|---|---|---|---|---|
| `User` | none | setup-scope | Settings | none now | User identity is global; grants define visibility. |
| `SessionToken` | user | setup-scope | `User` | none | Auth state only. |
| `Workspace` | none | setup-scope | Settings | none now | Workspace contains projects but is not operational OTM data. |
| `Project` | workspace | setup-scope | Settings | add client/domain relation later if Settings spec requires | Project is the top setup container. |
| `Profile` | `project_id` | setup-scope | `Project` | none now | Profile is project configuration. |
| `Environment` | `project_id` | setup-scope | `Project` | none now | Environment is project configuration. |
| `ActiveContext` | `project_id`, `profile_id`, `environment_id`, `domain_name`, `can_view_all_domains` | setup-scope | `User` | none now | Already supports context selector and DBA wildcard domains. |
| `UserPreference` | user | setup-scope | `User` | none | UI preference only. |
| `Role` | none | setup-scope | Settings | none now | Role definitions are global templates. |
| `Capability` | none | setup-scope | Settings | none | Capability registry is global. |
| `UserProjectRole` | `project_id` | setup-scope | Settings | add domain/environment grants later if access-policy design requires | Current project grant bridge. |
| `RoleCapability` | role/capability | setup-scope | Settings | none | Global role capability mapping. |
| `Module` | none | global | Platform | none | Backend-owned module registry. |
| `FeatureFlag` | scope string | global | Platform | needs-review | Current flags are global/string-scoped; per-project flags need a separate design. |
| `AuditLog` | metadata JSON only | global | Platform | needs-review | Keep append-only audit global; later add indexed scope columns only if needed for audit search. |
| `DomainEvent` | `project_id` only | private-operational | Event producer | add `environment_id`, `domain_name`, visibility/policy metadata if used for user-visible events | Event payloads must not leak cross-domain data. |

## Jobs, Artifacts, Evidence, And Assets

| Model | Current Scope Fields | Classification | Scope Owner | Migration Expectation | Notes |
|---|---|---|---|---|---|
| `Job` | `project_id`, `profile_id`, `environment_id`, `domain_name` | private-operational | Job creator/source module | add visibility/policy if jobs become user-searchable by policy | Initial scoping utility tests use this as a scoped model. |
| `JobEvent` | inherits job | inherits-parent-scope | `Job` | none | Access only through scoped job. |
| `Artifact` | `project_id`, sensitivity | public-capable | Source module record | add `environment_id`, `domain_name`, visibility/policy | Shared file/evidence primitive; retrofit before module artifacts expand. |
| `Manifest` | `project_id` | public-capable | Source module record | add `environment_id`, `domain_name`, visibility/policy | Must inherit from generated artifact/package/batch. |
| `Evidence` | `project_id`, sensitivity/client-safe | public-capable | Source module record | add `environment_id`, `domain_name`, visibility/policy | Public evidence must be explicit and client-safe. |
| `AssetClassification` | none | global | Assets module | none | Classification vocabulary. |
| `Asset` | `project_id`, `profile_id`, `environment_id`, visibility, scope type, sensitivity | public-capable | Assets module | add `domain_name`, access-policy binding | Existing visibility fields are useful but not sufficient for domain segregation. |
| `AssetVersion` | `asset_id` | inherits-parent-scope | `Asset` | none | Access only through scoped asset. |
| `AssetLink` | `asset_id` | inherits-parent-scope | `Asset` | none | Links must not bypass asset visibility. |

## Master Data

| Model | Current Scope Fields | Classification | Scope Owner | Migration Expectation | Oracle/Data Dictionary Need |
|---|---|---|---|---|---|
| `MasterDataTemplate` | none | public-capable | Master Data template authoring | add `project_id`, `environment_id`, `profile_id`, `domain_name`, visibility/policy | Validate target tables through Data Dictionary before fixtures. |
| `MasterDataBatch` | none | private-operational | `MasterDataTemplate` or batch upload | add full operational scope | Validate table dependencies before generated CSV fixtures. |
| `MasterDataCanonicalRecord` | `batch_id` | inherits-parent-scope | `MasterDataBatch` | none | Access through batch. |
| `MasterDataOutputRecord` | `batch_id` | inherits-parent-scope | `MasterDataBatch` | none | Access through batch. |
| `MasterDataCsvFile` | `batch_id` | inherits-parent-scope | `MasterDataBatch` | none | OTM CSV format rules apply. |
| `MasterDataCoordinateQualityBatch` | none | needs-review | Master Data | likely add full operational scope if kept in current module | Coordinate Quality is not a top-level UI module in this phase. |
| `MasterDataCoordinateQualityResult` | `batch_id` | inherits-parent-scope | `MasterDataCoordinateQualityBatch` | none | Keep behind parent and current UI phase constraints. |

## Rates

| Model | Current Scope Fields | Classification | Scope Owner | Migration Expectation | Oracle/Data Dictionary Need |
|---|---|---|---|---|---|
| `RateBatch` | `project_id`, `environment_id`, `profile_id`, `domain_name` | private-operational | Rates Studio | add visibility/policy only if access-policy design requires | Validate tables and dependency order through Data Dictionary. |
| `RateBatchTable` | `batch_id` | inherits-parent-scope | `RateBatch` | none | Access through scoped batch. |
| `RateBatchRow` | `batch_id`, `batch_table_id` | inherits-parent-scope | `RateBatch` | none | Access through scoped batch. |
| `RateBatchIssue` | `batch_id`, optional row/table ids | inherits-parent-scope | `RateBatch` | none | Access through scoped batch. |

## Load Plan And Cutover

| Model | Current Scope Fields | Classification | Scope Owner | Migration Expectation | Oracle/Data Dictionary Need |
|---|---|---|---|---|---|
| `LoadPlanPackage` | `project_id`, `environment_id`, `profile_id` | private-operational | Load Plan source module | add `domain_name`, visibility/policy or enforce source batch inheritance | Validate load sequence and table dependencies. |
| `CutoverChecklistTemplate` | none | global | Load Plan | none | System-seeded checklist template. |
| `CutoverChecklistTemplateItem` | `template_id` | inherits-parent-scope | `CutoverChecklistTemplate` | none | Global template item. |
| `CutoverChecklist` | `project_id`, `environment_id`, `profile_id` | private-operational | `LoadPlanPackage` | add `domain_name`, visibility/policy or enforce package inheritance | Access through package/checklist pair. |
| `CutoverChecklistItem` | `checklist_id`, `package_id` | inherits-parent-scope | `CutoverChecklist` | none | Access through scoped checklist. |
| `CsvutilBuild` | `project_id`, `environment_id`, `profile_id` | private-operational | `LoadPlanPackage` | add `domain_name`, visibility/policy or enforce package inheritance | OTM CSV format and date session rules apply. |
| `LoadPlanZipAnalysis` | `project_id`, `environment_id`, `profile_id` | private-operational | `LoadPlanPackage` | add `domain_name`, visibility/policy or enforce package inheritance | ZIP fixture validation required. |
| `LoadPlanReviewItem` | `project_id`, `environment_id`, `profile_id` | private-operational | `LoadPlanZipAnalysis` | add `domain_name`, visibility/policy or enforce package inheritance | Access through package/analysis. |
| `LoadPlanReviewDecision` | `project_id`, `environment_id`, `profile_id` | private-operational | `LoadPlanReviewItem` | add `domain_name`, visibility/policy or enforce item inheritance | Decision evidence must inherit scope. |
| `LoadPlanSequenceSnapshot` | `project_id`, `environment_id`, `profile_id` | private-operational | `LoadPlanPackage` | add `domain_name`, visibility/policy or enforce package inheritance | Validate sequence through Data Dictionary. |
| `LoadPlanCutoverReadiness` | `project_id`, `environment_id`, `profile_id` | private-operational | `LoadPlanPackage` | add `domain_name`, visibility/policy or enforce package inheritance | Readiness export must inherit scope. |
| `LoadPlanReadinessExport` | `project_id`, `environment_id`, `profile_id` | private-operational | `LoadPlanCutoverReadiness` | add `domain_name`, visibility/policy or enforce readiness inheritance | Artifact/manifest/evidence must inherit scope. |
| `LoadPlanCutoverHandoff` | `project_id`, `environment_id`, `profile_id` | private-operational | `LoadPlanReadinessExport` | add `domain_name`, visibility/policy or enforce readiness inheritance | Handoff archive must inherit scope. |

## Integration

| Model | Current Scope Fields | Classification | Scope Owner | Migration Expectation | Oracle/Data Dictionary Need |
|---|---|---|---|---|---|
| `IntegrationDefinition` | none | private-operational | Integration Mapping Studio | add full operational scope | Validate OTM payload roots against official Oracle schema docs when uncertain. |
| `IntegrationSystem` | none | private-operational | Settings/Integration | add full operational scope; consider environment-specific endpoints | Avoid storing secrets in docs, tests, or fixtures. |
| `IntegrationEndpoint` | `system_id` | inherits-parent-scope | `IntegrationSystem` | none if endpoint always belongs to scoped system | Endpoint visibility follows system/environment. |
| `IntegrationPayloadArtifact` | `definition_id`, `artifact_id` | inherits-parent-scope | `IntegrationDefinition` | none after artifacts gain scope | Linked artifact must match definition scope. |
| `IntegrationSchemaDocument` | `definition_id`, `payload_artifact_id` | inherits-parent-scope | `IntegrationDefinition` | none | Access through definition. |
| `IntegrationSchemaNode` | `schema_document_id` | inherits-parent-scope | `IntegrationSchemaDocument` | none | Access through document/definition. |
| `IntegrationMapping` | `definition_id`, schema docs | inherits-parent-scope | `IntegrationDefinition` | none | Access through definition. |
| `IntegrationTransformType` | none | global | Integration | none | System-seeded transform vocabulary. |
| `IntegrationLoopDefinition` | `definition_id` | inherits-parent-scope | `IntegrationDefinition` | none | Access through definition. |
| `IntegrationJoinRule` | `definition_id` | inherits-parent-scope | `IntegrationDefinition` | none | Access through definition. |
| `IntegrationJoinBinding` | `definition_id` | inherits-parent-scope | `IntegrationDefinition` | none | Access through definition. |
| `IntegrationJoinBindingHop` | `binding_id`, `definition_id` | inherits-parent-scope | `IntegrationJoinBinding` | none | Access through binding/definition. |
| `IntegrationLookupDefinition` | `definition_id` | inherits-parent-scope | `IntegrationDefinition` | none | Access through definition. |
| `IntegrationResponseHandler` | `definition_id` | inherits-parent-scope | `IntegrationDefinition` | none | Access through definition. |

## Order Release

| Model | Current Scope Fields | Classification | Scope Owner | Migration Expectation | Oracle/Data Dictionary Need |
|---|---|---|---|---|---|
| `OrderReleaseTemplate` | none | public-capable | Order Release Generator | add full operational scope | Validate generated XML and related fields with Oracle docs/Data Dictionary where uncertain. |
| `OrderReleaseBatch` | `template_id` | private-operational | `OrderReleaseTemplate` or upload context | add full operational scope or enforce template inheritance plus batch environment | Batch upload is operational and environment-specific. |
| `OrderReleaseBatchRow` | `batch_id` | inherits-parent-scope | `OrderReleaseBatch` | none | Access through scoped batch. |

## Reference Catalog And Oracle Technical Metadata

| Model | Current Scope Fields | Classification | Scope Owner | Migration Expectation | Oracle/Data Dictionary Need |
|---|---|---|---|---|---|
| `ReferenceObjectType` | none | global | Reference Catalog | none | Object type vocabulary. |
| `ReferenceObject` | `project_id`, `environment_id`, `domain_name` | public-capable | Reference Catalog | add visibility/policy if needed | Domain-specific references already explicit; Public references must remain explicit. |
| `ReferenceFieldPolicy` | module/field/object policy | global | Reference Catalog | none | Validation policy, not operational data. |
| `ReferenceImportBatch` | `project_id`, `environment_id`, `profile_id` | private-operational | Reference Catalog | add `domain_name`, visibility/policy | Imported references must not cross domains. |
| `ReferenceSnapshot` | `project_id`, `environment_id`, `profile_id` | private-operational | Reference Catalog | add `domain_name`, visibility/policy or enforce item-domain rules | Snapshot may include multiple domains only for DBA/approved cases. |
| `ReferenceSnapshotItem` | `snapshot_id`, `domain_name` | inherits-parent-scope | `ReferenceSnapshot` | none unless snapshot supports mixed-domain access | Access through scoped snapshot. |
| `OtmMacroObject` | none | global | Catalog Core | none | Technical/functional catalog. |
| `OtmMacroObjectTable` | macro object | global | Catalog Core | none | Technical catalog relation. |
| `OtmMacroObjectDependency` | macro object | global | Catalog Core | none | Technical catalog relation. |
| `SchemaPack` | optional asset id | global | Catalog Core/Integration | needs-review only if custom client schema packs are added | Official schema packs remain global technical metadata. |
| `SchemaFile` | schema pack | global | Catalog Core/Integration | none | Technical metadata. |
| `SchemaRoot` | schema pack/file | global | Catalog Core/Integration | none | Technical metadata. |
| `SchemaPath` | schema root | global | Catalog Core/Integration | none | Technical metadata. |
| `ServiceOperation` | schema pack/file | global | Catalog Core/Integration | none | Technical metadata. |
| `MacroObjectSchemaLink` | macro object/schema root | global | Catalog Core/Integration | none | Technical metadata. |
| `OtmTableDefinition` | none | global | Data Dictionary | none | Official Oracle/Data Dictionary source. |
| `OtmTableColumn` | table | global | Data Dictionary | none | Official Oracle/Data Dictionary source. |
| `OtmTableForeignKey` | table | global | Data Dictionary | none | Official Oracle/Data Dictionary source. |
| `OtmLoadSequence` | module/table | global | Catalog Core/Load Plan | none | Technical load contract. |
| `OtmCsvContract` | module/table | global | Catalog Core/CSVUtil | none | Technical CSV contract. |

## Migration Order

1. Shared artifact/evidence/assets scope fields and tests.
2. Settings access-policy model or binding design.
3. Master Data template and batch scope.
4. Integration definition/system scope.
5. Order Release template and batch scope.
6. Load Plan domain inheritance hardening.
7. Rates access-policy hardening if required by Settings grants.

## Test Requirements Before Each Migration

- Same project/environment/domain records are visible.
- Cross-project records are hidden from normal users.
- Cross-environment records are hidden from normal users.
- Cross-domain records are hidden from normal users.
- Explicit Public View records are visible only through public-capable paths.
- `DBA` can see all domains without changing stored data.
- Child-detail endpoints cannot bypass parent scope.
- Generated artifacts/evidence inherit source record scope.

## Open Questions

- Whether `DomainEvent` needs indexed scope columns now or can remain scoped
  through metadata until user-visible event feeds exist.
- Whether `FeatureFlag` needs project/environment targeting in this phase.
- Whether custom client schema packs should be public-capable assets or remain
  global technical metadata linked to scoped assets.
- Whether `ReferenceSnapshot` should support mixed-domain snapshots for DBA
  only, or require one domain per snapshot.
