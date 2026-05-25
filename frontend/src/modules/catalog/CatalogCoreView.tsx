import { useState, type FormEvent } from 'react';

import { ApiError } from '../../platform/api';
import {
  useCatalogMacroObjectDetail,
  useCatalogMacroObjectLoadPlan,
  useCatalogMacroObjects,
  useCatalogMacroObjectTables,
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
  const macroObjects = useCatalogMacroObjects(token);
  const [selectedMacroCode, setSelectedMacroCode] = useState<string | null>(null);
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
  const macroItems = macroObjects.data?.items ?? [];
  const effectiveMacroCode = selectedMacroCode ?? macroItems[0]?.code ?? null;
  const macroDetail = useCatalogMacroObjectDetail(token, effectiveMacroCode);
  const macroTables = useCatalogMacroObjectTables(token, effectiveMacroCode);
  const macroLoadPlan = useCatalogMacroObjectLoadPlan(token, effectiveMacroCode);
  const selectedMacro = macroDetail.data;
  const tableItems = macroTables.data?.items ?? [];
  const loadPlanItems = macroLoadPlan.data?.items ?? [];
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

  function handleSelectMacroObject(macroCode: string) {
    if (macroCode === effectiveMacroCode) return;
    clearCatalogValidationResults();
    setSelectedMacroCode(macroCode);
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

  return (
    <>
      <PageHeader
        description="Canonical OTM catalog foundation for macro objects, load plans, data dictionary alignment, and module contracts."
        label="Module workspace"
        title="OTM Catalog Core"
      />

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
