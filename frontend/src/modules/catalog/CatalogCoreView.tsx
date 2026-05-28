import { useEffect, useState, type FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { ApiError } from '../../platform/api';
import {
  useCatalogMacroObjectDataDictionaryCheck,
  useCatalogMacroObjectDetail,
  useCatalogMacroObjectLoadPlan,
  useCatalogMacroObjects,
  useCatalogMacroObjectTables,
  useCatalogSchemaGuidanceReadiness,
  useCatalogSchemaRootPaths,
  useCatalogSchemaRootsByRole,
  useCatalogReferenceOptions,
  useCatalogTableColumns,
  useCatalogTableDetail,
  useCatalogTables,
  validateCatalogColumn,
  validateCatalogReference,
  validateCatalogTable
} from '../../platform/hooks';
import type {
  CatalogMacroObject,
  CatalogValidateColumnResult,
  CatalogValidateReferenceResult,
  CatalogValidateTableResult
} from '../../platform/types';
import { PageHeader } from '../../app/shell';
import {
  Button,
  DetailList,
  FeedbackMessage,
  MetricGrid,
  ModuleObjectList,
  ModuleWorkspaceLayout,
  SelectedObjectPanel,
  StatePanel
} from '../../ui/components';
import { booleanStatus } from '../moduleStatus';

function catalogMacroMeta(item: CatalogMacroObject) {
  const tableCount = item.summary?.table_count ?? 0;
  const dependencyCount = item.summary?.dependency_count ?? 0;
  return [item.category, item.default_method, `${tableCount} table(s)`, `${dependencyCount} dependency(ies)`];
}

const defaultCatalogValidation = {
  columnName: "RATE_GEO_COST_GROUP_GID",
  columnTableName: "RATE_GEO_COST",
  referenceDomainName: "OTM1",
  referenceFieldName: "currency_gid",
  referenceModuleId: "rates",
  referenceValue: "OTM1.BRL",
  tableName: "RATE_GEO_COST",
  tableUsage: "cutover"
};

export function CatalogCoreView({ token }: { token: string }) {
  const location = useLocation();
  const navigate = useNavigate();
  const routeMacroMatch = location.pathname.match(/^\/catalog\/macro-objects\/([^/?#]+)/);
  const routeMacroCode = routeMacroMatch ? decodeURIComponent(routeMacroMatch[1]) : null;
  const routeTableMatch = location.pathname.match(/^\/catalog\/tables\/([^/?#]+)/);
  const routeTableName = routeTableMatch ? decodeURIComponent(routeTableMatch[1]) : null;
  const isTableExplorerRoute = location.pathname === "/catalog/tables";
  const isTableRoute = isTableExplorerRoute || Boolean(routeTableName);
  const isReferenceOptionsRoute = location.pathname === "/catalog/reference-options";
  const isSchemaGuidanceRoute = location.pathname === "/catalog/schema-guidance";
  const macroObjects = useCatalogMacroObjects(token);
  const [tableName, setTableName] = useState(defaultCatalogValidation.tableName);
  const [tableUsage, setTableUsage] = useState(defaultCatalogValidation.tableUsage);
  const [columnTableName, setColumnTableName] = useState(defaultCatalogValidation.columnTableName);
  const [columnName, setColumnName] = useState(defaultCatalogValidation.columnName);
  const [referenceModuleId, setReferenceModuleId] = useState(defaultCatalogValidation.referenceModuleId);
  const [referenceFieldName, setReferenceFieldName] = useState(defaultCatalogValidation.referenceFieldName);
  const [referenceValue, setReferenceValue] = useState(defaultCatalogValidation.referenceValue);
  const [referenceDomainName, setReferenceDomainName] = useState(defaultCatalogValidation.referenceDomainName);
  const [tableValidation, setTableValidation] = useState<CatalogValidateTableResult | null>(null);
  const [columnValidation, setColumnValidation] = useState<CatalogValidateColumnResult | null>(null);
  const [referenceValidation, setReferenceValidation] = useState<CatalogValidateReferenceResult | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [runningValidation, setRunningValidation] = useState<string | null>(null);
  const [selectedSchemaRootId, setSelectedSchemaRootId] = useState<string | null>(null);
  const [schemaPathQuery, setSchemaPathQuery] = useState("");
  const [tableSearchQuery, setTableSearchQuery] = useState("rate_geo");
  const [referenceObjectType, setReferenceObjectType] = useState("CURRENCY");
  const macroItems = macroObjects.data?.items ?? [];
  const effectiveMacroCode = routeMacroCode;
  const macroDetail = useCatalogMacroObjectDetail(token, effectiveMacroCode);
  const macroTables = useCatalogMacroObjectTables(token, effectiveMacroCode);
  const macroLoadPlan = useCatalogMacroObjectLoadPlan(token, effectiveMacroCode);
  const macroCrossCheck = useCatalogMacroObjectDataDictionaryCheck(token, effectiveMacroCode);
  const schemaReadiness = useCatalogSchemaGuidanceReadiness(token);
  const envelopeRoots = useCatalogSchemaRootsByRole(token, "ENVELOPE_ONLY");
  const macroRoots = useCatalogSchemaRootsByRole(token, "MACRO_OBJECT");
  const catalogTables = useCatalogTables(token, tableSearchQuery, 25);
  const catalogTableDetail = useCatalogTableDetail(token, routeTableName);
  const catalogTableColumns = useCatalogTableColumns(token, routeTableName);
  const catalogReferenceOptions = useCatalogReferenceOptions(token, referenceObjectType, referenceDomainName);
  const schemaRootPaths = useCatalogSchemaRootPaths(token, selectedSchemaRootId, schemaPathQuery);
  const selectedMacro = macroDetail.data;
  const tableItems = macroTables.data?.items ?? [];
  const loadPlanItems = macroLoadPlan.data?.items ?? [];
  const readinessItems = schemaReadiness.data?.items ?? [];
  const envelopeRootItems = envelopeRoots.data?.items ?? [];
  const macroRootItems = macroRoots.data?.items ?? [];
  const schemaRootItems = [...envelopeRootItems, ...macroRootItems];
  const selectedSchemaRoot = schemaRootItems.find((item) => item.id === selectedSchemaRootId) ?? null;
  const selectedSchemaPathItems = schemaRootPaths.data?.items ?? [];
  const schemaLinkItems = macroCrossCheck.data?.schema_links ?? [];
  const csvutilMacroCount = macroItems.filter((item) => item.allow_csvutil).length;
  const cutoverMacroCount = macroItems.filter((item) => item.allow_cutover).length;
  const validatedTableCount = tableItems.filter((item) => item.validated_by_datadict).length;

  function clearCatalogValidationResults() {
    setTableValidation(null);
    setColumnValidation(null);
    setReferenceValidation(null);
    setValidationError(null);
    setRunningValidation(null);
  }
  useEffect(() => {
    clearCatalogValidationResults();
  }, [effectiveMacroCode]);

  function handleSelectMacroObject(macroCode: string) {
    if (macroCode === effectiveMacroCode) return;
    clearCatalogValidationResults();
    void navigate(`/catalog/macro-objects/${encodeURIComponent(macroCode)}`);
  }

  if (macroObjects.isLoading) {
    return <StatePanel>Loading OTM Catalog Core...</StatePanel>;
  }

  if (macroObjects.isError || !macroObjects.data) {
    return <StatePanel tone="error">OTM Catalog Core is unavailable.</StatePanel>;
  }

  async function runTableValidation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError(null);
    setRunningValidation("table");
    try {
      const result = await validateCatalogTable(token, {
        table_name: tableName.trim(),
        usage: tableUsage || null
      });
      setTableValidation(result);
    } catch (caught) {
      setValidationError(caught instanceof ApiError ? caught.message : "Table validation failed.");
    } finally {
      setRunningValidation(null);
    }
  }

  async function runColumnValidation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError(null);
    setRunningValidation("column");
    try {
      const result = await validateCatalogColumn(token, {
        table_name: columnTableName.trim(),
        column_name: columnName.trim()
      });
      setColumnValidation(result);
    } catch (caught) {
      setValidationError(caught instanceof ApiError ? caught.message : "Column validation failed.");
    } finally {
      setRunningValidation(null);
    }
  }

  async function runReferenceValidation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError(null);
    setRunningValidation("reference");
    try {
      const result = await validateCatalogReference(token, {
        module_id: referenceModuleId.trim(),
        field_name: referenceFieldName.trim(),
        value: referenceValue.trim(),
        domain_name: referenceDomainName.trim() || null
      });
      setReferenceValidation(result);
    } catch (caught) {
      setValidationError(caught instanceof ApiError ? caught.message : "Reference validation failed.");
    } finally {
      setRunningValidation(null);
    }
  }

  function resetCatalogValidation() {
    setTableName(defaultCatalogValidation.tableName);
    setTableUsage(defaultCatalogValidation.tableUsage);
    setColumnTableName(defaultCatalogValidation.columnTableName);
    setColumnName(defaultCatalogValidation.columnName);
    setReferenceModuleId(defaultCatalogValidation.referenceModuleId);
    setReferenceFieldName(defaultCatalogValidation.referenceFieldName);
    setReferenceValue(defaultCatalogValidation.referenceValue);
    setReferenceDomainName(defaultCatalogValidation.referenceDomainName);
    clearCatalogValidationResults();
  }

  const schemaGuidanceWorkspace = (
    <section className="panel catalog-validation-panel" aria-label="Schema guidance workspace">
      <div className="panel-header">
        <div>
          <h2>Schema guidance</h2>
          <p className="empty-text">Backend-owned XML contract readiness separated by role.</p>
        </div>
      </div>
      <MetricGrid
        ariaLabel="Schema guidance metrics"
        items={[
          {
            key: "schema_ready",
            label: "Ready guidance",
            status: booleanStatus(schemaReadiness.data?.summary.ready_count ?? 0),
            value: schemaReadiness.data?.summary.ready_count ?? 0
          },
          {
            key: "schema_blocked",
            label: "Blocked guidance",
            status: booleanStatus(schemaReadiness.data?.summary.blocked_count ?? 0),
            value: schemaReadiness.data?.summary.blocked_count ?? 0
          },
          {
            key: "envelopes",
            label: "Envelope roots",
            status: booleanStatus(envelopeRootItems.length),
            value: envelopeRootItems.length
          },
          {
            key: "macro_roots",
            label: "Macro roots",
            status: booleanStatus(macroRootItems.length),
            value: macroRootItems.length
          }
        ]}
      />
      <div className="catalog-validation-grid">
        <DetailList
          ariaLabel="Integration envelope roots"
          emptyText={envelopeRoots.isLoading ? "Loading envelope roots..." : "No envelope roots indexed."}
          items={envelopeRootItems.map((item) => ({
            id: item.id,
            meta: [item.domain_area, item.envelope_role, item.root_type],
            status: item.schema_guidance_role,
            subtitle: item.canonical_root_name,
            title: item.root_display_label
          }))}
        />
        <DetailList
          ariaLabel="Macro schema roots"
          emptyText={macroRoots.isLoading ? "Loading macro roots..." : "No macro roots indexed."}
          items={macroRootItems.map((item) => ({
            id: item.id,
            meta: [item.domain_area, item.data_dictionary_family || "No table family", item.root_type],
            status: item.schema_guidance_role,
            subtitle: item.canonical_root_name,
            title: item.root_display_label
          }))}
        />
      </div>
      <div className="catalog-root-picker" aria-label="Schema root inspector">
        {schemaRootItems.map((item) => (
          <Button
            key={item.id}
            aria-pressed={selectedSchemaRootId === item.id}
            onClick={() => {
              setSelectedSchemaRootId(item.id);
              setSchemaPathQuery("");
            }}
            type="button"
            variant={selectedSchemaRootId === item.id ? "primary" : "secondary"}
          >
            {`Inspect ${item.root_display_label}`}
          </Button>
        ))}
      </div>
      <section className="catalog-schema-root-detail" aria-label="Selected schema root detail">
        <div className="panel-header">
          <div>
            <h3>{selectedSchemaRoot?.root_display_label ?? "Select a schema root"}</h3>
            <p className="empty-text">
              {selectedSchemaRoot
                ? `${selectedSchemaRoot.canonical_root_name} from ${selectedSchemaRoot.domain_area}`
                : "Choose one root above to review backend-indexed XML paths."}
            </p>
          </div>
        </div>
        {selectedSchemaRoot ? (
          <label className="catalog-schema-path-search">
            Schema path search
            <input
              value={schemaPathQuery}
              onChange={(event) => setSchemaPathQuery(event.target.value)}
              placeholder="Search indexed paths"
            />
          </label>
        ) : null}
        <DetailList
          ariaLabel="Selected schema root paths"
          emptyText={
            selectedSchemaRootId
              ? schemaRootPaths.isLoading
                ? "Loading schema paths..."
                : "No paths indexed for this schema root."
              : "No schema root selected."
          }
          items={selectedSchemaPathItems.map((item) => ({
            id: item.id,
            meta: [
              item.node_name,
              item.data_type || "No type",
              item.is_required ? "Required" : "Optional",
              item.is_repeatable ? "Repeatable" : "Single",
              item.documentation || item.source_file
            ],
            status: item.is_required ? "REQUIRED" : "OPTIONAL",
            title: item.path
          }))}
        />
      </section>
      <DetailList
        ariaLabel="Schema guidance readiness"
        emptyText={schemaReadiness.isLoading ? "Loading schema guidance readiness..." : "No schema readiness data available."}
        items={readinessItems.map((item) => ({
          id: item.macro_object_code,
          meta: [
            item.category,
            `${item.validated_table_count}/${item.target_table_count} table(s)`,
            `${item.schema_link_count} schema link(s)`
          ],
          status: item.readiness_status,
          subtitle: item.macro_object_name,
          title: item.macro_object_code
        }))}
      />
    </section>
  );

  if (isTableRoute) {
    const tableRows = catalogTables.data?.items ?? [];
    const selectedTable = catalogTableDetail.data;
    const selectedColumns = catalogTableColumns.data?.items ?? [];

    return (
      <>
        <PageHeader
          description={
            routeTableName
              ? "Route-level Data Dictionary table detail with backend-owned column metadata."
              : "Search OTM Data Dictionary tables before using them in module workflows."
          }
          label={routeTableName ? "Catalog table detail" : "Catalog explorer"}
          title={routeTableName ? `${routeTableName} Table detail` : "Catalog Table Explorer"}
        />
        <div className="route-action-row">
          <Link className="button button-secondary" to="/catalog">
            Back to Catalog
          </Link>
          {routeTableName ? (
            <Link className="button button-secondary" to="/catalog/tables">
              Back to Tables
            </Link>
          ) : null}
        </div>

        {!routeTableName ? (
          <section className="panel catalog-validation-panel" aria-label="Catalog table explorer">
            <div className="panel-header">
              <h2>Table search</h2>
            </div>
            <label className="catalog-schema-path-search">
              Table search
              <input value={tableSearchQuery} onChange={(event) => setTableSearchQuery(event.target.value)} />
            </label>
            <ModuleObjectList
              ariaLabel="Catalog table search results"
              emptyText={catalogTables.isLoading ? "Loading catalog tables..." : "No catalog tables match this search."}
              items={tableRows.map((item) => ({
                id: item.table_name,
                meta: [item.schema_name, item.data_category, `${item.column_count} column(s)`],
                status: item.allow_cutover || item.allow_csvutil ? "ACTIVE" : "BLOCKED",
                subtitle: item.description,
                title: item.table_name
              }))}
              onSelect={(tableName) => void navigate(`/catalog/tables/${encodeURIComponent(tableName)}`)}
              selectedId={routeTableName}
            />
          </section>
        ) : (
          <ModuleWorkspaceLayout
            ariaLabel="Catalog table detail workspace"
            side={null}
            status={selectedTable?.allow_cutover || selectedTable?.allow_csvutil ? "ACTIVE" : "BLOCKED"}
            title="Table detail"
          >
            {catalogTableDetail.isLoading ? <StatePanel>Loading catalog table...</StatePanel> : null}
            {selectedTable ? (
              <>
                <MetricGrid
                  ariaLabel="Catalog table metrics"
                  items={[
                    {
                      key: "columns",
                      label: "Columns",
                      status: booleanStatus(selectedTable.column_count),
                      value: selectedTable.column_count
                    },
                    {
                      key: "foreign_keys",
                      label: "Foreign keys",
                      status: booleanStatus(selectedTable.foreign_key_count ?? 0),
                      value: selectedTable.foreign_key_count ?? 0
                    },
                    {
                      key: "date_columns",
                      label: "Date columns",
                      status: booleanStatus(selectedTable.date_columns?.length ?? 0),
                      value: selectedTable.date_columns?.length ?? 0
                    },
                    {
                      key: "required_columns",
                      label: "Required columns",
                      status: booleanStatus(selectedTable.required_columns?.length ?? 0),
                      value: selectedTable.required_columns?.length ?? 0
                    }
                  ]}
                />
                <section className="panel" aria-label="Catalog table summary">
                  <div className="panel-header">
                    <div>
                      <h2>{selectedTable.table_name}</h2>
                      <p className="empty-text">{selectedTable.description}</p>
                    </div>
                  </div>
                  <DetailList
                    ariaLabel="Catalog table columns"
                    emptyText={catalogTableColumns.isLoading ? "Loading table columns..." : "No columns available for this table."}
                    items={selectedColumns.map((item) => ({
                      id: item.column_name,
                      meta: [
                        item.data_type,
                        item.is_primary_key ? "Primary key" : "Not primary",
                        item.is_required ? "Required" : item.nullable || item.is_nullable ? "Nullable" : "Optional"
                      ],
                      status: item.is_required ? "REQUIRED" : "OPTIONAL",
                      title: item.column_name
                    }))}
                  />
                </section>
              </>
            ) : null}
          </ModuleWorkspaceLayout>
        )}
      </>
    );
  }

  if (isReferenceOptionsRoute) {
    const referenceOptions = catalogReferenceOptions.data?.items ?? [];
    const allowedDomains = catalogReferenceOptions.data?.allowed_domains ?? [];

    return (
      <>
        <PageHeader
          description="Browse backend-owned reference values in the active domain scope before validating module CSV or integration fields."
          label="Catalog reference browser"
          title="Catalog Reference Options"
        />
        <div className="route-action-row">
          <Link className="button button-secondary" to="/catalog">
            Back to Catalog
          </Link>
        </div>

        <section className="panel catalog-validation-panel" aria-label="Catalog reference options browser">
          <div className="panel-header">
            <div>
              <h2>Reference scope</h2>
              <p className="empty-text">
                {allowedDomains.length ? `Allowed domains: ${allowedDomains.join(", ")}` : "Allowed domains load from the active context."}
              </p>
            </div>
          </div>
          <div className="catalog-validation-grid">
            <form className="catalog-validation-form" onSubmit={(event) => event.preventDefault()}>
              <h3>Options</h3>
              <label>
                Object type
                <input
                  required
                  value={referenceObjectType}
                  onChange={(event) => setReferenceObjectType(event.target.value.toUpperCase())}
                />
              </label>
              <label>
                Domain
                <input value={referenceDomainName} onChange={(event) => setReferenceDomainName(event.target.value)} />
              </label>
            </form>

            <form className="catalog-validation-form" onSubmit={(event) => void runReferenceValidation(event)}>
              <h3>Validate reference</h3>
              <label>
                Module
                <input
                  required
                  value={referenceModuleId}
                  onChange={(event) => setReferenceModuleId(event.target.value)}
                />
              </label>
              <label>
                Field
                <input
                  required
                  value={referenceFieldName}
                  onChange={(event) => setReferenceFieldName(event.target.value)}
                />
              </label>
              <label>
                Reference value
                <input required value={referenceValue} onChange={(event) => setReferenceValue(event.target.value)} />
              </label>
              <Button disabled={runningValidation === "reference"} type="submit" variant="primary">
                {runningValidation === "reference" ? "Validating..." : "Validate reference"}
              </Button>
              {referenceValidation ? (
                <div className="catalog-validation-result" aria-label="Reference validation result">
                  <strong>{`Reference validation: ${referenceValidation.severity}`}</strong>
                  <span>{`${referenceValidation.object_type}: ${referenceValidation.gid}`}</span>
                  <p>{referenceValidation.message}</p>
                </div>
              ) : null}
            </form>
          </div>
          {validationError ? <FeedbackMessage tone="error">{validationError}</FeedbackMessage> : null}
          <DetailList
            ariaLabel="Catalog reference options"
            emptyText={catalogReferenceOptions.isLoading ? "Loading reference options..." : "No reference options match this scope."}
            items={referenceOptions.map((item) => ({
              id: item.gid,
              meta: [item.xid, item.domain_name, item.display_name],
              status: item.domain_name === catalogReferenceOptions.data?.domain_name ? "ACTIVE_SCOPE" : "VISIBLE_SCOPE",
              subtitle: item.display_name,
              title: item.gid
            }))}
          />
        </section>
      </>
    );
  }

  if (isSchemaGuidanceRoute) {
    return (
      <>
        <PageHeader
          description="Inspect backend-owned schema readiness, XML roots, and indexed paths without exposing local schema files."
          label="Catalog schema guidance"
          title="Catalog Schema Guidance"
        />
        <div className="route-action-row">
          <Link className="button button-secondary" to="/catalog">
            Back to Catalog
          </Link>
        </div>
        {schemaGuidanceWorkspace}
      </>
    );
  }

  return (
    <>
      <PageHeader
        description={
          routeMacroCode
            ? "Route-level macro object inspection for backend-owned tables, dependencies, Data Dictionary checks, and schema links."
            : "Canonical OTM catalog foundation for macro objects, load plans, data dictionary alignment, and module contracts."
        }
        label={routeMacroCode ? "Catalog detail" : "Module workspace"}
        title={routeMacroCode ? `${routeMacroCode} Catalog detail` : "OTM Catalog Core"}
      />
      {routeMacroCode ? (
        <div className="route-action-row">
          <Link className="button button-secondary" to="/catalog">
            Back to Catalog
          </Link>
        </div>
      ) : (
        <div className="route-action-row">
          <Link className="button button-secondary" to="/catalog/tables">
            Table Explorer
          </Link>
          <Link className="button button-secondary" to="/catalog/reference-options">
            Reference Options
          </Link>
          <Link className="button button-secondary" to="/catalog/schema-guidance">
            Schema Guidance
          </Link>
        </div>
      )}

      <MetricGrid
        ariaLabel="OTM Catalog Core metrics"
        items={[
          { key: "macro_objects", label: "Macro objects", status: booleanStatus(macroObjects.data.total), value: macroObjects.data.total },
          { key: "csvutil", label: "CSVUTIL allowed", status: booleanStatus(csvutilMacroCount), value: csvutilMacroCount },
          { key: "cutover", label: "Cutover allowed", status: booleanStatus(cutoverMacroCount), value: cutoverMacroCount },
          { key: "validated", label: "Validated tables", status: booleanStatus(validatedTableCount), value: validatedTableCount }
        ]}
      />

      <section className="panel catalog-validation-panel" aria-label="Catalog validation">
        <div className="panel-header">
          <h2>Catalog validation</h2>
          <Button disabled={Boolean(runningValidation)} onClick={resetCatalogValidation} type="button" variant="secondary">
            Reset catalog validation
          </Button>
        </div>
        {validationError ? <FeedbackMessage tone="error">{validationError}</FeedbackMessage> : null}
        <div className="catalog-validation-grid">
          <form className="catalog-validation-form" onSubmit={(event) => void runTableValidation(event)}>
            <h3>Table</h3>
            <label>
              Table name
              <input required value={tableName} onChange={(event) => setTableName(event.target.value)} />
            </label>
            <label>
              Usage
              <select value={tableUsage} onChange={(event) => setTableUsage(event.target.value)}>
                <option value="">Any</option>
                <option value="csvutil">csvutil</option>
                <option value="cutover">cutover</option>
              </select>
            </label>
            <Button disabled={runningValidation === "table"} type="submit" variant="primary">
              {runningValidation === "table" ? "Validating..." : "Validate table"}
            </Button>
            {tableValidation ? (
              <div className="catalog-validation-result" aria-label="Table validation result">
                <strong>{`Table validation: ${tableValidation.severity}`}</strong>
                <span>{tableValidation.table_name}</span>
                <p>{tableValidation.message}</p>
              </div>
            ) : null}
          </form>

          <form className="catalog-validation-form" onSubmit={(event) => void runColumnValidation(event)}>
            <h3>Column</h3>
            <label>
              Column table
              <input
                required
                value={columnTableName}
                onChange={(event) => setColumnTableName(event.target.value)}
              />
            </label>
            <label>
              Column name
              <input required value={columnName} onChange={(event) => setColumnName(event.target.value)} />
            </label>
            <Button disabled={runningValidation === "column"} type="submit" variant="primary">
              {runningValidation === "column" ? "Validating..." : "Validate column"}
            </Button>
            {columnValidation ? (
              <div className="catalog-validation-result" aria-label="Column validation result">
                <strong>{`Column validation: ${columnValidation.severity}`}</strong>
                <span>{`${columnValidation.table_name}.${columnValidation.column_name}`}</span>
                <p>{columnValidation.message}</p>
              </div>
            ) : null}
          </form>

          <form className="catalog-validation-form" onSubmit={(event) => void runReferenceValidation(event)}>
            <h3>Reference</h3>
            <label>
              Module
              <input
                required
                value={referenceModuleId}
                onChange={(event) => setReferenceModuleId(event.target.value)}
              />
            </label>
            <label>
              Field
              <input
                required
                value={referenceFieldName}
                onChange={(event) => setReferenceFieldName(event.target.value)}
              />
            </label>
            <label>
              Reference value
              <input required value={referenceValue} onChange={(event) => setReferenceValue(event.target.value)} />
            </label>
            <label>
              Domain
              <input value={referenceDomainName} onChange={(event) => setReferenceDomainName(event.target.value)} />
            </label>
            <Button disabled={runningValidation === "reference"} type="submit" variant="primary">
              {runningValidation === "reference" ? "Validating..." : "Validate reference"}
            </Button>
            {referenceValidation ? (
              <div className="catalog-validation-result" aria-label="Reference validation result">
                <strong>{`Reference validation: ${referenceValidation.severity}`}</strong>
                <span>{`${referenceValidation.object_type}: ${referenceValidation.gid}`}</span>
                <p>{referenceValidation.message}</p>
              </div>
            ) : null}
          </form>
        </div>
      </section>

      <ModuleWorkspaceLayout
        ariaLabel="OTM Catalog Core workspace"
        side={
          routeMacroCode ? (
          <SelectedObjectPanel
            ariaLabel="Selected catalog macro object"
            emptyText="Select a macro object to inspect backend-owned catalog metadata."
            fields={
              selectedMacro
                ? [
                    { label: "Category", value: selectedMacro.category },
                    { label: "Default method", value: selectedMacro.default_method },
                    { label: "Tables", value: selectedMacro.summary?.table_count ?? tableItems.length },
                    { label: "Dependencies", value: selectedMacro.summary?.dependency_count ?? loadPlanItems.length - 1 }
                  ]
                : []
            }
            isLoading={(macroDetail.isLoading || macroTables.isLoading || macroLoadPlan.isLoading) && Boolean(effectiveMacroCode)}
            loadingText="Loading selected macro object..."
            status={selectedMacro?.allow_csvutil || selectedMacro?.allow_cutover ? "ACTIVE" : "READ_ONLY"}
            subtitle={selectedMacro?.name}
            title={selectedMacro?.code}
          >
            {selectedMacro?.description ? <p className="empty-text">{selectedMacro.description}</p> : null}
            <DetailList
              ariaLabel="Selected macro object schema links"
              emptyText={macroCrossCheck.isLoading ? "Loading schema links..." : "No schema links ready for this macro object."}
              items={schemaLinkItems.map((item) => ({
                id: item.id,
                meta: [item.schema_guidance_role, item.domain_area, item.data_dictionary_family || "No table family", item.functional_confidence],
                status: item.source_reference_status,
                subtitle: item.root_name,
                title: item.root_display_label
              }))}
            />
            <DetailList
              ariaLabel="Selected macro object tables"
              emptyText="No tables linked to this macro object."
              items={tableItems.map((item) => ({
                id: item.id,
                meta: [item.relationship_role, item.data_category, item.allow_csvutil ? "CSVUTIL" : "No CSVUTIL"],
                status: item.validated_by_datadict ? "VALIDATED" : "NEEDS_REVIEW",
                title: item.table_name
              }))}
            />
            <DetailList
              ariaLabel="Selected macro object load plan"
              emptyText="No load plan available for this macro object."
              items={loadPlanItems.map((item) => ({
                id: `${item.dependency_role}-${item.macro_object_code}`,
                meta: [item.dependency_role, item.dependency_type, `${item.table_count} table(s)`],
                status: item.all_tables_validated ? "VALIDATED" : "NEEDS_REVIEW",
                title: item.macro_object_code
              }))}
            />
          </SelectedObjectPanel>
          ) : null
        }
        status={macroItems.length ? "ACTIVE" : "EMPTY"}
        title="Macro objects"
      >
        <ModuleObjectList
          ariaLabel="Catalog macro objects"
          emptyText="No catalog macro objects available for the current context."
          items={macroItems.map((item) => ({
            id: item.code,
            meta: catalogMacroMeta(item),
            status: item.allow_csvutil || item.allow_cutover ? "ACTIVE" : "READ_ONLY",
            subtitle: item.name,
            title: item.code
          }))}
          onSelect={handleSelectMacroObject}
          selectedId={effectiveMacroCode}
        />
      </ModuleWorkspaceLayout>
    </>
  );
}
